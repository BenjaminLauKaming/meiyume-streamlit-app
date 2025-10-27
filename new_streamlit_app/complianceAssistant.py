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
N8N_COMPLIANCE_WORKFLOW_URL = "https://meiyume.app.n8n.cloud/webhook/62280c29-7f88-4e1c-9e2b-ec308fff4b8d"

def submit_to_n8n_and_poll(uploaded_file, session_id, db_engine):
    """Submit file to n8n and poll for results from database."""
    progress_bar = st.progress(0)
    status_container = st.empty()
    try:
        status_container.info("Submitting file to n8n workflow...")
        progress_bar.progress(0.2)
        
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
        print(f"DEBUG: File name: {uploaded_file.name}")
        print(f"DEBUG: Session ID: {session_id}")
        print(f"DEBUG: File size: {len(file_content)} bytes")
        
        response = requests.post(
            N8N_COMPLIANCE_WORKFLOW_URL,
            json=webhook_payload,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Meiyume-AI-Assistant/1.0'
            },
            timeout=60
        )
        
        print(f"DEBUG: Response status: {response.status_code}")
        
        if response.status_code not in [200, 201]:
            status_container.error(f"Submission failed: {response.status_code}")
            return None

        status_container.info("File submitted. Awaiting results...")
        progress_bar.progress(0.5)
        
        result_data = poll_for_db_results(session_id, 'com', db_engine)
        
        if result_data:
            status_container.success("Analysis completed!")
            progress_bar.progress(1.0)
            return result_data
        else:
            status_container.warning("Processing timed out or failed.")
            return None
            
    except Exception as e:
        status_container.error(f"An error occurred: {e}")
        return None

def poll_for_db_results(session_id, agent_type, db_engine):
    """Polls the database for a result matching the session_id and agent_type."""
    max_attempts = 90
    stmt = text("SELECT data FROM results WHERE session_id = :session_id AND agent_type = :agent_type")
    for attempt in range(max_attempts):
        time.sleep(2)  # Wait before checking
        try:
            with db_engine.connect() as connection:
                result = connection.execute(stmt, {"session_id": session_id, "agent_type": agent_type}).fetchone()
            
            if result:
                # Handle nested data structure from n8n (same as CAD workflow)
                db_data = result[0]
                if isinstance(db_data, dict) and "data" in db_data:
                    if isinstance(db_data.get("data"), dict) and isinstance(db_data["data"].get("data"), list):
                        actual_data = db_data["data"]["data"][0]
                        extracted_data = actual_data
                    elif isinstance(db_data.get("data"), list):
                        extracted_data = db_data["data"]
                    else:
                        extracted_data = db_data
                else:
                    extracted_data = db_data
                
                return extracted_data
        except Exception as e:
            print(f"Database query error: {e}")
            continue
            
    return None

def compliance_assistant(db_engine):
    """Compliance Checker main interface, using a database for results."""
    st.title("🧪 Compliance Checker")
    st.markdown("### Upload MSDS (PDF) for compliance check")

    if 'compliance_current' not in st.session_state:
        st.session_state.compliance_current = None
        
    # Test button to simulate results with existing session ID
    if st.button("🧪 Test with Existing Session ID", type="secondary"):
        test_session_id = "94891177-6c2f-466a-be23-8efe139182c9"
        st.info(f"Testing with session ID: {test_session_id}")
        
        # Query the database for this specific session
        try:
            query = text("""
                SELECT data FROM results 
                WHERE session_id = :session_id AND agent_type = 'com'
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            
            with db_engine.connect() as connection:
                result = connection.execute(query, {"session_id": test_session_id})
                row = result.fetchone()
                
                if row:
                    # The data is already a dict, not a JSON string
                    result_data = row[0]  # row[0] is already the dict
                    
                    # Handle nested data structure from n8n
                    if isinstance(result_data, dict) and "data" in result_data:
                        if isinstance(result_data.get("data"), dict) and isinstance(result_data["data"].get("data"), list):
                            actual_data = result_data["data"]["data"][0]
                            extracted_data = actual_data
                        elif isinstance(result_data.get("data"), list):
                            extracted_data = result_data["data"]
                        else:
                            extracted_data = result_data
                    else:
                        extracted_data = result_data
                    
                    # Save to session state
                    st.session_state.compliance_current = {
                        "filename": "Test File.pdf",
                        "status": "completed",
                        "results": extracted_data
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
            st.session_state.compliance_current = {
                "filename": uploaded_file.name,
                "status": "processing"
            }
            result_data = submit_to_n8n_and_poll(uploaded_file, session_id, db_engine)
            if result_data:
                st.session_state.compliance_current['status'] = 'completed'
                st.session_state.compliance_current['results'] = result_data

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
            
            # Display compliance findings
            if isinstance(results_data, dict):
                # Check if we have an "output" field (from n8n workflow)
                if "output" in results_data:
                    output = results_data.get("output", "")
                    
                    # Display the compliance findings
                    st.markdown("#### Compliance Findings")
                    # Split the output by line and display each finding
                    findings = [f.strip() for f in output.split('\n') if f.strip()]
                    for finding in findings:
                        if finding.startswith('-'):
                            finding = finding[1:]  # Remove leading dash
                        if finding:
                            st.markdown(f"• {finding}")
                else:
                    # Try to extract key metrics if they exist (old format)
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
