import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
import time
from pathlib import Path

# Import assistant modules
from engAssistant import engineering_assistant
from qualityAssistant import quality_assistant

load_dotenv()

# Configuration
DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://localhost:8000")
UPLOAD_ENDPOINT = f"{DJANGO_API_URL}/api/upload/"
RESULTS_ENDPOINT = f"{DJANGO_API_URL}/api/results/"

# Page configuration
st.set_page_config(
    page_title="AI CAD Analyzer Hub",
    page_icon=" ",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'access_token' not in st.session_state:
        st.session_state.access_token = None
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'upload_history' not in st.session_state:
        st.session_state.upload_history = []
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Home"

def authenticate_user():
    """Handle user authentication with Azure AD"""
    st.title("🔐 Authentication Required")
    st.info("Please authenticate with your Microsoft/Azure AD credentials to access the CAD Analyzer Hub.")
    
    # For demo purposes, we'll use a simple token input
    # In production, this would integrate with Azure AD OAuth2 flow
    with st.form("auth_form"):
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if username and password:
                # In production, validate against Azure AD
                # For now, simulate successful authentication
                st.session_state.authenticated = True
                st.session_state.user_info = {"username": username, "email": f"{username}@company.com"}
                st.rerun()
            else:
                st.error("Please enter both username and password")

def upload_file_to_django(file, metadata):
    """Upload file to Django backend"""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        data = {
            "metadata": json.dumps(metadata),
            "user_id": st.session_state.user_info.get("username", "anonymous")
        }
        
        headers = {}
        if st.session_state.access_token:
            headers["Authorization"] = f"Bearer {st.session_state.access_token}"
        
        response = requests.post(
            UPLOAD_ENDPOINT,
            files=files,
            data=data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Upload failed: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Network error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Upload error: {str(e)}")
        return None

def get_processing_status(task_id):
    """Check processing status from Django backend"""
    try:
        headers = {}
        if st.session_state.access_token:
            headers["Authorization"] = f"Bearer {st.session_state.access_token}"
        
        response = requests.get(
            f"{RESULTS_ENDPOINT}{task_id}/",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
            
    except requests.exceptions.RequestException:
        return None

def sidebar_navigation():
    """Render sidebar navigation"""
    with st.sidebar:
        st.title("AI Agent Hub")
        st.markdown("---")
        
        # User info
        st.subheader("👤 User Info")
        st.write(f"**Username:** {st.session_state.user_info['username']}")
        st.write(f"**Email:** {st.session_state.user_info['email']}")
        st.markdown("---")
        
        # Navigation menu
        st.subheader("🧭 Navigation")
        
        # Home button
        if st.button("Home", use_container_width=True, 
                    type="primary" if st.session_state.current_page == "Home" else "secondary"):
            st.session_state.current_page = "Home"
            st.rerun()
        
        # Engineering Assistant button
        if st.button("Engineering Assistant", use_container_width=True,
                    type="primary" if st.session_state.current_page == "Engineering" else "secondary"):
            st.session_state.current_page = "Engineering"
            st.rerun()
        
        # Quality Assistant button
        if st.button("Quality Assistant", use_container_width=True,
                    type="primary" if st.session_state.current_page == "Quality" else "secondary"):
            st.session_state.current_page = "Quality"
            st.rerun()

        # Complaint Assistant button
        if st.button("Complaint Assistant", use_container_width=True,
                    type="primary" if st.session_state.current_page == "Complaint" else "secondary"):
            st.session_state.current_page = "Complaint"
            st.rerun()
        
        st.markdown("---")
        
        # System status
        st.subheader("🔄 System Status")
        try:
            response = requests.get(f"{DJANGO_API_URL}/api/health/", timeout=5)
            if response.status_code == 200:
                st.success("🟢 Backend: Online")
            else:
                st.error("🔴 Backend: Issues")
        except:
            st.error("🔴 Backend: Offline")
        
        st.markdown("---")
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.access_token = None
            st.session_state.user_info = None
            st.session_state.current_page = "Home"
            st.rerun()

def home_page():
    """Render the main home/hub page"""
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("AI Agent Hub")
        st.markdown("### Welcome to your Engineering & Quality Control Center")
        st.markdown("Developed by Benjamin Lau")
    
    st.markdown("---")
    
    # Overview cards
    col1, col2, col3= st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(100deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 15px; color: white; margin: 1rem 0;">
            <h3>Engineering Assistant</h3>
            <p>Advanced CAD drawing analysis powered by AI</p>
            <ul>
                <li> Dimension extraction</li>
                <li> Tolerance analysis</li>
                <li> Part relationship mapping</li>
                <li> Technical report generation</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Launch Engineering Assistant", use_container_width=True, type="primary"):
            st.session_state.current_page = "Engineering"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(100deg, #f093fb 0%, #f5576c 100%); 
                    padding: 2rem; border-radius: 15px; color: white; margin: 1rem 0;">
            <h3>Quality Assistant</h3>
            <p>Comprehensive quality control and compliance tools</p>
            <ul>
                <li> Quality standards verification</li>
                <li> Compliance checklists</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🎯 Launch Quality Assistant", use_container_width=True, type="primary"):
            st.session_state.current_page = "Quality"
            st.rerun()

    with col3:
        st.markdown("""
        <div style="background: linear-gradient(100deg, #87ceeb 0%, #B9EBFF 100%);
                    padding: 2rem; border-radius: 15px; color: white; margin: 1rem 0;">
            <h3>Complaint Assistant</h3>
            <p>Comprehensive quality control and compliance tools</p>
            <ul>
                <li> Chat Bot</li>
                <li> Potential Solutions</li>
                <li> Root cause Analysis</li>
                <li> History Searching</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("💣 Launch Complaint Assistant", use_container_width=True, type="primary"):
            st.session_state.current_page = "Complaint"
            st.rerun()
    
    st.markdown("---")
    
    # Recent activity and stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="📊 Total Analyses",
            value=len(st.session_state.upload_history),
            delta=f"+{len([h for h in st.session_state.upload_history if time.time() - h.get('timestamp', 0) < 86400])} today"
        )
    
    with col2:
        completed = len([h for h in st.session_state.upload_history if h.get('status') == 'completed'])
        st.metric(
            label="✅ Completed",
            value=completed,
            delta=f"{(completed/max(len(st.session_state.upload_history), 1)*100):.1f}% success rate"
        )
    
    with col3:
        processing = len([h for h in st.session_state.upload_history if h.get('status') == 'processing'])
        st.metric(
            label="⏳ Processing",
            value=processing
        )
    
    # Recent uploads section
    if st.session_state.upload_history:
        st.subheader("📈 Recent Activity")
        
        # Create a nice table of recent uploads
        recent_uploads = sorted(st.session_state.upload_history, 
                              key=lambda x: x.get('timestamp', 0), reverse=True)[:5]
        
        for upload in recent_uploads:
            with st.expander(f"📄 {upload.get('filename', 'Unknown')} - {upload.get('status', 'Unknown').title()}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Status:** {upload.get('status', 'Unknown').title()}")
                with col2:
                    st.write(f"**Time:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(upload.get('timestamp', 0)))}")
                with col3:
                    st.write(f"**Task ID:** {upload.get('task_id', 'N/A')}")
    
    # Quick actions
    st.markdown("---")
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📁 Upload New Drawing", use_container_width=True):
            st.session_state.current_page = "Engineering"
            st.rerun()
    
    with col2:
        if st.button("📊 View Analytics", use_container_width=True):
            st.info("Analytics dashboard coming soon!")
    
    with col3:
        if st.button("⚙️ Settings", use_container_width=True):
            st.info("Settings panel coming soon!")
    
    with col4:
        if st.button("❓ Help & Docs", use_container_width=True):
            st.info("Documentation coming soon!")

def main_app():
    """Main application interface with navigation"""
    sidebar_navigation()
    
    # Render the appropriate page based on navigation
    if st.session_state.current_page == "Home":
        home_page()
    elif st.session_state.current_page == "Engineering":
        engineering_assistant()
    elif st.session_state.current_page == "Quality":
        quality_assistant()
    elif st.session_state.current_page == "Complaint":
        complaint_assistant()

def main():
    """Main application entry point"""
    init_session_state()
    
    if not st.session_state.authenticated:
        authenticate_user()
    else:
        main_app()

if __name__ == "__main__":
    main() 