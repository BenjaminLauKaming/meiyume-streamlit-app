"""
Meiyume AI Assistant - Main Streamlit Application

A comprehensive platform for multiple AI-powered assistants including:
- CAD Analysis Assistant
- Quality RAG Chat Assistant
"""

import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd
import time
import os
from dotenv import load_dotenv
from auth_utils import ensure_authenticated, render_login_form

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Meiyume AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'upload_history' not in st.session_state:
    st.session_state.upload_history = []

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'jwt_tokens' not in st.session_state:
    st.session_state.jwt_tokens = None

if 'user_info' not in st.session_state:
    st.session_state.user_info = {}

# Custom CSS for better styling
st.markdown("""
<style>
    .assistant-card {
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 1rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease;
    }
    
    .assistant-card:hover {
        transform: translateY(-2px);
    }
    
    .assistant-card.cad {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .assistant-card.quality {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    .assistant-card.file-management {
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
    }
    
    .assistant-card.esg {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    
    .assistant-card h3 {
        margin-top: 0;
        margin-bottom: 1rem;
        font-size: 1.2rem;
    }
    
    .assistant-card p {
        margin-bottom: 0;
        font-size: 0.9rem;
        line-height: 1.4;
    }
    
    .login-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        border-radius: 15px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .sidebar-logo {
        display: flex;
        justify-content: center;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function"""
    
    # Temporarily disable authentication for testing
    # if not st.session_state.authenticated or not ensure_authenticated():
    #     render_login_page()
    #     return
    
    # Set authenticated for testing
    st.session_state.authenticated = True
    st.session_state.user_info = {"username": "test_user"}
    

    
    # Logo and Navigation
    st.sidebar.markdown(
        f'''
        <div class="sidebar-logo">
            <img src="https://meiyume-website-media.s3.ap-southeast-1.amazonaws.com/wp-content/uploads/2020/08/14174032/Meiyume_footer_logo-e1667547906481.png" width="200">
        </div>
        ''',
        unsafe_allow_html=True
    )
    st.sidebar.title("🎯 Navigation")
    
    # Page selection
    page = st.sidebar.selectbox(
        "Choose a Page",
        ["🏠 Home", "📐 CAD Analysis", "🤖 Quality RAG Chat", "📁 RAG File Management", "🌱 ESG Analysis", "🧪 Compliance Checker"],
        help="Select the page you want to view"
    )
    
    # Display selected page
    if page == "🏠 Home":
        show_home_page()
    elif page == "📐 CAD Analysis":
        show_cad_assistant()
    elif page == "🤖 Quality RAG Chat":
        show_quality_rag_chat()
    elif page == "📁 RAG File Management":
        show_rag_file_management()
    elif page == "🌱 ESG Analysis":
        show_esg_assistant()
    elif page == "🧪 Compliance Checker":
        show_compliance_checker()
    
    # User info and logout at bottom
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"👋 Welcome, **{st.session_state.user_info.get('username', 'User')}**")
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.jwt_tokens = None
        st.session_state.user_info = {}
        st.rerun()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Version:** 2.0.0")
    st.sidebar.markdown("**Powered by:** Meiyume AI")

def render_login_page():
    """Render the login page"""
 
    
    # Welcome message
    st.markdown("""
    <div style="text-align: center; margin: 0;">
        <h2>Welcome to Meiyume AI Assistant Platform</h2>
        <p>Your comprehensive AI-powered assistant for CAD analysis, quality control, and complaint management.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Login form
    render_login_form()
    
    # Features preview
    st.markdown("---")
    st.markdown("## 🚀 Platform Features")
    
    st.markdown("""
    ### 📐 CAD Analysis
    - Advanced 2D CAD drawing analysis
    - Dimension and tolerance extraction
    - Part relationship mapping
    - Material specification detection
    
    ### 🤖 Quality RAG Chat
    - AI-powered quality control chat
    - Real-time Q&A on standards
    - Best practices guidance
    - Interactive knowledge base
    
    ### 📁 RAG File Management
    - Upload complaint records and detail reports
    - Manage RAG knowledge base documents
    - File categorization and tagging
    - Content preview and organization
    
    ### 🌱 ESG Audit
    - Factory document analysis
    - Language identification
    - Volume extraction (litres)
    - Utility consumption tracking
    """)

def show_home_page():
    """Display the home page with overview and quick actions"""
    
    st.markdown("## 🏠 Welcome to Meiyume AI Assistant")
    st.markdown("### Your AI-powered platform for engineering, quality, and customer service excellence")
    

    st.markdown("---")

    
    # Assistant cards using Streamlit columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="assistant-card cad">
            <h3>📐 CAD Analysis Assistant</h3>
            <p>Analyze 2D CAD PDF drawings to extract dimensions, tolerances, and part relationships using AI.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Start CAD Analysis", key="home_cad", use_container_width=True):
            st.session_state.page = "📐 CAD Analysis"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="assistant-card quality">
            <h3>🤖 Quality RAG Chat</h3>
            <p>Chat with AI about quality control, testing protocols, standards, and best practices.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🤖 Start Quality Chat", key="home_quality_chat", use_container_width=True):
            st.session_state.page = "🤖 Quality RAG Chat"
            st.rerun()
    
    # Second row of cards
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("""
        <div class="assistant-card file-management">
            <h3>📁 RAG File Management</h3>
            <p>Upload and manage complaint records and detail reports for the RAG knowledge base.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📁 Manage Files", key="home_file_management", use_container_width=True):
            st.session_state.page = "📁 RAG File Management"
            st.rerun()
    
    with col4:
        st.markdown("""
        <div class="assistant-card esg">
            <h3>🌱 ESG Audit Assistant</h3>
            <p>Upload factory documents (receipts, bills, reports) for ESG analysis and volume extraction.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🌱 Start ESG Audit", key="home_esg", use_container_width=True):
            st.session_state.page = "🌱 ESG Analysis"
            st.rerun()
    

def show_cad_assistant():
    """Display CAD Analysis Assistant"""
    from engAssistant import engineering_assistant
    engineering_assistant()

def show_quality_rag_chat():
    """Display Quality RAG Chat Assistant"""
    from qualityRagChat import quality_rag_chat
    quality_rag_chat()

def show_rag_file_management():
    """Display RAG File Management Interface"""
    from qualityRagChat import rag_file_management
    rag_file_management()

def show_esg_assistant():
    """Display ESG Analysis Assistant"""
    from esgAssistant import esg_assistant
    esg_assistant()

def show_compliance_checker():
    """Display Compliance Checker"""
    from complianceAssistant import compliance_assistant
    compliance_assistant()

if __name__ == "__main__":
    main() 