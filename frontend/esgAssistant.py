"""
ESG Assistant - Environmental, Social, and Governance Analysis

This module provides ESG analysis functionality by uploading files to an n8n workflow
and receiving analysis results.
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime
import pandas as pd

def esg_assistant():
    """Main ESG Assistant interface"""
    
    st.title("🌱 ESG Assistant")
    st.markdown("### Factory Document Analysis for ESG")
    st.markdown("Upload factory documents (water bills, fluid usage reports, chemical inventory forms) for ESG analysis.")
    
    # Initialize session state for ESG
    if 'esg_analysis_history' not in st.session_state:
        st.session_state.esg_analysis_history = []
    
    if 'esg_current_analysis' not in st.session_state:
        st.session_state.esg_current_analysis = None
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 📄 Upload Factory Document for ESG analysis")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a document",
            type=['pdf', 'doc', 'docx', 'txt', 'csv', 'xlsx', 'jpg', 'jpeg', 'png'],
            help="Upload factory documents such as water bills, fluid usage reports, chemical inventory forms, or utility receipts"
        )
        
        if uploaded_file is not None:
            # Display file info
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            st.info(f"File size: {uploaded_file.size / 1024:.2f} KB")
            
            # Analysis button
            if st.button("🔍 Start ESG analysis", type="primary", use_container_width=True):
                analyze_esg_document(uploaded_file)
        
        # Display current analysis results
        if st.session_state.esg_current_analysis:
            display_esg_results(st.session_state.esg_current_analysis)
    
    with col2:
        st.markdown("#### 📊 Analysis History")
        display_esg_history()
        
        st.markdown("---")

        st.markdown("#### ℹ️ ESG Analysis Info")
        st.markdown("""
        **Receipt Analysis:**
        - 🌐 Language identification
        - 💧 Volume extraction (litres)
        - 🏭 Factory document processing
        """)

def analyze_esg_document(uploaded_file):
    """Analyze factory document for ESG audit using n8n workflow with Django backend integration"""
    
    with st.spinner("🔄 Analyzing factory document for ESG ..."):
        try:
            # Prepare the file for upload to n8n workflow
            files = {
                'pdfFile': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
            }
            
            # Add metadata for webhook callback (when ready)
            data = {
                'webhook_url': 'https://958ee75f6848.ngrok-free.app/api/esg/webhook/',
                'document_type': 'factory_document',
                'filename': uploaded_file.name
            }
            
            # Submit to n8n workflow
            workflow_url = "https://meiyume.app.n8n.cloud/form/6592d141-79ea-4923-809b-152a546662f7"
            
            response = requests.post(workflow_url, files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                # File submitted successfully to n8n, now wait for webhook results
                st.success("✅ File submitted to analysis workflow!")
                st.info("🔄 Processing... Results will appear below when analysis is complete.")
                
                # Create a processing record
                processing_record = {
                    "timestamp": datetime.now(),
                    "filename": uploaded_file.name,
                    "file_size": uploaded_file.size,
                    "status": "processing",
                    "results": {"message": "Analysis in progress..."},
                    "audit_type": "factory_document"
                }
                
                # Store processing record
                st.session_state.esg_current_analysis = processing_record
                st.session_state.esg_analysis_history.append(processing_record)
                
                # Start polling for results from webhook
                poll_for_webhook_results(uploaded_file.name)
                
                st.rerun()
                
            else:
                st.error(f"❌ Analysis failed with status code: {response.status_code}")
                st.error(f"Response: {response.text}")
                
        except requests.exceptions.Timeout:
            st.error("⏱️ Analysis timed out. Please try again with a smaller file.")
        except requests.exceptions.RequestException as e:
            st.error(f"🔗 Network error: {str(e)}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")

def poll_for_webhook_results(filename):
    """Poll for results from the webhook after n8n analysis"""
    
    max_attempts = 12  # Poll for up to 2 minutes (12 * 10 seconds)
    attempt = 0
    
    # Create a placeholder for status updates
    status_placeholder = st.empty()
    
    while attempt < max_attempts:
        try:
            time.sleep(10)  # Wait 10 seconds between polls
            attempt += 1
            
            # Check for latest results from webhook
            backend_url = "https://958ee75f6848.ngrok-free.app"
            response = requests.get(f"{backend_url}/api/esg/latest/", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    latest_result = data['data']
                    
                    # Check if this is a new result (simple check)
                    if latest_result.get('identified_language') and latest_result.get('identified_language') != 'Unknown':
                        # We have results! Update the current analysis
                        completed_record = {
                            "timestamp": datetime.now(),
                            "filename": filename,
                            "file_size": st.session_state.esg_current_analysis.get('file_size', 0),
                            "status": "completed",
                            "results": {
                                "identified_language": latest_result.get('identified_language'),
                                "total_litres": latest_result.get('total_litres'),
                                "raw_analysis": latest_result.get('full_payload', {})
                            },
                            "audit_type": "factory_document"
                        }
                        
                        # Update session state
                        st.session_state.esg_current_analysis = completed_record
                        
                        # Update the last item in history if it was processing
                        if (st.session_state.esg_analysis_history and 
                            st.session_state.esg_analysis_history[-1].get('status') == 'processing'):
                            st.session_state.esg_analysis_history[-1] = completed_record
                        
                        status_placeholder.success("✅ Analysis completed! Results are ready.")
                        st.rerun()
                        return
                        
            # Still processing
            status_placeholder.info(f"🔄 Still processing... (attempt {attempt}/{max_attempts})")
            
        except Exception as e:
            status_placeholder.warning(f"⚠️ Error checking results: {str(e)}")
            continue
    
    # If we get here, polling timed out
    status_placeholder.warning("⏱️ Analysis is taking longer than expected. Results will appear when ready.")

def display_esg_results(analysis_record):
    """Display results"""
    
    st.markdown("---")
    st.markdown("### 📊 ESG Analysis Results")
    
    # Analysis metadata
    col1, col2= st.columns(2)
    with col1:
        st.metric("File", analysis_record["filename"])
    with col2:
        st.metric("Status", analysis_record["status"].title())

    
    # Display results
    results = analysis_record["results"]
    
    if isinstance(results, dict):
        # Display ESG results in a clean format
        st.markdown("#### 🔍 ESG Analysis Results")
        
        # Create a simple table for the key results
        col1, col2 = st.columns(2)
        
        with col1:
            # Display language identification
            language = results.get("identified_language") or results.get("document_language", "Not detected")
            st.metric("🌐 Document Language", language)
        
        with col2:
            # Display volume extraction  
            volume = results.get("total_litres") or results.get("total_volume_litres", "Not found")
            if isinstance(volume, (int, float)):
                volume_display = f"{volume} L"
            else:
                volume_display = str(volume)
            st.metric("💧 Total Volume", volume_display)
        
        # Create a DataFrame for easy viewing and export
        esg_data = {
            "Field": ["Language", "Volume"],
            "Value": [language, volume_display]
        }
        
        # Add other fields if they exist
        if results.get("currency"):
            esg_data["Field"].append("Currency")
            esg_data["Value"].append(results.get("currency"))
        
        if results.get("total_cost"):
            esg_data["Field"].append("Total Cost")
            esg_data["Value"].append(results.get("total_cost"))
            
        if results.get("billing_period"):
            esg_data["Field"].append("Billing Period")
            esg_data["Value"].append(results.get("billing_period"))
        
        # Display as table
        import pandas as pd
        df = pd.DataFrame(esg_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Add CSV download button
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📊 Download as CSV",
            data=csv_data,
            file_name=f"esg_analysis_{analysis_record['filename']}_{analysis_record['timestamp'].strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
    else:
        # If plain text response
        st.markdown("**Analysis Results:**")
        st.write(results)
    
    # Results are displayed immediately above - no download needed

def display_esg_history():
    """Display ESG analysis history"""
    
    if not st.session_state.esg_analysis_history:
        st.info("No analysis history yet")
        return
    
    # Show recent analyses
    recent_analyses = st.session_state.esg_analysis_history[-5:]  # Last 5
    
    for i, analysis in enumerate(reversed(recent_analyses)):
        with st.expander(f"📄 {analysis['filename'][:20]}... - {analysis['timestamp'].strftime('%H:%M')}"):
            st.write(f"**File:** {analysis['filename']}")
            st.write(f"**Size:** {analysis['file_size'] / 1024:.2f} KB")
            st.write(f"**Status:** {analysis['status'].title()}")
            st.write(f"**Time:** {analysis['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            if st.button(f"View Results", key=f"view_esg_{i}"):
                st.session_state.esg_current_analysis = analysis
                st.rerun()
    
    # Clear history option
    if len(st.session_state.esg_analysis_history) > 0:
        if st.button("🗑️ Clear History", key="clear_esg_history"):
            st.session_state.esg_analysis_history = []
            st.session_state.esg_current_analysis = None
            st.rerun()

if __name__ == "__main__":
    esg_assistant()
