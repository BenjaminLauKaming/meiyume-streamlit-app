import streamlit as st
import requests
import json
import os
import time
import pandas as pd
from datetime import datetime, timezone
from io import BytesIO, StringIO
from dotenv import load_dotenv
import uuid
import base64
from sqlalchemy import text

# Try to import MultipartEncoder, fallback to manual multipart if not available
try:
    from requests_toolbelt import MultipartEncoder
    HAS_MULTIPART_ENCODER = True
except ImportError:
    HAS_MULTIPART_ENCODER = False
    print("Warning: requests_toolbelt not available, using fallback multipart method")

load_dotenv()

# n8n workflow URL for CAD analysis - using webhook endpoint
N8N_CAD_WORKFLOW_URL = "https://meiyume.app.n8n.cloud/webhook/3c737ba6-d463-4e54-9cd4-addadca410b4"

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
            dim_df.columns = [str(c).replace('﻿', '').strip() for c in dim_df.columns]
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

            # Persist and edit selection via checkbox column
            sel_state_key = f"dim_selected_ids_{key_prefix}"
            if sel_state_key not in st.session_state:
                st.session_state[sel_state_key] = set()

            editable_df = filtered.copy()
            # Use original index as a stable row identifier across edits
            editable_df = editable_df.reset_index().rename(columns={"index": "row_id"})
            editable_df["selected"] = editable_df["row_id"].apply(lambda i: i in st.session_state[sel_state_key])

            # Use st.dataframe with custom checkboxes to avoid rerun issues
            st.markdown("**Select rows to export:**")
            
            # Add table headers for dimensions
            header_col1, header_col2, header_col3, header_col4, header_col5, header_col6, header_col7 = st.columns([0.5, 2, 1.5, 2, 0.8, 1, 1])
            with header_col1:
                st.markdown("**Select**")
            with header_col2:
                st.markdown("**Part Name**")
            with header_col3:
                st.markdown("**Dimension Type**")
            with header_col4:
                st.markdown("**Feature**")
            with header_col5:
                st.markdown("**Unit**")
            with header_col6:
                st.markdown("**Value**")
            with header_col7:
                st.markdown("**Tolerance**")
            
            # Display the table with checkboxes
            for idx, row in filtered.iterrows():
                col1, col2, col3, col4, col5, col6, col7 = st.columns([0.5, 2, 1.5, 2, 0.8, 1, 1])
                
                with col1:
                    checkbox_key = f"dim_checkbox_{key_prefix}_{idx}"
                    is_checked = st.checkbox("Select", value=idx in st.session_state[sel_state_key], key=checkbox_key, label_visibility="collapsed")
                    
                    if is_checked and idx not in st.session_state[sel_state_key]:
                        st.session_state[sel_state_key].add(idx)
                    elif not is_checked and idx in st.session_state[sel_state_key]:
                        st.session_state[sel_state_key].remove(idx)
                
                with col2:
                    st.write(row.get('part_name', ''))
                with col3:
                    st.write(row.get('dimension_type', ''))
                with col4:
                    st.write(row.get('feature', ''))
                with col5:
                    st.write(row.get('unit', ''))
                with col6:
                    st.write(row.get('value', ''))
                with col7:
                    st.write(row.get('tolerance', ''))

            # Prepare selected rows for export
            selected_ids = st.session_state[sel_state_key]
            if selected_ids:
                selected_rows = filtered.loc[filtered.index.isin(selected_ids)]
                st.success(f"{len(selected_rows)} row(s) selected")

                export_cols = list(selected_rows.columns)
                try:
                    xlsx_buffer = BytesIO()
                    with pd.ExcelWriter(xlsx_buffer, engine="openpyxl") as writer:
                        selected_rows.to_excel(writer, index=False, sheet_name="Dimensions")
                    xlsx_buffer.seek(0)
                    st.download_button(
                        label="⬇️ Export selected to Excel (XLSX)",
                        data=xlsx_buffer.getvalue(),
                        file_name="selected_dimensions.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"dim_export_xlsx_{key_prefix}"
                    )
                except Exception:
                    csv_buffer = BytesIO()
                    selected_rows.to_csv(csv_buffer, index=False)
                    csv_buffer.seek(0)
                    st.download_button(
                        label="⬇️ Export selected (CSV)",
                        data=csv_buffer.getvalue(),
                        file_name="selected_dimensions.csv",
                        mime="text/csv",
                        key=f"dim_export_csv_{key_prefix}"
                    )
        else:
            st.info("No dimension data available")
    with tabs[1]:
        if match_df is not None:
            # Normalize column names
            match_df = match_df.copy()
            match_df.columns = [str(c).replace('﻿', '').strip() for c in match_df.columns]
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

            # Persist and edit selection via checkbox column for matching table
            m_sel_state_key = f"match_selected_ids_{key_prefix}"
            if m_sel_state_key not in st.session_state:
                st.session_state[m_sel_state_key] = set()

            m_editable_df = m_filtered.copy()
            m_editable_df = m_editable_df.reset_index().rename(columns={"index": "row_id"})
            m_editable_df["selected"] = m_editable_df["row_id"].apply(lambda i: i in st.session_state[m_sel_state_key])

            # Use st.dataframe with custom checkboxes to avoid rerun issues
            st.markdown("**Select rows to export:**")
            
            # Add table headers for matching
            header_col1, header_col2, header_col3, header_col4, header_col5, header_col6, header_col7, header_col8, header_col9, header_col10, header_col11, header_col12 = st.columns([0.5, 1.2, 1.2, 1.5, 1, 1, 1.2, 1.5, 1, 1, 1, 1])
            with header_col1:
                st.markdown("**Select**")
            with header_col2:
                st.markdown("**Dimension Type**")
            with header_col3:
                st.markdown("**Part A**")
            with header_col4:
                st.markdown("**Feature A**")
            with header_col5:
                st.markdown("**Value A**")
            with header_col6:
                st.markdown("**Range A**")
            with header_col7:
                st.markdown("**Part B**")
            with header_col8:
                st.markdown("**Feature B**")
            with header_col9:
                st.markdown("**Value B**")
            with header_col10:
                st.markdown("**Range B**")
            with header_col11:
                st.markdown("**Difference (mm)**")
            with header_col12:
                st.markdown("**Range Diff (mm)**")
            
            # Display the table with checkboxes
            for idx, row in m_filtered.iterrows():
                col1, col2, col3, col4, col5, col6, col7, col8, col9, col10, col11, col12 = st.columns([0.5, 1.2, 1.2, 1.5, 1, 1, 1.2, 1.5, 1, 1, 1, 1])
                
                with col1:
                    checkbox_key = f"match_checkbox_{key_prefix}_{idx}"
                    is_checked = st.checkbox("Select", value=idx in st.session_state[m_sel_state_key], key=checkbox_key, label_visibility="collapsed")
                    
                    if is_checked and idx not in st.session_state[m_sel_state_key]:
                        st.session_state[m_sel_state_key].add(idx)
                    elif not is_checked and idx in st.session_state[m_sel_state_key]:
                        st.session_state[m_sel_state_key].remove(idx)
                
                with col2:
                    st.write(row.get('dimension_type', ''))
                with col3:
                    st.write(row.get('part_a', ''))
                with col4:
                    st.write(row.get('feature_a', ''))
                with col5:
                    st.write(row.get('value_a', ''))
                with col6:
                    st.write(row.get('range_a', ''))
                with col7:
                    st.write(row.get('part_b', ''))
                with col8:
                    st.write(row.get('feature_b', ''))
                with col9:
                    st.write(row.get('value_b', ''))
                with col10:
                    st.write(row.get('range_b', ''))
                with col11:
                    st.write(row.get('difference_mm', ''))
                with col12:
                    st.write(row.get('range_difference_mm', ''))

            m_selected_ids = st.session_state[m_sel_state_key]
            if m_selected_ids:
                m_selected_rows = m_filtered.loc[m_filtered.index.isin(m_selected_ids)]
                st.success(f"{len(m_selected_rows)} row(s) selected")

                try:
                    m_xlsx_buffer = BytesIO()
                    with pd.ExcelWriter(m_xlsx_buffer, engine="openpyxl") as writer:
                        m_selected_rows.to_excel(writer, index=False, sheet_name="Matching")
                    m_xlsx_buffer.seek(0)
                    st.download_button(
                        label="⬇️ Export selected to Excel (XLSX)",
                        data=m_xlsx_buffer.getvalue(),
                        file_name="selected_matching.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"match_export_xlsx_{key_prefix}"
                    )
                except Exception:
                    m_csv_buffer = BytesIO()
                    m_selected_rows.to_csv(m_csv_buffer, index=False)
                    m_csv_buffer.seek(0)
                    st.download_button(
                        label="⬇️ Export selected (CSV)",
                        data=m_csv_buffer.getvalue(),
                        file_name="selected_matching.csv",
                        mime="text/csv",
                        key=f"match_export_csv_{key_prefix}"
                    )
        else:
            st.info("No matching data available")

def engineering_assistant(db_engine):
    """Engineering Assistant main interface"""
    def submit_to_n8n_and_poll(uploaded_file, session_id):
        """Submit file to n8n and poll for results from database."""
        progress_bar = st.progress(0)
        status_container = st.empty()
        try:
            status_container.info("Submitting file to n8n workflow...")
            progress_bar.progress(0.2)
            
            # Get webhook URL - use ngrok URL if available, otherwise localhost
            webhook_url = os.getenv('WEBHOOK_URL', 'http://localhost:5001/webhook/cad')
            
            file_content = uploaded_file.getvalue()
            file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            # Use JSON approach like Django backend does for webhooks
            webhook_payload = {
                'data': file_base64,
                'session_id': session_id,
                'filename': uploaded_file.name,
                'webhook_url': webhook_url
            }
            
            # Debug logging
            print(f"DEBUG: Sending to n8n webhook - URL: {N8N_CAD_WORKFLOW_URL}")
            print(f"DEBUG: Payload keys: {list(webhook_payload.keys())}")
            print(f"DEBUG: File name: {uploaded_file.name}")
            print(f"DEBUG: Session ID: {session_id}")
            print(f"DEBUG: File size: {len(file_content)} bytes")
            print(f"DEBUG: Base64 size: {len(file_base64)} chars")
            
            response = requests.post(
                N8N_CAD_WORKFLOW_URL,
                json=webhook_payload,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Meiyume-AI-Assistant/1.0'
                },
                timeout=60
            )

            # Debug response
            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response text: {response.text[:200]}...")

            if response.status_code not in [200, 201]:
                st.error(f"n8n submission failed: {response.status_code} - {response.text}")
                return None

            status_container.info("File submitted. Awaiting results...")
            progress_bar.progress(0.5)
            
            result_data = poll_for_cad_results_from_db(db_engine, session_id)
            
            if result_data:
                status_container.success("Analysis completed!")
                progress_bar.progress(1.0)
                return result_data
            else:
                status_container.warning("Processing timed out or failed.")
                return None
                
        except Exception as e:
            status_container.error(f"An error occurred: {e}")
            return None

    def poll_for_cad_results_from_db(db_engine, session_id):
        """Polls the database for results from n8n webhook."""
        max_attempts = 180  # Poll for 3 minutes (90 * 2s)
        
        for attempt in range(max_attempts):
            time.sleep(2)
            try:
                # Query the database for results
                query = text("""
                    SELECT data FROM results 
                    WHERE session_id = :session_id AND agent_type = 'cad'
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
                
                with db_engine.connect() as connection:
                    result = connection.execute(query, {"session_id": session_id})
                    row = result.fetchone()
                    
                    if row:
                        # The data is already a dict, not a JSON string
                        db_data = row[0]  # row[0] is already the dict
                        
                        # Convert database format to display format
                        # Database has: {"dimension": "base64_csv", "matching": "base64_csv", "session_id": "uuid"}
                        # Display expects: [{"dimension": "base64_csv", "matching": "base64_csv", "session_id": "uuid"}]
                        
                        results_list = [db_data]  # Wrap in list for display_base64_results
                        return {
                            "status": "completed",
                            "results": results_list
                        }
                        
            except Exception as e:
                print(f"Database query error: {e}")
                continue
                
        return None        
    st.title("⚙️ Engineering Assistant")
    st.markdown("### Advanced CAD Drawing Analysis with AI")


    # Persist results across reruns so filters don't clear the tables
    if 'cad_results' not in st.session_state:
        st.session_state.cad_results = None
    if 'cad_session_id' not in st.session_state:
        st.session_state.cad_session_id = None
    
    # Test button to simulate results with existing session ID
    if st.button("🧪 Test with Existing Session ID", type="secondary"):
        test_session_id = "8f0101e0-aa1f-4f95-81a9-52a629b92f03"
        st.info(f"Testing with session ID: {test_session_id}")
        
        # Query the database for this specific session
        try:
            query = text("""
                SELECT data FROM results 
                WHERE session_id = :session_id AND agent_type = 'cad'
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            
            with db_engine.connect() as connection:
                result = connection.execute(query, {"session_id": test_session_id})
                row = result.fetchone()
                
                if row:
                    # The data is already a dict, not a JSON string
                    db_data = row[0]  # row[0] is already the dict
                    
                    # Convert database format to display format
                    results_list = [db_data]  # Wrap in list for display_base64_results
                    
                    # Save to session state
                    st.session_state.cad_results = results_list
                    st.session_state.cad_session_id = test_session_id
                    
                    st.success("✅ Test data loaded successfully!")
                    st.rerun()
                else:
                    st.error("❌ No data found for that session ID")
                    
        except Exception as e:
            st.error(f"❌ Error loading test data: {e}")
    
    
    
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
                    result = submit_to_n8n_and_poll(uploaded_file, session_id)
                    if result:
                        st.success("File uploaded successfully!")
                        task_id = result.get("task_id") or result.get("id")
                        # Update history
                        if 'upload_history' not in st.session_state:
                            st.session_state.upload_history = []
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
