import streamlit as st
import requests
import json
import os
import time
import base64
from datetime import datetime
import uuid
from sqlalchemy import text

# This URL is for the n8n workflow webhook endpoint
N8N_COMPLIANCE_WORKFLOW_URL = "https://meiyume.app.n8n.cloud/webhook-test/62280c29-7f88-4e1c-9e2b-ec308fff4b8d"

def submit_to_n8n(uploaded_file, session_id):
    """Submits the file and session_id to the n8n workflow."""
    try:
        # Convert file to base64 for JSON webhook
        file_content = uploaded_file.getvalue()
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        # Prepare payload for n8n workflow
        webhook_payload = {
            'data': file_base64,
            'session_id': session_id,
            'filename': uploaded_file.name
        }
        
        # Debug logging
        print(f"DEBUG: Sending to n8n webhook - URL: {N8N_COMPLIANCE_WORKFLOW_URL}")
        print(f"DEBUG: Payload keys: {list(webhook_payload.keys())}")
        print(f"DEBUG: File name: {uploaded_file.name}")
        print(f"DEBUG: Session ID: {session_id}")
        print(f"DEBUG: File size: {len(file_content)} bytes")
        print(f"DEBUG: Base64 size: {len(file_base64)} chars")
        
        # Send as JSON with proper headers
        response = requests.post(
            N8N_COMPLIANCE_WORKFLOW_URL,
            json=webhook_payload,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Meiyume-AI-Assistant/1.0'
            },
            timeout=60
        )
        
        # Debug response
        print(f"DEBUG: Response status: {response.status_code}")
        print(f"DEBUG: Response text: {response.text[:200]}...")
        if response.status_code == 200:
            st.success("File submitted successfully! Waiting for results.")
            return True
        else:
            st.error(f"Workflow submission failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        st.error(f"An error occurred during submission: {e}")
        return False

def poll_for_db_results(session_id, agent_type, db_engine):
    """Polls the database for a result matching the session_id and agent_type."""
    max_attempts = 90
    status_placeholder = st.empty()
    stmt = text("SELECT data FROM results WHERE session_id = :session_id AND agent_type = :agent_type")
    for attempt in range(max_attempts):
        with db_engine.connect() as connection:
            result = connection.execute(stmt, {"session_id": session_id, "agent_type": agent_type}).fetchone()
        if result:
            status_placeholder.success("✅ Analysis complete!")
            return result[0]
        status_placeholder.info(f"🔄 Awaiting results... (Attempt {attempt + 1}/{max_attempts})")
        time.sleep(2)
    status_placeholder.warning("⏱️ Polling timed out.")
    return None

def compliance_assistant(db_engine):
    """Compliance Checker main interface, using a database for results."""
    st.title("🧪 Compliance Checker")
    st.markdown("### Upload MSDS (PDF) for compliance check")

    if 'compliance_current' not in st.session_state:
        st.session_state.compliance_current = None
        
    # Test button to simulate results with existing session ID
    if st.button("🧪 Test with Existing Session ID", type="secondary"):
        test_session_id = "your-test-session-id-here"  # Replace with a real session ID once you have one
        st.info(f"Testing with session ID: {test_session_id}")
        
        # Query the database for this specific session
        try:
            query = text("""
                SELECT data FROM results 
                WHERE session_id = :session_id AND agent_type = 'compliance'
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            
            with db_engine.connect() as connection:
                result = connection.execute(query, {"session_id": test_session_id})
                row = result.fetchone()
                
                if row:
                    # The data is already a dict, not a JSON string
                    result_data = row[0]  # row[0] is already the dict
                    
                    # Save to session state
                    st.session_state.compliance_current = {
                        "filename": "Test File.pdf",
                        "status": "completed",
                        "results": result_data
                    }
                    
                    st.success("✅ Test data loaded successfully!")
                    st.rerun()
                else:
                    st.error("❌ No data found for that session ID")
                    
        except Exception as e:
            st.error(f"❌ Error loading test data: {e}")

    uploaded_file = st.file_uploader("Choose an MSDS PDF", type=['pdf'])

    if uploaded_file is not None:
        if st.button("🚀 Submit for Compliance Check", type="primary"):
            session_id = str(uuid.uuid4())
            st.info(f"Analysis started with session ID: {session_id}")
            st.session_state.compliance_current = {
                "filename": uploaded_file.name,
                "status": "processing"
            }
            if submit_to_n8n(uploaded_file, session_id):
                result_data = poll_for_db_results(session_id, 'compliance', db_engine)
                if result_data:
                    st.session_state.compliance_current['status'] = 'completed'
                st.session_state.compliance_current['results'] = result_data
                # No longer need to force a rerun, Streamlit will update automatically.

    if st.session_state.compliance_current:
        display_compliance_result(st.session_state.compliance_current)

def display_compliance_result(record):
    """Display compliance results in a well-formatted way"""
    st.markdown("---")
    st.markdown("### 📄 Submission Status")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("File", record["filename"])
    with col2:
        st.metric("Status", record["status"].title())

    if "results" in record and record["results"]:
        st.markdown("### ✅ Compliance Results")
        
        # Extract data from results
        results_data = record["results"]
        
        # Create tabs for different views of the data
        tabs = st.tabs(["📊 Summary", "🔍 Details", "📝 Raw Data"])
        
        with tabs[0]:
            st.markdown("#### Summary of Compliance Analysis")
            
            # Display key metrics if available
            if isinstance(results_data, dict):
                # Extract key metrics if they exist
                product_name = results_data.get("product_name", "Not specified")
                compliance_status = results_data.get("compliance_status", "Unknown")
                risk_level = results_data.get("risk_level", "Not assessed")
                
                # Create metrics
                metric_cols = st.columns(3)
                with metric_cols[0]:
                    st.metric("Product", product_name)
                with metric_cols[1]:
                    status_color = "🟢" if compliance_status == "Compliant" else "🔴" if compliance_status == "Non-compliant" else "🟡"
                    st.metric("Compliance Status", f"{status_color} {compliance_status}")
                with metric_cols[2]:
                    risk_color = "🟢" if risk_level == "Low" else "🟡" if risk_level == "Medium" else "🔴" if risk_level == "High" else "⚪"
                    st.metric("Risk Level", f"{risk_color} {risk_level}")
                
                # Display key findings if available
                if "findings" in results_data and isinstance(results_data["findings"], list):
                    st.markdown("#### Key Findings")
                    for i, finding in enumerate(results_data["findings"]):
                        st.markdown(f"**{i+1}.** {finding}")
            else:
                st.info("No structured summary data available.")
        
        with tabs[1]:
            st.markdown("#### Detailed Compliance Information")
            
            if isinstance(results_data, dict):
                # Display any detailed sections
                if "details" in results_data and isinstance(results_data["details"], dict):
                    details = results_data["details"]
                    
                    # Create expandable sections for each detail category
                    for category, info in details.items():
                        with st.expander(f"{category.title()}"):
                            if isinstance(info, dict):
                                for key, value in info.items():
                                    st.markdown(f"**{key}:** {value}")
                            elif isinstance(info, list):
                                for item in info:
                                    if isinstance(item, dict):
                                        for key, value in item.items():
                                            st.markdown(f"**{key}:** {value}")
                                        st.markdown("---")
                                    else:
                                        st.markdown(f"- {item}")
                            else:
                                st.write(info)
                else:
                    # If no structured details, show any other fields
                    for key, value in results_data.items():
                        if key not in ["product_name", "compliance_status", "risk_level", "findings"] and not isinstance(value, (dict, list)):
                            st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")
            else:
                st.info("No detailed information available.")
        
        with tabs[2]:
            st.markdown("#### Raw Response Data")
            st.json(results_data)
            
    elif record["status"] == "processing":
        st.info("Processing... results will appear here when ready.")
    elif record["status"] == "failed":
        st.error("Failed to retrieve results for this analysis.")
