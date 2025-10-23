import streamlit as st
import requests
import json
import os
import time
from datetime import datetime
import uuid
from sqlalchemy import text

# This URL is for the n8n workflow trigger
N8N_ESG_WORKFLOW_URL = ""

def submit_to_n8n(uploaded_file, session_id):
    """Submits the file and session_id to the n8n workflow."""
    try:
        # Get webhook URL - use ngrok URL if available, otherwise localhost
        webhook_url = os.getenv('WEBHOOK_URL', 'http://localhost:5001/webhook/esg')
        
        files = {'data': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        data = {
            'session_id': session_id,
            'document_type': 'factory_document',
            'filename': uploaded_file.name,
            'webhook_url': webhook_url  # Tell n8n where to send results
        }
        response = requests.post(N8N_ESG_WORKFLOW_URL, files=files, data=data, timeout=30)
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

def esg_assistant(db_engine):
    """Main ESG Assistant interface"""
    st.title("🌱 ESG Assistant")
    st.markdown("### Factory Document Analysis for ESG")
    
    if 'esg_current_analysis' not in st.session_state:
        st.session_state.esg_current_analysis = None
    
    uploaded_file = st.file_uploader(
        "Choose a document",
        type=['pdf', 'doc', 'docx', 'txt', 'csv', 'xlsx', 'jpg', 'jpeg', 'png']
    )
    
    if uploaded_file is not None:
        if st.button("🔍 Start ESG analysis", type="primary"):
            session_id = str(uuid.uuid4())
            st.info(f"Analysis started with session ID: {session_id}")
            st.session_state.esg_current_analysis = {
                "filename": uploaded_file.name,
                "status": "processing"
            }
            if submit_to_n8n(uploaded_file, session_id):
                result_data = poll_for_db_results(session_id, 'esg', db_engine)
                if result_data:
                    st.session_state.esg_current_analysis['status'] = 'completed'
                    st.session_state.esg_current_analysis['results'] = result_data
                else:
                    st.session_state.esg_current_analysis['status'] = 'failed'
                # No longer need to force a rerun, Streamlit will update automatically.

    if st.session_state.esg_current_analysis:
        display_esg_results(st.session_state.esg_current_analysis)

def display_esg_results(analysis_record):
    """Display results"""
    st.markdown("---")
    st.markdown("### 📊 ESG Analysis Results")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("File", analysis_record["filename"])
    with col2:
        st.metric("Status", analysis_record["status"].title())
    
    if "results" in analysis_record and analysis_record["results"]:
        st.markdown("#### Full Result Payload")
        st.json(analysis_record["results"])
    elif analysis_record["status"] == "processing":
        st.info("Processing... results will appear here when ready.")
    elif analysis_record["status"] == "failed":
        st.error("Failed to retrieve results for this analysis.")
