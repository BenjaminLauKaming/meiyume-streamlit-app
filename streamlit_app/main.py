import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
import time
from pathlib import Path

load_dotenv()

# Configuration
DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://localhost:8000")
UPLOAD_ENDPOINT = f"{DJANGO_API_URL}/api/upload/"
RESULTS_ENDPOINT = f"{DJANGO_API_URL}/api/results/"

# Page configuration
st.set_page_config(
    page_title="AI CAD Analyzer",
    page_icon="🔧",
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

def authenticate_user():
    """Handle user authentication with Azure AD"""
    st.title("🔐 Authentication Required")
    st.info("Please authenticate with your Microsoft/Azure AD credentials to access the CAD Analyzer.")
    
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

def main_app():
    """Main application interface"""
    st.title("🔧 AI CAD Analyzer")
    st.markdown("### Analyze 2D CAD PDF drawings with AI-powered dimension extraction")
    
    # Sidebar user info
    with st.sidebar:
        st.subheader("👤 User Info")
        st.write(f"**Username:** {st.session_state.user_info['username']}")
        st.write(f"**Email:** {st.session_state.user_info['email']}")
        

        # Logout button
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.access_token = None
            st.session_state.user_info = None
            st.rerun()
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📁 Upload CAD Drawing")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload a 2D CAD drawing in PDF format"
        )
        
        if uploaded_file is not None:
            # Display file info
            st.success(f"File uploaded: {uploaded_file.name}")
            st.info(f"File size: {uploaded_file.size / 1024:.2f} KB")
            
            # Metadata input
            with st.expander("📋 Additional Information (Optional)"):
                project_name = st.text_input("Project Name")
                drawing_number = st.text_input("Drawing Number")
                revision = st.text_input("Revision")
                notes = st.text_area("Notes")
            
            # Analysis options
            st.subheader("⚙️ Analysis Options")
            extract_dimensions = st.checkbox("Extract Dimensions", value=True)
            extract_tolerances = st.checkbox("Extract Tolerances", value=True)
            part_relationships = st.checkbox("Analyze Part Relationships", value=True)
            
            # Process button
            if st.button("🚀 Start Analysis", type="primary"):
                metadata = {
                    "project_name": project_name,
                    "drawing_number": drawing_number,
                    "revision": revision,
                    "notes": notes,
                    "analysis_options": {
                        "extract_dimensions": extract_dimensions,
                        "extract_tolerances": extract_tolerances,
                        "part_relationships": part_relationships
                    }
                }
                
                with st.spinner("Uploading file and starting analysis..."):
                    result = upload_file_to_django(uploaded_file, metadata)
                    
                    if result:
                        st.success("File uploaded successfully!")
                        task_id = result.get("task_id")
                        
                        if task_id:
                            st.session_state.upload_history.append({
                                "task_id": task_id,
                                "filename": uploaded_file.name,
                                "timestamp": time.time(),
                                "status": "processing"
                            })
                            
                            # Show processing status
                            status_placeholder = st.empty()
                            progress_bar = st.progress(0)
                            
                            # Poll for results
                            max_attempts = 30  # 5 minutes max
                            for attempt in range(max_attempts):
                                status_data = get_processing_status(task_id)
                                
                                if status_data:
                                    status = status_data.get("status", "processing")
                                    progress = status_data.get("progress", 0)
                                    
                                    status_placeholder.info(f"Status: {status.title()}")
                                    progress_bar.progress(min(progress / 100, 1.0))
                                    
                                    if status == "completed":
                                        st.success("Analysis completed!")
                                        
                                        # Display results
                                        if "results" in status_data:
                                            display_results(status_data["results"])
                                        
                                        # Update history
                                        for item in st.session_state.upload_history:
                                            if item["task_id"] == task_id:
                                                item["status"] = "completed"
                                        break
                                    elif status == "failed":
                                        st.error("Analysis failed. Please try again.")
                                        break
                                
                                time.sleep(10)  # Wait 10 seconds before next check
                            else:
                                st.warning("Analysis is taking longer than expected. Check back later.")
    
    with col2:
        st.subheader("📊 Recent Uploads")
        
        if st.session_state.upload_history:
            for item in reversed(st.session_state.upload_history[-5:]):  # Show last 5
                with st.container():
                    st.markdown(f"**{item['filename']}**")
                    st.markdown(f"Status: {item['status'].title()}")
                    st.markdown(f"Time: {time.strftime('%H:%M:%S', time.localtime(item['timestamp']))}")
                    st.markdown("---")
        else:
            st.info("No recent uploads")

def display_results(results):
    """Display analysis results"""
    st.subheader("📈 Analysis Results")
    
    # Create tabs for different result types
    tabs = st.tabs(["📏 Dimensions", "🎯 Tolerances", "🔗 Relationships", "📥 Downloads"])
    
    with tabs[0]:
        if "dimensions" in results:
            st.json(results["dimensions"])
        else:
            st.info("No dimension data available")
    
    with tabs[1]:
        if "tolerances" in results:
            st.json(results["tolerances"])
        else:
            st.info("No tolerance data available")
    
    with tabs[2]:
        if "relationships" in results:
            st.json(results["relationships"])
        else:
            st.info("No relationship data available")
    
    with tabs[3]:
        st.subheader("Download Results")
        if "download_urls" in results:
            for file_type, url in results["download_urls"].items():
                st.download_button(
                    label=f"Download {file_type.upper()}",
                    data=requests.get(url).content,
                    file_name=f"analysis_results.{file_type}",
                    mime=f"application/{file_type}"
                )

def main():
    """Main application entry point"""
    init_session_state()
    
    if not st.session_state.authenticated:
        authenticate_user()
    else:
        main_app()

if __name__ == "__main__":
    main() 