import streamlit as st
import requests
import json
import os
import time
import pandas as pd
from datetime import datetime, timezone
from io import BytesIO
from dotenv import load_dotenv
from auth_utils import get_auth_headers


load_dotenv()

# Configuration
DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://localhost:8000")

def generate_fake_cad_results():
    """Generate realistic fake CAD analysis results"""
    return {
        "results": [
            {
                "result_type": "dimensions",
                "raw_data": {
                    "parts": [
                        {
                            "name": "Perfume Cap",
                            "dimensions": [
                                {"name": "Outer Diameter", "value": 24.5, "unit": "mm", "tolerance": "±0.1", "critical": True},
                                {"name": "Inner Diameter", "value": 22.3, "unit": "mm", "tolerance": "±0.1", "critical": True},
                                {"name": "Height", "value": 15.2, "unit": "mm", "tolerance": "±0.2", "critical": False},
                                {"name": "Thread Pitch", "value": 1.5, "unit": "mm", "tolerance": "±0.05", "critical": True},
                                {"name": "Wall Thickness", "value": 1.1, "unit": "mm", "tolerance": "±0.1", "critical": False}
                            ]
                        },
                        {
                            "name": "Spray Head",
                            "dimensions": [
                                {"name": "Nozzle Diameter", "value": 0.8, "unit": "mm", "tolerance": "±0.02", "critical": True},
                                {"name": "Body Diameter", "value": 12.5, "unit": "mm", "tolerance": "±0.1", "critical": False},
                                {"name": "Length", "value": 28.7, "unit": "mm", "tolerance": "±0.2", "critical": False},
                                {"name": "Spring Travel", "value": 3.2, "unit": "mm", "tolerance": "±0.1", "critical": True},
                                {"name": "Actuator Force", "value": 2.5, "unit": "N", "tolerance": "±0.3", "critical": True}
                            ]
                        },
                        {
                            "name": "Bottle Neck",
                            "dimensions": [
                                {"name": "External Thread Diameter", "value": 22.0, "unit": "mm", "tolerance": "±0.1", "critical": True},
                                {"name": "Internal Diameter", "value": 18.5, "unit": "mm", "tolerance": "±0.1", "critical": False},
                                {"name": "Thread Height", "value": 8.0, "unit": "mm", "tolerance": "±0.1", "critical": False},
                                {"name": "Neck Height", "value": 25.0, "unit": "mm", "tolerance": "±0.2", "critical": False},
                                {"name": "Shoulder Radius", "value": 5.0, "unit": "mm", "tolerance": "±0.2", "critical": False}
                            ]
                        }
                    ],
                    "contact_pairs": [
                        {
                            "part1": "Perfume Cap",
                            "part2": "Bottle Neck", 
                            "contact_type": "Thread Connection",
                            "fit_status": "Good Fit",
                            "clearance": 0.2,
                            "unit": "mm"
                        },
                        {
                            "part1": "Spray Head",
                            "part2": "Bottle Neck",
                            "contact_type": "Press Fit",
                            "fit_status": "Tight Fit", 
                            "clearance": -0.1,
                            "unit": "mm"
                        },
                        {
                            "part1": "Perfume Cap",
                            "part2": "Spray Head",
                            "contact_type": "Clearance Fit",
                            "fit_status": "Good Fit",
                            "clearance": 0.3,
                            "unit": "mm"
                        },
                        {
                            "part1": "Bottle Neck",
                            "part2": "Perfume Cap",
                            "contact_type": "Sealing Surface",
                            "fit_status": "Perfect Fit",
                            "clearance": 0.05,
                            "unit": "mm"
                        }
                    ]
                }
            }
        ]
    }

def simulate_workflow_processing():
    """Simplified workflow simulation with just progress bar and status"""
    steps = [
        ("📤 Uploading file to Django backend...", 0.15),
        ("⚙️ Django processing file and preparing for n8n...", 0.30),
        ("🔄 Starting n8n workflow...", 0.45),
        ("📡 Uploading file to Gemini AI...", 0.60),
        ("🤖 Gemini AI analyzing CAD drawing...", 0.85),
        ("📤 Sending results back to Django...", 1.0)
    ]
    
    # Create containers
    progress_bar = st.progress(0)
    status_container = st.empty()
    
    # Simulate processing
    for step_text, progress in steps:
        status_container.info(step_text)
        progress_bar.progress(progress)
        time.sleep(0.8)  # Shorter delay
    
    # Final success message
    status_container.success("✅ Analysis completed successfully!")
    time.sleep(0.5)
    
    return generate_fake_cad_results()

def run_demo_analysis(filename=None):
    """Consolidated demo analysis function"""
    st.markdown("---")
    st.markdown("### 🧪 Running Demo Analysis...")
    
    if filename:
        st.info(f"Processing: {filename}")
    
    # Run simulation
    results = simulate_workflow_processing()
    
    st.markdown("---")
    st.markdown("### 📊 Demo Analysis Results")
    display_results_spreadsheet(results)

def display_results_spreadsheet(results_data):
    """Display CAD analysis results in a beautiful spreadsheet format"""
    st.subheader("📈 Analysis Results - Spreadsheet View")
    
    # Create tabs for different result types
    tabs = st.tabs(["📊 Parts & Dimensions", "🔗 Part Relationships", "📋 Summary", "📥 Downloads"])
    
    with tabs[0]:
        st.markdown("### 📏 Parts and Dimensions Analysis")
        
        # Find the dimensions result
        dimensions_result = None
        for result in results_data.get("results", []):
            if result.get("result_type") == "dimensions":
                dimensions_result = result
                break
        
        if dimensions_result and "parts" in dimensions_result.get("raw_data", {}):
            parts_data = dimensions_result["raw_data"]["parts"]
            
            # Create a comprehensive dataframe for all parts and dimensions
            all_dimensions = []
            
            for part in parts_data:
                part_name = part.get("name", "Unknown Part")
                dimensions = part.get("dimensions", [])
                
                for dim in dimensions:
                    all_dimensions.append({
                        "Part Name": part_name,
                        "Feature": dim.get("name", ""),
                        "Value": dim.get("value", ""),
                        "Tolerance": dim.get("tolerance", ""),
                        "Unit": dim.get("unit", ""),
                        "Critical": "✅" if dim.get("critical", False) else "❌"
                    })
            
            if all_dimensions:
                df = pd.DataFrame(all_dimensions)
                
                # Display the dataframe with styling
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Part Name": st.column_config.TextColumn("Part Name", width="medium"),
                        "Feature": st.column_config.TextColumn("Feature", width="large"),
                        "Value": st.column_config.NumberColumn("Value", format="%.3f"),
                        "Tolerance": st.column_config.TextColumn("Tolerance", width="small"),
                        "Unit": st.column_config.TextColumn("Unit", width="small"),
                        "Critical": st.column_config.TextColumn("Critical", width="small")
                    }
                )
                
                # Add filters and search
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    part_filter = st.selectbox(
                        "Filter by Part",
                        ["All Parts"] + list(df["Part Name"].unique())
                    )
                
                with col2:
                    critical_only = st.checkbox("Show Critical Dimensions Only")
                
                # Apply filters
                filtered_df = df.copy()
                if part_filter != "All Parts":
                    filtered_df = filtered_df[filtered_df["Part Name"] == part_filter]
                if critical_only:
                    filtered_df = filtered_df[filtered_df["Critical"] == "✅"]
                
                if len(filtered_df) != len(df):
                    st.markdown(f"**Showing {len(filtered_df)} of {len(df)} dimensions**")
                    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
                
                # Summary statistics
                st.markdown("---")
                st.markdown("### 📊 Summary Statistics")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Parts", len(parts_data))
                
                with col2:
                    st.metric("Total Dimensions", len(all_dimensions))
                
                with col3:
                    critical_count = len([d for d in all_dimensions if d["Critical"] == "✅"])
                    st.metric("Critical Dimensions", critical_count)
                
                with col4:
                    interior_count = len([d for d in all_dimensions if d["Critical"] == "❌"])
                    st.metric("Non-Critical Dimensions", interior_count)
                
            else:
                st.info("No dimension data available")
        else:
            st.info("No dimension data available")
    
    with tabs[1]:
        st.markdown("### 🔗 Part Relationships & Fits")
        
        if dimensions_result and "contact_pairs" in dimensions_result.get("raw_data", {}):
            contact_pairs = dimensions_result["raw_data"]["contact_pairs"]
            
            if contact_pairs:
                # Create relationship dataframe
                relationships = []
                
                for pair in contact_pairs:
                    relationships.append({
                        "Part A": pair.get("part1", ""),
                        "Part B": pair.get("part2", ""),
                        "Contact Type": pair.get("contact_type", ""),
                        "Fit Status": pair.get("fit_status", ""),
                        "Clearance": f"{pair.get('clearance', '0')} {pair.get('unit', '')}"
                    })
                
                rel_df = pd.DataFrame(relationships)
                
                # Display with styling
                st.dataframe(
                    rel_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Part A": st.column_config.TextColumn("Part A", width="medium"),
                        "Part B": st.column_config.TextColumn("Part B", width="medium"),
                        "Contact Type": st.column_config.TextColumn("Contact Type", width="large"),
                        "Fit Status": st.column_config.TextColumn("Fit Status", width="large"),
                        "Clearance": st.column_config.TextColumn("Clearance", width="small")
                    }
                )
                
                # Fit status summary
                st.markdown("---")
                st.markdown("### 🎯 Fit Analysis Summary")
                
                fit_counts = rel_df["Fit Status"].value_counts()
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    compatible = fit_counts.get("Good Fit", 0)
                    st.metric("✅ Good Fit", compatible)
                
                with col2:
                    tight = fit_counts.get("Tight Fit", 0)
                    st.metric("⚠️ Tight Fit", tight)
                
                with col3:
                    loose = fit_counts.get("Loose Fit", 0)
                    st.metric("❌ Loose Fit", loose)
                
                with col4:
                    perfect = fit_counts.get("Perfect Fit", 0)
                    st.metric("🎯 Perfect Fit", perfect)
                
            else:
                st.info("No part relationships detected")
        else:
            st.info("No relationship data available")
    
    with tabs[2]:
        st.markdown("### 📋 Analysis Summary")
        
        if dimensions_result:
            # Extract summary data
            parts_data = dimensions_result["raw_data"].get("parts", [])
            contact_pairs = dimensions_result["raw_data"].get("contact_pairs", [])
            
            # Create summary metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📏 Dimension Summary")
                
                total_dimensions = sum(len(part.get("dimensions", [])) for part in parts_data)
                critical_dimensions = sum(
                    sum(1 for dim in part.get("dimensions", []) if dim.get("critical", False))
                    for part in parts_data
                )
                
                st.metric("Total Parts Analyzed", len(parts_data))
                st.metric("Total Dimensions", total_dimensions)
                st.metric("Critical Dimensions", critical_dimensions)
                st.metric("Part Relationships", len(contact_pairs))
            
            with col2:
                st.markdown("#### 🎯 Quality Metrics")
                
                if total_dimensions > 0:
                    critical_percentage = (critical_dimensions / total_dimensions) * 100
                    st.metric("Critical Dimension %", f"{critical_percentage:.1f}%")
                
                if contact_pairs:
                    compatible_pairs = sum(1 for pair in contact_pairs if pair.get("fit_status") == "Good Fit")
                    compatibility_rate = (compatible_pairs / len(contact_pairs)) * 100
                    st.metric("Compatibility Rate", f"{compatibility_rate:.1f}%")
            
            # Part breakdown
            st.markdown("---")
            st.markdown("#### 📊 Part Breakdown")
            
            if parts_data:
                part_summary = []
                for part in parts_data:
                    part_name = part.get("name", "Unknown")
                    dimensions = part.get("dimensions", [])
                    critical_count = sum(1 for dim in dimensions if dim.get("critical", False))
                    
                    part_summary.append({
                        "Part Name": part_name,
                        "Total Dimensions": len(dimensions),
                        "Critical Dimensions": critical_count,
                        "Features": ", ".join([dim.get("name", "") for dim in dimensions[:3]]) + ("..." if len(dimensions) > 3 else "")
                    })
                
                summary_df = pd.DataFrame(part_summary)
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    with tabs[3]:
        st.subheader("📥 Download Results")
        
        if dimensions_result:
            # Generate downloadable files
            
            # Create dimensions CSV
            if "parts" in dimensions_result["raw_data"]:
                all_dimensions = []
                for part in dimensions_result["raw_data"]["parts"]:
                    part_name = part.get("name", "Unknown Part")
                    for dim in part.get("dimensions", []):
                        all_dimensions.append({
                            "Part Name": part_name,
                            "Feature": dim.get("name", ""),
                            "Value": dim.get("value", ""),
                            "Tolerance": dim.get("tolerance", ""),
                            "Unit": dim.get("unit", ""),
                            "Critical": dim.get("critical", False)
                        })
                
                if all_dimensions:
                    df_dimensions = pd.DataFrame(all_dimensions)
                    csv_buffer = BytesIO()
                    df_dimensions.to_csv(csv_buffer, index=False)
                    csv_buffer.seek(0)
                    
                    st.download_button(
                        label="📊 Download Dimensions (CSV)",
                        data=csv_buffer.getvalue(),
                        file_name="cad_dimensions.csv",
                        mime="text/csv"
                    )
            
            # Create relationships CSV
            if "contact_pairs" in dimensions_result["raw_data"]:
                relationships = dimensions_result["raw_data"]["contact_pairs"]
                if relationships:
                    df_relationships = pd.DataFrame(relationships)
                    csv_buffer = BytesIO()
                    df_relationships.to_csv(csv_buffer, index=False)
                    csv_buffer.seek(0)
                    
                    st.download_button(
                        label="🔗 Download Relationships (CSV)",
                        data=csv_buffer.getvalue(),
                        file_name="cad_relationships.csv",
                        mime="text/csv"
                    )
            
            # Download full JSON report
            json_buffer = BytesIO()
            json_str = json.dumps(dimensions_result["raw_data"], indent=2)
            json_buffer.write(json_str.encode('utf-8'))
            json_buffer.seek(0)
            
            st.download_button(
                label="📄 Download Full Report (JSON)",
                data=json_buffer.getvalue(),
                file_name="cad_analysis_report.json",
                mime="application/json"
            )
        
        st.info("💡 Tip: Use the CSV files to import data into Excel or other spreadsheet applications for further analysis.")
UPLOAD_ENDPOINT = f"{DJANGO_API_URL}/api/cad/uploads/"
RESULTS_ENDPOINT = f"{DJANGO_API_URL}/api/cad/results/"

def upload_file_to_django(file, metadata):
    """Upload file to Django backend"""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        data = {
            "metadata": json.dumps(metadata),
            "user_id": st.session_state.user_info.get("username", "anonymous")
        }
        
        headers = get_auth_headers()
        
        response = requests.post(
            UPLOAD_ENDPOINT,
            files=files,
            data=data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code in [200, 201]:  # 200 = OK, 201 = Created
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
        headers = get_auth_headers()
        
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

def upload_file_with_progress(uploaded_file):
    """Upload file with progress display similar to simulation"""
    steps = [
        ("📤 Uploading file to Django backend...", 0.20),
        ("⚙️ Django processing file and preparing for n8n...", 0.40),
        ("🔄 Starting n8n workflow...", 0.60),
        ("📡 Processing with AI...", 0.80),
        ("📊 Generating results...", 1.0)
    ]
    
    # Create containers
    progress_bar = st.progress(0)
    status_container = st.empty()
    
    try:
        # Step 1: Upload
        status_container.info(steps[0][0])
        progress_bar.progress(steps[0][1])
        
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        data = {"assistant_type": "cad"}
        
        response = requests.post(
            "http://localhost:8000/api/meiyume-core/upload/",
            files=files,
            data=data,
            timeout=30
        )
        
        if response.status_code != 200:
            status_container.error(f"❌ Upload failed: {response.text}")
            return None
            
        upload_data = response.json()
        upload_id = upload_data.get("id")
        
        # Step 2: Processing
        status_container.info(steps[1][0])
        progress_bar.progress(steps[1][1])
        time.sleep(1)
        
        # Step 3: Workflow
        status_container.info(steps[2][0])
        progress_bar.progress(steps[2][1])
        time.sleep(1)
        
        # Step 4: AI Processing
        status_container.info(steps[3][0])
        progress_bar.progress(steps[3][1])
        
        # Poll for results
        max_attempts = 60
        for attempt in range(max_attempts):
            time.sleep(2)
            
            try:
                result_response = requests.get(
                    f"http://localhost:8000/api/meiyume-core/upload/{upload_id}/",
                    timeout=10
                )
                
                if result_response.status_code == 200:
                    result_data = result_response.json()
                    
                    if result_data.get("status") == "completed":
                        # Step 5: Complete
                        status_container.info(steps[4][0])
                        progress_bar.progress(steps[4][1])
                        time.sleep(0.5)
                        
                        status_container.success("✅ Analysis completed successfully!")
                        return result_data
                        
                    elif result_data.get("status") == "failed":
                        status_container.error("❌ Processing failed")
                        return None
                        
            except requests.RequestException:
                continue
        
        status_container.error("❌ Processing timeout")
        return None
        
    except Exception as e:
        status_container.error(f"❌ Error: {str(e)}")
        return None

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
        
        # Always show processing options
        st.subheader("🚀 Processing Options")
        
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
  
            
            with col_y:
                part_relationships = st.checkbox("🔗 Analyze Part Relationships", value=True)
            
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
            
            # Single analysis button when file is uploaded
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
                        "analyze_part_relationships": part_relationships,
                        "extract_material_specifications": material_analysis,
                        "detect_assembly_components": assembly_info,
                        "ai_model_version": "gemini-2.5-flash" if ai_model == "Gemini 2.5 Flash (Default)" else "gemini-pro",
                        "confidence_threshold": accuracy_level / 5.0,  # Convert 1-5 scale to 0.2-1.0
                        "max_analysis_time": 300
                    }
                }
                
                with st.spinner("Uploading file and starting analysis..."):
                    result = upload_file_with_progress(uploaded_file)
                    
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
                                        
                                        # Display results using the beautiful spreadsheet format
                                        if "results" in status_data:
                                            # Convert the Django results format to match our display function
                                            formatted_results = {
                                                "id": task_id,
                                                "original_filename": uploaded_file.name,
                                                "status": "completed",
                                                "progress_percentage": 100,
                                                "results": status_data["results"]
                                            }
                                            display_results_spreadsheet(formatted_results)
                                        else:
                                            st.info("Analysis completed but no detailed results available")
                                            # Show basic status info instead
                                            st.json(status_data)
                                        
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
        
        else:
            # Show prominent testing options when no file is uploaded
            st.info("👆 Upload a PDF file above to start analysis, or try the demo below!")
            


        
            if st.button("🧪 Try Demo Analysis", type="primary", use_container_width=True, help="See how the CAD analysis works with sample data"):
                run_demo_analysis()
            
        
    
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
    st.set_page_config(
        page_title="CAD Drawing Analysis Assistant",
        page_icon="🛠️",
        layout="wide"
    )
    
    st.title("🛠️ CAD Drawing Analysis Assistant")
    st.markdown("Upload CAD drawings (PDF) for dimensional analysis and part relationship detection.")
    
    # Main upload section
    uploaded_file = st.file_uploader(
        "📁 Choose a CAD drawing file (PDF)",
        type=['pdf'],
        help="Upload PDF files containing CAD drawings for analysis"
    )
    
    # Always show processing options - with and without file
    st.markdown("### 🚀 Processing Options")
    
    if uploaded_file is not None:
        st.success(f"✅ File selected: {uploaded_file.name}")
        st.info(f"📁 File size: {uploaded_file.size / 1024:.1f} KB")
        
        # Three columns when file is uploaded
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 Analyze CAD Drawing", type="primary", use_container_width=True):
                st.markdown("---")
                st.markdown("### 📤 Processing Real Upload...")
                
                result = upload_file_with_progress(uploaded_file)
                
                if result:
                    st.markdown("---")
                    st.markdown("### 📊 Analysis Results")
                    display_results_spreadsheet(result)
                    
        with col2:
            if st.button("🧪 Demo with This File", type="secondary", use_container_width=True, help="Show how results would look with this filename but demo data"):
                st.markdown("---")
                st.markdown("### 🧪 Processing Simulation...")
                
                # Run simulation with same interface as real upload
                results = simulate_workflow_processing()
                
                st.markdown("---")
                st.markdown("### 📊 Analysis Results")
                display_results_spreadsheet(results)
                
        with col3:
            if st.button("🧪 Test Interface", type="secondary", use_container_width=True, help="See how the interface works with realistic test data"):
                st.markdown("---")
                st.markdown("### 🧪 Running Demo Analysis...")
                
                # Run simulation
                results = simulate_workflow_processing()
                
                st.markdown("---")
                st.markdown("### 📊 Demo Analysis Results")
                display_results_spreadsheet(results)
    
    else:
        # Show testing option prominently when no file is uploaded
        st.info("👆 Upload a PDF file above, or try the demo below to see how the analysis works!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧪 Try Demo Analysis", type="primary", use_container_width=True, help="See how the interface works with realistic test data"):
                st.markdown("---")
                st.markdown("### 🧪 Running Demo Analysis...")
                
                # Run simulation
                results = simulate_workflow_processing()
                
                st.markdown("---")
                st.markdown("### 📊 Demo Analysis Results")
                display_results_spreadsheet(results)
        
        with col2:
            st.markdown("**Demo includes:**")
            st.markdown("- 📏 Dimension extraction")
            st.markdown("- 🔗 Part relationship analysis")
            st.markdown("- 📊 Interactive spreadsheet results")
            st.markdown("- 🎯 Realistic CAD data simulation")
    
    # Help section
    with st.expander("ℹ️ How to use this assistant"):
        st.markdown("""
        **Quick Start:**
        1. **Try Demo First**: Click "🧪 Test Interface with Simulation" to see how it works
        2. **Real Analysis**: Upload a PDF file and click "🚀 Analyze CAD Drawing"
        3. **Demo with Your File**: Upload a file and click "🧪 Demo with This File" to see results format
        
        **Features:**
        - 📏 Automatic dimension extraction from CAD drawings
        - 🔗 Part relationship analysis and fit compatibility
        - 📊 Interactive spreadsheet results with filtering
        - 📥 Export to CSV, JSON formats
        - 🎯 Beautiful visual summaries and metrics
        """)

if __name__ == "__main__":
    main()
