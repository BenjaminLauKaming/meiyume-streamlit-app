import streamlit as st
import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

# Configuration
DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://localhost:8000")
UPLOAD_ENDPOINT = f"{DJANGO_API_URL}/api/upload/"
RESULTS_ENDPOINT = f"{DJANGO_API_URL}/api/results/"

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

def engineering_assistant():
    """Engineering Assistant main interface"""
    st.title("⚙️ Engineering Assistant")
    st.markdown("### Advanced CAD Drawing Analysis with AI")
    
    # Quick stats at the top
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📊 Total Uploads",
            value=len(st.session_state.upload_history)
        )
    
    with col2:
        completed = len([h for h in st.session_state.upload_history if h.get('status') == 'completed'])
        st.metric(
            label="✅ Completed",
            value=completed
        )
    
    with col3:
        processing = len([h for h in st.session_state.upload_history if h.get('status') == 'processing'])
        st.metric(
            label="⏳ Processing",
            value=processing
        )
    
    with col4:
        today_uploads = len([h for h in st.session_state.upload_history 
                           if time.time() - h.get('timestamp', 0) < 86400])
        st.metric(
            label="📅 Today",
            value=today_uploads
        )
    
    st.markdown("---")
    
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
                col_a, col_b = st.columns(2)
                with col_a:
                    project_name = st.text_input("Project Name")
                    drawing_number = st.text_input("Drawing Number")
                with col_b:
                    revision = st.text_input("Revision")
                    priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
                notes = st.text_area("Notes")
            
            # Analysis options
            st.subheader("⚙️ Analysis Options")
            
            col_x, col_y = st.columns(2)
            with col_x:
                extract_dimensions = st.checkbox("📏 Extract Dimensions", value=True)
                extract_tolerances = st.checkbox("🎯 Extract Tolerances", value=True)
                part_relationships = st.checkbox("🔗 Analyze Part Relationships", value=True)
            
            with col_y:
                material_analysis = st.checkbox("🔬 Material Analysis", value=False)
                surface_finish = st.checkbox("✨ Surface Finish Detection", value=False)
                assembly_info = st.checkbox("🔧 Assembly Information", value=False)
            
            # Advanced options
            with st.expander("🔧 Advanced Options"):
                ai_model = st.selectbox(
                    "AI Model",
                    ["Gemini 2.5 Flash (Default)", "Gemini Pro", "Custom Model"],
                    help="Select the AI model for analysis"
                )
                
                output_format = st.multiselect(
                    "Output Formats",
                    ["CSV", "Excel", "JSON", "PDF Report"],
                    default=["CSV"]
                )
                
                accuracy_level = st.slider(
                    "Accuracy Level",
                    min_value=1,
                    max_value=5,
                    value=3,
                    help="Higher accuracy takes longer but provides better results"
                )
            
            # Process button
            if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
                metadata = {
                    "project_name": project_name,
                    "drawing_number": drawing_number,
                    "revision": revision,
                    "priority": priority,
                    "notes": notes,
                    "analysis_options": {
                        "extract_dimensions": extract_dimensions,
                        "extract_tolerances": extract_tolerances,
                        "part_relationships": part_relationships,
                        "material_analysis": material_analysis,
                        "surface_finish": surface_finish,
                        "assembly_info": assembly_info,
                        "ai_model": ai_model,
                        "output_format": output_format,
                        "accuracy_level": accuracy_level
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
                                "status": "processing",
                                "project_name": project_name,
                                "priority": priority
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
            # Filter for engineering uploads only
            eng_uploads = [h for h in st.session_state.upload_history if h.get('task_id')]
            
            for item in reversed(eng_uploads[-5:]):  # Show last 5
                with st.container():
                    status_color = {
                        'completed': '🟢',
                        'processing': '🟡',
                        'failed': '🔴',
                        'pending': '⚪'
                    }.get(item.get('status', 'unknown'), '⚪')
                    
                    st.markdown(f"**{status_color} {item['filename']}**")
                    if item.get('project_name'):
                        st.markdown(f"*Project: {item['project_name']}*")
                    st.markdown(f"Status: {item['status'].title()}")
                    st.markdown(f"Time: {time.strftime('%H:%M:%S', time.localtime(item['timestamp']))}")
                    
                    # Quick action buttons
                    if item['status'] == 'completed':
                        if st.button(f"📥 Download Results", key=f"download_{item['task_id']}"):
                            st.info("Download functionality coming soon!")
                    
                    st.markdown("---")
        else:
            st.info("No recent uploads")
        
        # Quick actions
        st.subheader("🚀 Quick Actions")
        
        if st.button("📚 View Templates", use_container_width=True):
            st.info("Template library coming soon!")
        
        if st.button("📊 Analysis History", use_container_width=True):
            st.info("Full history view coming soon!")
        
        if st.button("⚙️ Export Settings", use_container_width=True):
            st.info("Settings export coming soon!")
        
        if st.button("❓ Help Guide", use_container_width=True):
            with st.expander("🔍 Quick Help"):
                st.markdown("""
                **Supported File Types:**
                - PDF (2D CAD drawings)
                
                **Analysis Features:**
                - 📏 Dimension extraction
                - 🎯 Tolerance analysis  
                - 🔗 Part relationships
                - 🔬 Material detection
                - ✨ Surface finish
                
                **Tips:**
                - Use high-quality PDFs for best results
                - Include drawing numbers for tracking
                - Higher accuracy = longer processing time
                """)
