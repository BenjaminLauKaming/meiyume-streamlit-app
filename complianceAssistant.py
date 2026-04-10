import streamlit as st
import requests
import time
import base64
import uuid
from sqlalchemy import text
import pandas as pd
from io import StringIO
from datetime import datetime

# This URL is for the n8n workflow webhook endpoint (File Upload)
N8N_COMPLIANCE_WORKFLOW_URL = "https://meiyume.app.n8n.cloud/webhook/62280c29-7f88-4e1c-9e2b-ec308fff4b8d"
# This URL is for the n8n workflow webhook endpoint (Single CAS ID)
N8N_CAS_WORKFLOW_URL = "https://meiyume.app.n8n.cloud/webhook/62280c29-7f88-4e1c-9e2b-eojh34i34uub34u"

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

def submit_cas_to_n8n_and_poll(cas_id, session_id, db_engine):
    """Submit single CAS ID to n8n and poll for results."""
    status_container = st.empty()
    try:
        status_container.info(f"Submitting CAS ID {cas_id} to n8n workflow...")
        
        # Prepare payload for n8n workflow
        webhook_payload = {
            'cas_id': cas_id,
            'session_id': session_id,
            'type': 'single_cas_check'
        }
        
        # Debug logging
        print(f"DEBUG: Sending to n8n CAS webhook - URL: {N8N_CAS_WORKFLOW_URL}")
        print(f"DEBUG: CAS ID: {cas_id}")
        
        response = requests.post(
            N8N_CAS_WORKFLOW_URL,
            json=webhook_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code not in [200, 201]:
            status_container.error(f"Submission failed: {response.status_code}")
            return None

        status_container.info("CAS ID submitted. Awaiting results...")
        
        result_data = poll_for_db_results(session_id, 'com', db_engine)
        
        if result_data:
            status_container.success("Analysis completed!")
            return result_data
        else:
            status_container.error("Processing timed out or failed.")
            return None
            
    except Exception as e:
        status_container.error(f"An error occurred: {e}")
        return None

def poll_for_db_results(session_id, agent_type, db_engine):
    """Polls the database for a result matching the session_id and agent_type."""
    max_attempts = 60  # 60 attempts * 2 seconds = 120 seconds total wait
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
    
    # Add regulations to sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown("### Regulations Checked")
        fixed = [
            "CMR CLC Regulation",
            "Reach SVHC",
            "CA Prop65",
            "Cosmetic Regulation CE annex II",
            "Cosmetic Regulation CE annex III",
        ]
        regulation_md = "\n".join(f"- {r}" for r in fixed)
        try:
            with db_engine.connect() as conn:
                result = conn.execute(text("SELECT display_name FROM customer_lists ORDER BY display_name"))
                customer_names = [row[0] for row in result]
            if customer_names:
                regulation_md += "\n" + "\n".join(f"- {n}" for n in customer_names)
        except Exception:
            pass
        st.markdown(regulation_md)

    st.markdown("### Upload MSDS (PDF) for compliance check")

    if 'compliance_current' not in st.session_state:
        st.session_state.compliance_current = None
        
    # Fetch recent history
    st.sidebar.markdown("---")
    st.sidebar.subheader("🕒 Recent Analysis History")
    
    try:
        history_query = text("""
            SELECT session_id, created_at, filename FROM results 
            WHERE agent_type = 'com' 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        with db_engine.connect() as connection:
            history_results = connection.execute(history_query).fetchall()
            
            if history_results:
                for row in history_results:
                    session_id = row[0]
                    created_at = row[1]
                    filename = row[2] if len(row) > 2 and row[2] else "Unknown File"
                    timestamp_str = created_at.strftime("%Y-%m-%d %H:%M") if created_at else "Unknown"
                    
                    # Use Unicode Bold characters for "Filename" and "UploadTime" since markdown isn't supported in buttons
                    # Filename -> 𝗙𝗶𝗹𝗲𝗻𝗮𝗺𝗲
                    # UploadTime -> 𝗨𝗽𝗹𝗼𝗮𝗱𝗧𝗶𝗺𝗲
                    label = f"𝗙𝗶𝗹𝗲𝗻𝗮𝗺𝗲: {filename}\n𝗨𝗽𝗹𝗼𝗮𝗱𝗧𝗶𝗺𝗲: {timestamp_str}"
                    
                    if st.sidebar.button(label, key=session_id):
                         # Load this session
                        try:
                            load_query = text("""
                                SELECT data FROM results 
                                WHERE session_id = :session_id AND agent_type = 'com'
                            """)
                            result = connection.execute(load_query, {"session_id": session_id}).fetchone()
                            
                            if result:
                                result_data = result[0]
                                extracted_data = result_data
                                
                                # Logic to extract data (same as before)
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
                                
                                st.session_state.compliance_current = {
                                    "filename": filename, 
                                    "status": "completed",
                                    "timestamp": timestamp_str, # Store timestamp
                                    "results": extracted_data
                                }
                                st.rerun()
                        except Exception as e:
                            st.sidebar.error(f"Error loading: {e}")
            else:
                st.sidebar.info("No recent history found.")
                
    except Exception as e:
        st.sidebar.error(f"Error fetching history: {e}")

    uploaded_file = st.file_uploader("Choose an MSDS PDF", type=['pdf'])

    if uploaded_file is not None:
        if st.button("🚀 Submit for Compliance Check", type="primary"):
            session_id = str(uuid.uuid4())
            st.session_state.compliance_current = {
                "filename": uploaded_file.name,
                "status": "processing",
                "timestamp": "-" # Placeholder until DB confirms
            }
            result_data = submit_to_n8n_and_poll(uploaded_file, session_id, db_engine)
            if result_data:
                st.session_state.compliance_current['status'] = 'completed'
                st.session_state.compliance_current['results'] = result_data
                
                # Fetch created_at from DB
                try:
                    time_query = text("SELECT created_at FROM results WHERE session_id = :session_id")
                    with db_engine.connect() as connection:
                        time_result = connection.execute(time_query, {"session_id": session_id}).fetchone()
                        if time_result and time_result[0]:
                            st.session_state.compliance_current['timestamp'] = time_result[0].strftime("%Y-%m-%d %H:%M")
                except Exception as e:
                    print(f"Error fetching time: {e}")

    # Section for Single CAS ID Check
    st.markdown("---")
    st.subheader("🔍 Check Single CAS ID")
    cas_input = st.text_input("Enter CAS ID (e.g., 50-00-0)", placeholder="Type a single CAS ID here...")
    
    if st.button("🔎 Check CAS ID"):
        if cas_input:
            session_id = str(uuid.uuid4())
            st.session_state.compliance_current = {
                "filename": f"CAS: {cas_input}",
                "status": "processing",
                "timestamp": "-"
            }
            # Use the new function for CAS ID
            result_data = submit_cas_to_n8n_and_poll(cas_input, session_id, db_engine)
            if result_data:
                st.session_state.compliance_current['status'] = 'completed'
                st.session_state.compliance_current['results'] = result_data
                
                # Fetch created_at from DB
                try:
                    time_query = text("SELECT created_at FROM results WHERE session_id = :session_id")
                    with db_engine.connect() as connection:
                        time_result = connection.execute(time_query, {"session_id": session_id}).fetchone()
                        if time_result and time_result[0]:
                            st.session_state.compliance_current['timestamp'] = time_result[0].strftime("%Y-%m-%d %H:%M")
                except Exception as e:
                    print(f"Error fetching time: {e}")
        else:
            st.warning("Please enter a CAS ID.")

    if st.session_state.compliance_current:
        display_compliance_result(st.session_state.compliance_current)

def display_compliance_result(record):
    """Display compliance results with base64 CSV decoded"""
    st.markdown("---")
    st.markdown("### 📄 Submission Status")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.metric("File", record.get("filename", "Unknown"))
    with col2:
        st.metric("Status", record.get("status", "").title())
    with col3:
        st.metric("Time", record.get("timestamp", "-"))

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
        if csv_data and not isinstance(csv_data, (list, dict)):
            try:
                # Decode base64
                decoded_csv = base64.b64decode(csv_data).decode('utf-8')
                
                # Parse CSV
                df = pd.read_csv(StringIO(decoded_csv))
                
                
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
                .compliance-pass {
                    color: #28a745;
                    font-weight: bold;
                    font-size: 1.1em;
                }
                .compliance-fail {
                    color: #dc3545;
                    font-weight: bold;
                    font-size: 1.1em;
                }
                .compliance-warning {
                    color: #DAA520;
                    font-weight: bold;
                    font-size: 1.1em;
                }
                /* Allow multiline buttons in sidebar */
                .stButton > button {
                    white-space: pre-wrap;
                    height: auto;
                    padding-top: 10px;
                    padding-bottom: 10px;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Check for Chemical Name column
                chem_name_col = None
                for col in df.columns:
                     if 'chemical' in col.lower() and 'name' in col.lower():
                          chem_name_col = col
                          break
                
                # Add table headers
                if chem_name_col:
                    header_col1, header_col2, header_col3 = st.columns([1, 1.5, 2.5])
                    with header_col1:
                        st.markdown('<div class="compliance-table-header">CAS ID</div>', unsafe_allow_html=True)
                    with header_col2:
                         st.markdown('<div class="compliance-table-header">Chemical Name</div>', unsafe_allow_html=True)
                    with header_col3:
                        st.markdown('<div class="compliance-table-header">Result</div>', unsafe_allow_html=True)
                else:
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
                    
                    # Normalize display for missing values
                    if str(cas_id).strip().lower() in ['nan', 'n/a', 'none', '']:
                        cas_id = 'n/a'

                    result = str(row.get('result', ''))
                    
                    # Split by nextline marker
                    issues = [issue.strip() for issue in result.split('*nextline*') if issue.strip()]
                    
                    # Create columns for custom table layout
                    if chem_name_col:
                        col1, col2, col3 = st.columns([1, 1.5, 2.5])
                        chem_name = str(row.get(chem_name_col, ''))
                        
                        with col1:
                            st.markdown(f'<div class="compliance-cas-id">{cas_id}</div>', unsafe_allow_html=True)
                        with col2:
                            st.markdown(f"**{chem_name}**")
                        # col3 is the result column
                        target_col = col3
                    else:
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.markdown(f'<div class="compliance-cas-id">{cas_id}</div>', unsafe_allow_html=True)
                        # col2 is the result column
                        target_col = col2
                    
                    with target_col:
                        # Check for N/A CAS ID first
                        if cas_id == 'n/a':
                            st.markdown(f'<div class="compliance-warning">CAS has not shown</div>', unsafe_allow_html=True)
                        elif issues:
                            for issue in issues:
                                # Check if issue is "not found in any source"
                                if issue.lower().strip() == "not found in any source":
                                    st.markdown(f'<div class="compliance-pass">PASS : Not found in any database</div>', unsafe_allow_html=True)
                                else:
                                    st.markdown(f'<div class="compliance-fail">FAIL : {issue}</div>', unsafe_allow_html=True)
                        else:
                            # Check if single result is "not found in any source"
                            if result.lower().strip() == "not found in any source":
                                st.markdown(f'<div class="compliance-pass">PASS : Not found in any database.</div>', unsafe_allow_html=True)
                            elif result:
                                st.markdown(f'<div class="compliance-fail">FAIL : {result}</div>', unsafe_allow_html=True)
                    
                    st.markdown("---")
                
            except Exception as e:
                st.error(f"Error decoding CSV: {e}")
                st.code(csv_data[:500] if len(csv_data) > 500 else csv_data, language="text")
        else:
            st.markdown('<h3 style="color: red;">⚠️ This file has no CAS ID or the execution failed. Please try again or upload another file.</h3>', unsafe_allow_html=True)
            
    elif record["status"] == "processing":
        st.info("Processing... results will appear here when ready.")
    elif record["status"] == "failed":
        st.error("Failed to retrieve results for this analysis.")
