import streamlit as st
import os
import json
import threading
import logging
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text, inspect, Column, String, JSON, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

# --- Database & Webhook Server Setup ---

# Suppress excessive Flask logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Get the database URL from the environment variable set in docker-compose.yml
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set.")

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Define the table structure for storing results
class Result(Base):
    __tablename__ = 'results'
    session_id = Column(String, primary_key=True)
    agent_type = Column(String, primary_key=True)
    data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

def init_db():
    """Initializes the database and creates the results table if it doesn't exist."""
    try:
        with engine.connect() as connection:
            inspector = inspect(engine)
            if not inspector.has_table("results"):
                print("Creating 'results' table...")
                Base.metadata.create_all(engine)
                print("Table 'results' created.")
            else:
                print("Table 'results' already exists.")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        # This is a critical error, so we might want to stop the app
        st.error(f"Database connection failed. Please check your Docker setup. Error: {e}")
        st.stop()

# 1. Define the Flask App
app = Flask(__name__)

@app.route('/webhook/<agent_type>', methods=['POST'])
def webhook(agent_type):
    """Receives data from n8n and inserts it into the PostgreSQL database."""
    try:
        data = request.get_json()
        session_id = data.get('session_id')

        if not session_id:
            return jsonify({"status": "error", "message": "session_id is required"}), 400

        # Upsert logic: Insert a new record, or update the data if the record already exists.
        stmt = text("""
            INSERT INTO results (session_id, agent_type, data)
            VALUES (:session_id, :agent_type, :data)
            ON CONFLICT (session_id, agent_type)
            DO UPDATE SET data = EXCLUDED.data, created_at = NOW();
        """)

        with engine.connect() as connection:
            connection.execute(stmt, {
                "session_id": session_id,
                "agent_type": agent_type,
                "data": json.dumps(data) # Ensure data is a JSON string
            })
            connection.commit() # Use commit with sqlalchemy 2.0

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"Webhook Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def run_webhook_server():
    app.run(host='0.0.0.0', port=5001, use_reloader=False)

# 2. Initialize DB and Run Server Thread
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state['db_initialized'] = True

if 'server_thread_started' not in st.session_state:
    thread = threading.Thread(target=run_webhook_server)
    thread.daemon = True
    thread.start()
    st.session_state['server_thread_started'] = True

# --- Streamlit App ---

import engAssistant
import esgAssistant
import complianceAssistant
import qualityRagChat

st.set_page_config(
    page_title="Meiyume AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application function"""
    st.sidebar.markdown(
        f'''
        <div class="sidebar-logo">
            <img src="https://meiyume-website-media.s3.ap-southeast-1.amazonaws.com/wp-content/uploads/2020/08/14174032/Meiyume_footer_logo-e1667547906481.png" width="200">
        </div>
        ''',
        unsafe_allow_html=True
    )
    st.sidebar.title("🎯 Navigation")

    st.sidebar.info("""
    **Action Required (if running locally):**
    1. Run `docker-compose up --build`.
    2. In a new terminal, run `ngrok http 5001`.
    3. Use the ngrok URL in your n8n workflows.
    """)

    page = st.sidebar.selectbox(
        "Choose an Assistant",
        ["CAD Analysis", "ESG Analysis", "Compliance Checker", "Quality RAG Chat"],
    )

    # Pass the database engine to the assistants
    db_engine = engine

    if page == "CAD Analysis":
        engAssistant.engineering_assistant(db_engine)
    elif page == "ESG Analysis":
        esgAssistant.esg_assistant(db_engine)
    elif page == "Compliance Checker":
        complianceAssistant.compliance_assistant(db_engine)
    elif page == "Quality RAG Chat":
        qualityRagChat.quality_rag_chat()

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Version:** 4.0.0 (Dockerized)")
    st.sidebar.markdown("**Powered by:** Meiyume AI")

if __name__ == "__main__":
    main()
