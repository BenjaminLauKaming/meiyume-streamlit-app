import streamlit as st
import requests
import time
import base64
import uuid
from sqlalchemy import text
import pandas as pd
from io import StringIO

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
                # Handle nested data structure from n8n
                db_data = result[0]
                
                # Extract data from nested structure: {"data": {"data": [{"data": "base64_csv"}]}}
                extracted_data = db_data
                if isinstance(db_data, dict) and "data" in db_data:
                    if isinstance(db_data.get("data"), dict) and "data" in db_data["data"]:
                        inner_data = db_data["data"].get("data")
                        if isinstance(inner_data, list) and len(inner_data) > 0:
                            extracted_data = inner_data[0]
                        elif isinstance(inner_data, str):
                            extracted_data = {"data": inner_data}
                    elif isinstance(db_data.get("data"), list):
                        if len(db_data["data"]) > 0:
                            extracted_data = db_data["data"][0]
                
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
        test_session_id = "99b42128-8050-4b04-a202-1377e2f530f0"
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
                    extracted_data = result_data
                    if isinstance(result_data, dict) and "data" in result_data:
                        if isinstance(result_data.get("data"), dict) and "data" in result_data["data"]:
                            inner_data = result_data["data"].get("data")
                            if isinstance(inner_data, list) and len(inner_data) > 0:
                                extracted_data = inner_data[0]
                            elif isinstance(inner_data, str):
                                extracted_data = {"data": inner_data}
                        elif isinstance(result_data.get("data"), list):
                            if len(result_data["data"]) > 0:
                                extracted_data = result_data["data"][0]
                    
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
    """Display compliance results with base64 CSV decoded"""
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
        
        # Handle nested data structure and extract base64 CSV
        csv_data = None
        
        if isinstance(results_data, dict):
            # Check for base64 CSV in various possible locations
            if "data" in results_data:
                csv_data = results_data.get("data")
            elif isinstance(results_data.get("data"), dict) and "data" in results_data["data"]:
                # Handle nested structure: {"data": {"data": "base64..."}}
                inner_data = results_data["data"].get("data")
                if isinstance(inner_data, list) and len(inner_data) > 0:
                    csv_data = inner_data[0].get("data")
                elif isinstance(inner_data, str):
                    csv_data = inner_data
        
        # Decode and display CSV
        if csv_data:
            try:
                # Decode base64
                decoded_csv = base64.b64decode(csv_data).decode('utf-8')
                
                # Parse CSV
                df = pd.read_csv(StringIO(decoded_csv))
                
                # Display as custom formatted table
                st.markdown("### 📋 Compliance Analysis Results")
                
                # Add CSS for larger font size
                st.markdown("""
                <style>
                .compliance-table {
                    font-size: 1.1em;
                }
                .compliance-table-header {
                    font-size: 1.2em;
                    font-weight: bold;
                }
                .compliance-cas-id {
                    font-size: 1.3em;
                    font-weight: 500;
                }
                .compliance-issues-header {
                    font-size: 1.3em;
                    font-weight: 500;
                }
                .compliance-not-found {
                    font-size: 1.3em;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Add table headers
                header_col1, header_col2 = st.columns([1, 2])
                with header_col1:
                    st.markdown('<div class="compliance-table-header">CAS ID</div>', unsafe_allow_html=True)
                with header_col2:
                    st.markdown('<div class="compliance-table-header">Result</div>', unsafe_allow_html=True)
                st.markdown("---")
                
                # Create custom table format
                for idx, row in df.iterrows():
                    # Get CAS ID (handle different column name variations)
                    cas_id = row.get('CAS ID', '') or row.get('cas_id', '') or row.get('CAS_ID', '') or str(row.iloc[0] if len(row) > 0 else '')
                    result = str(row.get('result', ''))
                    
                    # Split by nextline marker
                    issues = [issue.strip() for issue in result.split('*nextline*') if issue.strip()]
                    
                    # Create columns for custom table layout
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.markdown(f'<div class="compliance-cas-id">{cas_id}</div>', unsafe_allow_html=True)
                    
                    with col2:
                        if issues:
                            # Only show "Compliance Issues" header if not all issues are "not found in any source"
                            all_not_found = all(issue.lower().strip() == "not found in any source" for issue in issues)
                            
                            if not all_not_found:
                                st.markdown('<div class="compliance-issues-header">Compliance Issues</div>', unsafe_allow_html=True)
                            
                            for issue in issues:
                                # Check if issue is "not found in any source"
                                if issue.lower().strip() == "not found in any source":
                                    st.markdown(f'<div class="compliance-not-found">{issue}</div>', unsafe_allow_html=True)
                                else:
                                    st.markdown(f'<div class="compliance-table">- {issue}</div>', unsafe_allow_html=True)
                        else:
                            # Check if single result is "not found in any source"
                            if result.lower().strip() != "not found in any source":
                                st.markdown(f'<div class="compliance-issues-header">Compliance Issues</div>', unsafe_allow_html=True)
                                st.markdown(f'<div class="compliance-table">*{result}*</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="compliance-not-found">{result}</div>', unsafe_allow_html=True)
                    
                    st.markdown("---")
                
            except Exception as e:
                st.error(f"Error decoding CSV: {e}")
                st.code(csv_data[:500] if len(csv_data) > 500 else csv_data, language="text")
        else:
            st.info("No CSV data found in results.")
            
    elif record["status"] == "processing":
        st.info("Processing... results will appear here when ready.")
    elif record["status"] == "failed":
        st.error("Failed to retrieve results for this analysis.")
