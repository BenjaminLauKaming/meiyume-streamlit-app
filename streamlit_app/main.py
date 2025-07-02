"""
Meiyume AI Assistant - Main Streamlit Application

A comprehensive platform for multiple AI-powered assistants including:
- CAD Analysis Assistant
- Quality Assistant (coming soon)
- Complaint Assistant (coming soon)
"""

import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Meiyume AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
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
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function"""
    
    # Main header
    st.markdown('<h1 class="main-header">🤖 Meiyume AI Assistant</h1>', unsafe_allow_html=True)
    
    # Sidebar for navigation
    st.sidebar.title("🎯 AI Assistants")
    
    # Assistant selection
    assistant = st.sidebar.selectbox(
        "Choose an Assistant",
        ["CAD Analysis", "Quality Assistant", "Complaint Assistant"],
        help="Select the AI assistant you want to use"
    )
    
    # Display selected assistant
    if assistant == "CAD Analysis":
        show_cad_assistant()
    elif assistant == "Quality Assistant":
        show_quality_assistant()
    elif assistant == "Complaint Assistant":
        show_complaint_assistant()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Version:** 1.0.0")
    st.sidebar.markdown("**Powered by:** Meiyume AI")

def show_cad_assistant():
    """Display CAD Analysis Assistant"""
    
    st.markdown('<div class="assistant-card">', unsafe_allow_html=True)
    st.markdown("## 📐 CAD Analysis Assistant")
    st.markdown("Analyze 2D CAD PDF drawings to extract dimensions, tolerances, and part relationships using AI.")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Import and show CAD assistant
    try:
        from engAssistant import engineering_assistant
        engineering_assistant()
    except ImportError:
        st.error("CAD Analysis Assistant is not available. Please check the installation.")
        st.info("The CAD assistant module could not be loaded. This might be due to missing dependencies or configuration issues.")

def show_quality_assistant():
    """Display Quality Assistant (placeholder)"""
    
    st.markdown('<div class="assistant-card">', unsafe_allow_html=True)
    st.markdown("## 🔍 Quality Assistant")
    st.markdown("Quality control and inspection analysis with defect detection and classification.")
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.info("🚧 Quality Assistant is coming soon!")
    st.markdown("""
    **Planned Features:**
    - Quality control analysis
    - Defect detection and classification
    - Quality metrics and reporting
    - Automated inspection workflows
    
    This assistant will help you analyze quality control data and identify potential issues in manufacturing processes.
    """)

def show_complaint_assistant():
    """Display Complaint Assistant (placeholder)"""
    
    st.markdown('<div class="assistant-card">', unsafe_allow_html=True)
    st.markdown("## 📝 Complaint Assistant")
    st.markdown("Customer complaint analysis and categorization with sentiment analysis and priority assessment.")
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.info("🚧 Complaint Assistant is coming soon!")
    st.markdown("""
    **Planned Features:**
    - Customer complaint analysis
    - Sentiment analysis
    - Priority assessment
    - Automated response suggestions
    - Trend analysis and reporting
    
    This assistant will help you process and analyze customer complaints to improve customer satisfaction and product quality.
    """)

def show_dashboard():
    """Show dashboard with statistics across all assistants"""
    
    st.markdown("## 📊 Dashboard")
    
    # Get statistics from API
    try:
        response = requests.get("http://localhost:8000/api/dashboard/stats/")
        if response.status_code == 200:
            stats = response.json()
            
            # Display statistics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Uploads", stats.get('total_uploads', 0))
            
            with col2:
                st.metric("Completed", stats.get('completed_uploads', 0))
            
            with col3:
                st.metric("Processing", stats.get('processing_uploads', 0))
            
            with col4:
                st.metric("Failed", stats.get('failed_uploads', 0))
            
            # Recent activity
            st.subheader("Recent Activity")
            recent_uploads = stats.get('recent_uploads', [])
            
            if recent_uploads:
                df = pd.DataFrame(recent_uploads)
                st.dataframe(df)
            else:
                st.info("No recent activity to display.")
                
        else:
            st.error("Failed to load dashboard statistics.")
            
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

if __name__ == "__main__":
    main() 