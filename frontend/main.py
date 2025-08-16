"""
Meiyume AI Assistant - Main Streamlit Application

A comprehensive platform for multiple AI-powered assistants including:
- CAD Analysis Assistant
- Quality Assistant
- Complaint Assistant (coming soon)
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
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-processing {
        color: #ffc107;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    .login-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        border-radius: 15px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function"""
    
    # Check authentication
    if not st.session_state.authenticated or not ensure_authenticated():
        render_login_page()
        return
    

    
    # User info in sidebar
    st.sidebar.markdown(f"👋 Welcome, **{st.session_state.user_info.get('username', 'User')}**")
    
    # Logout button
    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.jwt_tokens = None
        st.session_state.user_info = {}
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Navigation
    st.sidebar.title("🎯 Navigation")
    
    # Page selection
    page = st.sidebar.selectbox(
        "Choose a Page",
        ["🏠 Home", "📐 CAD Analysis", "🔍 Quality Assistant", "🤖 Quality RAG Chat", "📝 Complaint Assistant"],
        help="Select the page you want to view"
    )
    
    # Display selected page
    if page == "🏠 Home":
        show_home_page()
    elif page == "📐 CAD Analysis":
        show_cad_assistant()
    elif page == "🔍 Quality Assistant":
        show_quality_assistant()
    elif page == "🤖 Quality RAG Chat":
        show_quality_rag_chat()
    elif page == "📝 Complaint Assistant":
        show_complaint_assistant()
    
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
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        ### 📐 CAD Analysis
        - Advanced 2D CAD drawing analysis
        - Dimension and tolerance extraction
        - Part relationship mapping
        - Material specification detection
        """)
    
    with col2:
        st.markdown("""
        ### 🔍 Quality Assistant
        - Automated test list generation
        - Quality protocol compliance
        - Custom specification support
        - Multi-standard compatibility
        """)
    
    with col3:
        st.markdown("""
        ### 🤖 Quality RAG Chat
        - AI-powered quality control chat
        - Real-time Q&A on standards
        - Best practices guidance
        - Interactive knowledge base
        """)
    
    with col4:
        st.markdown("""
        ### 📝 Complaint Assistant
        - Customer complaint analysis
        - Sentiment analysis
        - Priority assessment
        - Automated response suggestions
        """)

def show_home_page():
    """Display the home page with overview and quick actions"""
    
    st.markdown("## 🏠 Welcome to Meiyume AI Assistant")
    st.markdown("### Your AI-powered platform for engineering, quality, and customer service excellence")
    

    st.markdown("---")
    
    # Quick actions
    st.markdown("## 🚀 Quick Actions")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Assistant cards
        st.markdown('<div class="assistant-card">', unsafe_allow_html=True)
        st.markdown("### 📐 CAD Analysis Assistant")
        st.markdown("Analyze 2D CAD PDF drawings to extract dimensions, tolerances, and part relationships using AI.")
        if st.button("🚀 Start CAD Analysis", key="home_cad", use_container_width=True):
            st.session_state.page = "📐 CAD Analysis"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown('<div class="assistant-card">', unsafe_allow_html=True)
        st.markdown("### 🔍 Quality Assistant")
        st.markdown("Generate comprehensive test lists and quality control protocols for your products.")
        if st.button("🔍 Open Quality Assistant", key="home_quality", use_container_width=True):
            st.session_state.page = "🔍 Quality Assistant"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown('<div class="assistant-card">', unsafe_allow_html=True)
        st.markdown("### 🤖 Quality RAG Chat")
        st.markdown("Chat with AI about quality control, testing protocols, standards, and best practices.")
        if st.button("🤖 Start Quality Chat", key="home_quality_chat", use_container_width=True):
            st.session_state.page = "🤖 Quality RAG Chat"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown('<div class="assistant-card">', unsafe_allow_html=True)
        st.markdown("### 📝 Complaint Assistant")
        st.markdown("Analyze and categorize customer complaints with AI-powered sentiment analysis.")
        if st.button("📝 View Complaint Assistant", key="home_complaint", use_container_width=True):
            st.session_state.page = "📝 Complaint Assistant"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📈 Recent Activity")
        
        if st.session_state.upload_history:
            for item in reversed(st.session_state.upload_history[-5:]):  # Show last 5
                with st.container():
                    status_color = {
                        'completed': '🟢',
                        'processing': '🟡',
                        'failed': '🔴',
                        'pending': '⚪'
                    }.get(item.get('status', 'unknown'), '⚪')
                    
                    st.markdown(f"**{status_color} {item.get('filename', 'Unknown')}**")
                    if item.get('project_name'):
                        st.markdown(f"*{item['project_name']}*")
                    st.markdown(f"Status: {item.get('status', 'unknown').title()}")
                    st.markdown(f"Time: {time.strftime('%H:%M', time.localtime(item.get('timestamp', 0)))}")
                    st.markdown("---")
        else:
            st.info("No recent activity")
        
        # System status
        st.markdown("### 🔧 System Status")
        try:
            response = requests.get(f"{os.getenv('DJANGO_API_URL', 'http://localhost:8000')}/api/health/", timeout=5)
            if response.status_code == 200:
                st.success("🟢 Backend Online")
            else:
                st.warning("🟡 Backend Issues")
        except:
            st.error("🔴 Backend Offline")

def show_cad_assistant():
    """Display CAD Analysis Assistant"""
    from engAssistant import engineering_assistant
    engineering_assistant()

def show_quality_assistant():
    """Display Quality Assistant"""
    from qualityAssistant import quality_assistant
    quality_assistant()

def show_quality_rag_chat():
    """Display Quality RAG Chat Assistant"""
    from qualityRagChat import quality_rag_chat
    quality_rag_chat()

def show_complaint_assistant():
    """Display Complaint Assistant"""
    from complaintAssistant import complaint_assistant
    complaint_assistant()



if __name__ == "__main__":
    main() 