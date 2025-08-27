import streamlit as st
import requests
import json
import os
import time
import pandas as pd
from datetime import datetime, timezone
from io import BytesIO, StringIO
from dotenv import load_dotenv
from auth_utils import get_auth_headers
import uuid
import base64


load_dotenv()

# Configuration
DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://localhost:8000")

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
UPLOAD_ENDPOINT = f"{DJANGO_API_URL}/api/upload/"
RESULTS_ENDPOINT = f"{DJANGO_API_URL}/api/upload/"

def upload_file_to_django(file, session_id):
    """Upload file to Django backend which forwards to n8n webhook"""
    try:
        files = {"file": (file.name, file.getvalue(), file.type or "application/pdf")}
        data = {
            "session_id": session_id
        }
        response = requests.post(
            UPLOAD_ENDPOINT,
            files=files,
            data=data,
            timeout=60
        )
        if response.status_code in [200, 201]:
            return response.json()
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
        response = requests.get(
            f"{RESULTS_ENDPOINT}{task_id}/",
            timeout=15
        )
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None

def upload_file_with_progress(uploaded_file, session_id):
    """Upload file with progress and poll until results are available"""
    steps = [
        ("📤 Uploading file...", 0.20),
        ("📡 Sending to n8n workflow...", 0.40),
        ("⚙️ Processing...", 0.70),
        ("📊 Generating results...", 0.90),
        ("✅ Finalizing...", 1.0)
    ]
    progress_bar = st.progress(0)
    status_container = st.empty()
    try:
        status_container.info(steps[0][0])
        progress_bar.progress(steps[0][1])
        upload_resp = upload_file_to_django(uploaded_file, session_id)
        if not upload_resp:
            status_container.error("❌ Upload failed")
            return None
        task_id = upload_resp.get("task_id") or upload_resp.get("id")
        if not task_id:
            status_container.error("❌ No task id returned from server")
            return None
        status_container.info(steps[1][0])
        progress_bar.progress(steps[1][1])
        # Poll for results (up to 3 minutes)
        max_attempts = 90  # 90 * 2s = 180s (3 minutes)
        for attempt in range(max_attempts):
            time.sleep(2)
            result_data = get_processing_status(task_id)
            if not result_data:
                continue
            status = result_data.get("status", "processing")
            # surface backend status/message to help diagnose session matching
            if result_data.get("message"):
                status_container.info(result_data.get("message"))
            if status == "completed":
                # If backend provides a session_id, ensure it matches before finishing
                backend_session_id = result_data.get("session_id")
                if backend_session_id and backend_session_id != session_id:
                    status_container.info("Results received for a different session. Waiting for this session_id...")
                    continue
                status_container.info(steps[4][0])
                progress_bar.progress(steps[4][1])
                time.sleep(0.3)
                status_container.success("✅ Analysis completed successfully!")
                return {"task_id": task_id, **result_data}
            if status == "failed":
                status_container.error("❌ Processing failed")
                return None
            # update progress if provided
            progress = result_data.get("progress", 0)
            if isinstance(progress, (int, float)):
                progress_bar.progress(min(max(progress / 100.0, 0.0), 0.95))
            else:
                # show mid progress while waiting
                progress_bar.progress(min(steps[2][1] + attempt * 0.002, 0.95))
            status_container.info(f"⏳ Status: {status}")
        status_container.error("❌ No results received within 3 minutes. Please try again or check the workflow.")
        return None
    except Exception as e:
        status_container.error(f"❌ Error: {str(e)}")
        return None

def display_base64_results(results_list, expected_session_id=None):
    """Decode base64 CSV results and display as dataframes, filtering by session_id"""
    if not isinstance(results_list, list) or not results_list:
        st.info("No results to display")
        return
    # If expected_session_id provided, filter
    if expected_session_id:
        results_list = [r for r in results_list if isinstance(r, dict) and r.get('session_id') == expected_session_id]
        if not results_list:
            st.warning("Results received, waiting for this session_id")
            return
    result = results_list[0]
    dim_df = None
    match_df = None
    try:
        if isinstance(result.get('dimension'), str):
            dim_csv = base64.b64decode(result['dimension']).decode('utf-8')
            dim_df = pd.read_csv(StringIO(dim_csv))
    except Exception as e:
        st.error(f"Failed to decode dimension CSV: {e}")
    try:
        if isinstance(result.get('matching'), str):
            match_csv = base64.b64decode(result['matching']).decode('utf-8')
            match_df = pd.read_csv(StringIO(match_csv))
    except Exception as e:
        st.error(f"Failed to decode matching CSV: {e}")
    tabs = st.tabs(["📏 Dimensions (CSV)", "🔗 Matching (CSV)"])
    key_prefix = (expected_session_id or "default").replace("-", "_")
    with tabs[0]:
        if dim_df is not None:
            # Normalize column names
            dim_df = dim_df.copy()
            dim_df.columns = [str(c).replace('\ufeff', '').strip() for c in dim_df.columns]
            lower_cols = {c.lower(): c for c in dim_df.columns}
            # Map common names to standard
            rename_map = {}
            if 'part name' in lower_cols:
                rename_map[lower_cols['part name']] = 'part_name'
            if 'part_name' in lower_cols:
                rename_map[lower_cols['part_name']] = 'part_name'
            if 'dimension_type' in lower_cols:
                rename_map[lower_cols['dimension_type']] = 'dimension_type'
            if 'feature' in lower_cols:
                rename_map[lower_cols['feature']] = 'feature'
            if 'unit' in lower_cols:
                rename_map[lower_cols['unit']] = 'unit'
            if 'value' in lower_cols:
                rename_map[lower_cols['value']] = 'value'
            if 'tolerance' in lower_cols:
                rename_map[lower_cols['tolerance']] = 'tolerance'
            dim_df = dim_df.rename(columns=rename_map)
            # Ensure numeric value
            if 'value' in dim_df.columns:
                dim_df['value'] = pd.to_numeric(dim_df['value'], errors='coerce')

            with st.expander("Filters and sorting", expanded=False):
                cols = st.columns(3)
                with cols[0]:
                    parts = sorted([p for p in dim_df.get('part_name', pd.Series(dtype=str)).dropna().unique()]) if 'part_name' in dim_df.columns else []
                    selected_parts = st.multiselect("Filter by Part", parts, key=f"dim_parts_{key_prefix}")
                with cols[1]:
                    dim_types = sorted([t for t in dim_df.get('dimension_type', pd.Series(dtype=str)).dropna().unique()]) if 'dimension_type' in dim_df.columns else []
                    selected_types = st.multiselect("Dimension Type", dim_types, key=f"dim_types_{key_prefix}")
                with cols[2]:
                    feature_query = st.text_input("Feature contains", key=f"dim_feat_{key_prefix}")

                if 'value' in dim_df.columns and dim_df['value'].notna().any():
                    vmin = float(dim_df['value'].min())
                    vmax = float(dim_df['value'].max())
                    val_range = st.slider("Value range (mm)", min_value=vmin, max_value=vmax, value=(vmin, vmax), key=f"dim_val_{key_prefix}")
                else:
                    val_range = None

                sort_col = st.selectbox("Sort by", options=list(dim_df.columns), key=f"dim_sort_{key_prefix}")
                sort_asc = st.radio("Order", options=["Ascending", "Descending"], horizontal=True, key=f"dim_sort_order_{key_prefix}") == "Ascending"

            filtered = dim_df
            if selected_parts and 'part_name' in filtered.columns:
                filtered = filtered[filtered['part_name'].isin(selected_parts)]
            if selected_types and 'dimension_type' in filtered.columns:
                filtered = filtered[filtered['dimension_type'].isin(selected_types)]
            if feature_query and 'feature' in filtered.columns:
                filtered = filtered[filtered['feature'].astype(str).str.contains(feature_query, case=False, na=False)]
            if val_range and 'value' in filtered.columns:
                filtered = filtered[(filtered['value'] >= val_range[0]) & (filtered['value'] <= val_range[1])]

            if sort_col in filtered.columns:
                filtered = filtered.sort_values(by=sort_col, ascending=sort_asc, kind='mergesort')

            st.markdown(f"Showing {len(filtered)} of {len(dim_df)} rows")
            st.dataframe(filtered, use_container_width=True, hide_index=True)
        else:
            st.info("No dimension data available")
    with tabs[1]:
        if match_df is not None:
            # Normalize column names
            match_df = match_df.copy()
            match_df.columns = [str(c).replace('\ufeff', '').strip() for c in match_df.columns]
            lower_cols_m = {c.lower(): c for c in match_df.columns}
            rename_map_m = {}
            for key in ['dimension_type','part_a','feature_a','value_a','part_b','feature_b','value_b','difference_mm','range_difference_mm']:
                if key in lower_cols_m:
                    rename_map_m[lower_cols_m[key]] = key
            match_df = match_df.rename(columns=rename_map_m)
            # Ensure numeric types
            for col in ['value_a','value_b','difference_mm','range_difference_mm']:
                if col in match_df.columns:
                    match_df[col] = pd.to_numeric(match_df[col], errors='coerce')

            with st.expander("Filters, sorting, and tolerance check", expanded=False):
                cols = st.columns(3)
                with cols[0]:
                    m_types = sorted([t for t in match_df.get('dimension_type', pd.Series(dtype=str)).dropna().unique()]) if 'dimension_type' in match_df.columns else []
                    sel_m_types = st.multiselect("Dimension Type", m_types, key=f"match_types_{key_prefix}")
                with cols[1]:
                    parts_a = sorted([p for p in match_df.get('part_a', pd.Series(dtype=str)).dropna().unique()]) if 'part_a' in match_df.columns else []
                    sel_parts_a = st.multiselect("Part A", parts_a, key=f"match_part_a_{key_prefix}")
                with cols[2]:
                    parts_b = sorted([p for p in match_df.get('part_b', pd.Series(dtype=str)).dropna().unique()]) if 'part_b' in match_df.columns else []
                    sel_parts_b = st.multiselect("Part B", parts_b, key=f"match_part_b_{key_prefix}")

                feat_query = st.text_input("Feature contains (A or B)", key=f"match_feat_{key_prefix}")

                if 'difference_mm' in match_df.columns and match_df['difference_mm'].notna().any():
                    dmin = float(match_df['difference_mm'].min())
                    dmax = float(match_df['difference_mm'].max())
                    diff_range = st.slider("Difference range (mm)", min_value=dmin, max_value=dmax, value=(dmin, dmax), key=f"match_diff_{key_prefix}")
                else:
                    diff_range = None

                st.markdown("Tolerance check thresholds")
                colt1, colt2 = st.columns(2)
                with colt1:
                    tight_th = st.number_input("Tight fit ≤ (mm)", value=0.05, min_value=0.0, step=0.01, format="%.2f", key=f"tight_{key_prefix}")
                with colt2:
                    good_th = st.number_input("Good fit ≤ (mm)", value=0.20, min_value=0.0, step=0.01, format="%.2f", key=f"good_{key_prefix}")

                sort_m_col = st.selectbox("Sort by", options=list(match_df.columns), key=f"match_sort_{key_prefix}")
                sort_m_asc = st.radio("Order", options=["Ascending", "Descending"], horizontal=True, key=f"match_sort_order_{key_prefix}") == "Ascending"

            m_filtered = match_df
            if sel_m_types and 'dimension_type' in m_filtered.columns:
                m_filtered = m_filtered[m_filtered['dimension_type'].isin(sel_m_types)]
            if sel_parts_a and 'part_a' in m_filtered.columns:
                m_filtered = m_filtered[m_filtered['part_a'].isin(sel_parts_a)]
            if sel_parts_b and 'part_b' in m_filtered.columns:
                m_filtered = m_filtered[m_filtered['part_b'].isin(sel_parts_b)]
            if feat_query:
                cond_a = (
                    m_filtered['feature_a'].astype(str).str.contains(feat_query, case=False, na=False)
                    if 'feature_a' in m_filtered.columns
                    else pd.Series(False, index=m_filtered.index)
                )
                cond_b = (
                    m_filtered['feature_b'].astype(str).str.contains(feat_query, case=False, na=False)
                    if 'feature_b' in m_filtered.columns
                    else pd.Series(False, index=m_filtered.index)
                )
                m_filtered = m_filtered[cond_a | cond_b]
            if diff_range and 'difference_mm' in m_filtered.columns:
                m_filtered = m_filtered[(m_filtered['difference_mm'] >= diff_range[0]) & (m_filtered['difference_mm'] <= diff_range[1])]

            # Add fit status classification
            def classify_fit(diff: float) -> str:
                if pd.isna(diff):
                    return 'Unknown'
                if diff < 0:
                    return 'Overlap/Interference'
                if diff <= tight_th:
                    return 'Tight fit'
                if diff <= good_th:
                    return 'Good fit'
                return 'Loose fit'

            if 'difference_mm' in m_filtered.columns:
                m_filtered = m_filtered.copy()
                m_filtered['fit_status'] = m_filtered['difference_mm'].apply(classify_fit)

            if sort_m_col in m_filtered.columns:
                m_filtered = m_filtered.sort_values(by=sort_m_col, ascending=sort_m_asc, kind='mergesort')

            st.markdown(f"Showing {len(m_filtered)} of {len(match_df)} rows")
            st.dataframe(m_filtered, use_container_width=True, hide_index=True)
        else:
            st.info("No matching data available")

def engineering_assistant():
    """Engineering Assistant main interface"""
    st.title("⚙️ Engineering Assistant")
    st.markdown("### Advanced CAD Drawing Analysis with AI")
    st.caption(f"Backend API: {DJANGO_API_URL}")

    # Persist results across reruns so filters don't clear the tables
    if 'cad_results' not in st.session_state:
        st.session_state.cad_results = None
    if 'cad_session_id' not in st.session_state:
        st.session_state.cad_session_id = None
    
    
    
    # Main content (single column)
    col1 = st.container()
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
            
            # Minimal metadata defaults (optional fields removed per request)
            project_name = ""
            drawing_number = ""
            revision = ""
            priority = "Medium"
            notes = ""
            
            
            # Single analysis button when file is uploaded
            if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
                metadata = {
                    "project_name": project_name,
                    "drawing_number": drawing_number,
                    "revision": revision,
                    "priority": priority,
                    "notes": notes
                }
                
                with st.spinner("Uploading file and starting analysis..."):
                    # Generate a fresh session_id per upload and keep for matching
                    session_id = str(uuid.uuid4())
                    st.info(f"Tracking session: {session_id}")
                    result = upload_file_with_progress(uploaded_file, session_id)
                    if result:
                        st.success("File uploaded successfully!")
                        task_id = result.get("task_id") or result.get("id")
                        # Update history
                        st.session_state.upload_history.append({
                            "task_id": task_id,
                            "filename": uploaded_file.name,
                            "timestamp": time.time(),
                            "status": "completed" if result.get("status") == "completed" else result.get("status", "processing"),
                            "project_name": project_name,
                            "priority": priority
                        })
                        # Display results (base64 CSVs only)
                        results_list = result.get("results")
                        if result.get("status") == "completed" and isinstance(results_list, list):
                            # Save to session state so UI interactions don't clear the view
                            st.session_state.cad_results = results_list
                            st.session_state.cad_session_id = session_id
                        else:
                            st.info("Completed, but no base64 CSV results to display.")
                    else:
                        st.info("Analysis completed but no results available yet.")
        
        else:
            # Show message when no file is uploaded
            st.info("👆 Upload a PDF file above to start analysis!")
        
    # Always display last results if available (keeps tables visible during filter interactions)
    if st.session_state.cad_results:
        display_base64_results(st.session_state.cad_results, expected_session_id=st.session_state.cad_session_id)


    
