import streamlit as st
import requests
import time
import base64
import uuid
import pandas as pd
from io import StringIO
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
                # Handle nested data structure from n8n
                db_data = result[0]
                if isinstance(db_data, dict) and "data" in db_data:
                    if isinstance(db_data.get("data"), dict) and isinstance(db_data["data"].get("data"), list):
                        # Structure: {"data": {"data": [{"data": "...", "session_id": "..."}]}}
                        actual_data = db_data["data"]["data"][0]
                        extracted_data = actual_data
                    elif isinstance(db_data.get("data"), list):
                        # Structure: {"data": [{"data": "...", "session_id": "..."}]}
                        # Get first item from the list
                        if len(db_data["data"]) > 0:
                            extracted_data = db_data["data"][0]
                        else:
                            extracted_data = db_data
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
        test_session_id = "29d97aee-191f-4846-af95-89cc4c3a6d6f"
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
        
        # Check for base64 CSV data
        csv_data = None
        if isinstance(results_data, dict):
            # After extraction, results_data should be: {"data": "base64_string", "session_id": "..."}
            if "data" in results_data:
                csv_data = results_data.get("data")
                # If it's still nested (hasn't been extracted yet), check deeper
                if isinstance(csv_data, dict) and "data" in csv_data:
                    nested_list = csv_data.get("data")
                    if isinstance(nested_list, list) and len(nested_list) > 0:
                        first_item = nested_list[0]
                        if isinstance(first_item, dict) and "data" in first_item:
                            csv_data = first_item.get("data")
        elif isinstance(results_data, list) and len(results_data) > 0:
            if isinstance(results_data[0], dict):
                csv_data = results_data[0].get("data")
        
        if csv_data:
            try:
                # Decode base64 CSV - handle both string and byte responses
                if isinstance(csv_data, str):
                    csv_bytes = base64.b64decode(csv_data)
                else:
                    csv_bytes = base64.b64decode(csv_data)
                
                # Try different encodings
                csv_decoded = None
                for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        csv_decoded = csv_bytes.decode(encoding)
                        break
                    except:
                        continue
                
                if not csv_decoded:
                    csv_decoded = csv_bytes.decode('utf-8', errors='replace')
                
                # Read CSV into pandas DataFrame
                df = pd.read_csv(StringIO(csv_decoded))
                
                # Remove ID and created_at columns if they exist
                columns_to_remove = ['id', 'ID', 'Id', 'created_at', 'Created At', 'Created_At', 'createdAt']
                for col in columns_to_remove:
                    if col in df.columns:
                        df = df.drop(columns=[col])
                
                # Display as a table
                st.markdown("#### Compliance Data Table")
                st.dataframe(df, use_container_width=True, hide_index=True)
                
            except Exception as e:
                st.error(f"Error decoding CSV: {e}")
        elif isinstance(results_data, dict) and "output" in results_data:
            # Fallback to output field if available
            output = results_data.get("output", "")
            
            if output:
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
                st.info("No output available.")
        else:
            st.info("No compliance results available.")
            
    elif record["status"] == "processing":
        st.info("Processing... results will appear here when ready.")
    elif record["status"] == "failed":
        st.error("Failed to retrieve results for this analysis.")
