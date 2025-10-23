import streamlit as st
import requests
import json
import os
import time
from datetime import datetime
import uuid
from sqlalchemy import text

# This URL is for the n8n workflow trigger
N8N_COMPLIANCE_WORKFLOW_URL = ""

def submit_to_n8n(uploaded_file, session_id):
    """Submits the file and session_id to the n8n workflow."""
    try:
        # Get webhook URL - use ngrok URL if available, otherwise localhost
        webhook_url = os.getenv('WEBHOOK_URL', 'http://localhost:5001/webhook/compliance')
        
        files = {'data': (uploaded_file.name, uploaded_file.getvalue(), 'application/pdf')}
        data = {
            'session_id': session_id,
            'filename': uploaded_file.name,
            'webhook_url': webhook_url  # Tell n8n where to send results
        }
        response = requests.post(N8N_COMPLIANCE_WORKFLOW_URL, files=files, data=data, timeout=30)
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
    """Display results"""
    st.markdown("---")
    st.markdown("### 📄 Submission Status")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("File", record["filename"])
    with col2:
        st.metric("Status", record["status"].title())

    if "results" in record and record["results"]:
        st.markdown("### ✅ Compliance Results")
        st.json(record["results"])
    elif record["status"] == "processing":
        st.info("Processing... results will appear here when ready.")
    elif record["status"] == "failed":
        st.error("Failed to retrieve results for this analysis.")
