import streamlit as st
import os
from sqlalchemy import create_engine, text, inspect, Column, String, JSON, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

# --- Database Setup ---

# Primary Database (for results, etc.)
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    st.error("DATABASE_URL not found. Please set it in your .env file.")
    st.stop()

# Compliance/Regulatory Database
COMPLIANCE_DATABASE_URL = os.environ.get("ComplanceDATABASE_URL") or DATABASE_URL

# SQLAlchemy engines
engine = create_engine(DATABASE_URL)
compliance_engine = create_engine(COMPLIANCE_DATABASE_URL)

Base = declarative_base()

# Define the table structure for storing results
class Result(Base):
    __tablename__ = 'results'
    session_id = Column(String, primary_key=True)
    agent_type = Column(String, primary_key=True)
    data = Column(JSON)
    filename = Column(String)  # Added filename column
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
        st.error(f"Database connection failed. Please check your Supabase setup. Error: {e}")
        st.stop()

# Initialize Database
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state['db_initialized'] = True

# --- Streamlit App ---

import engAssistant
import complianceAssistant
import qualityRagChat
import regulatory_scraper
import multimodalAssistant


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


    page = st.sidebar.selectbox(
        "Choose an Assistant",
        ["CAD Analysis", "Compliance Checker", "Quality RAG Chat", "Regulatory Scraper", "Multimodal RAG Agent"],
    )

    # Pass the database engine to the assistants
    db_engine = engine

    if page == "CAD Analysis":
        engAssistant.engineering_assistant(db_engine)
    elif page == "Compliance Checker":
        complianceAssistant.compliance_assistant(compliance_engine)
    elif page == "Quality RAG Chat":
        qualityRagChat.quality_rag_chat()
    elif page == "Regulatory Scraper":
        regulatory_scraper.regulatory_scraper_page(compliance_engine)
    elif page == "Multimodal RAG Agent":
        multimodalAssistant.multimodal_assistant_page()

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Version:** 5.1.0")
    st.sidebar.markdown("**Powered by:** Meiyume AI")

if __name__ == "__main__":
    main()
