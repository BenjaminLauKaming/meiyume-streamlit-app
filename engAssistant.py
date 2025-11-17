import streamlit as st
import requests
import time
import pandas as pd
from io import BytesIO, StringIO
from dotenv import load_dotenv
import uuid
import base64
from sqlalchemy import text
from pypdf import PdfReader, PdfWriter

load_dotenv()

# n8n workflow URL for CAD analysis - using webhook endpoint
N8N_CAD_WORKFLOW_URL = "https://meiyume.app.n8n.cloud/webhook/dcd53389-3d85-469d-840e-35ecae130592"

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
    def submit_to_n8n_and_poll(uploaded_file, session_id, db_engine):
        """Submit file to n8n and poll for results from database."""
        progress_bar = st.progress(0)
        status_container = st.empty()
        try:
            status_container.info("Processing PDF and splitting pages...")
            progress_bar.progress(0.1)
            
            file_content = uploaded_file.getvalue()
            file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            # Split PDF into individual pages
            status_container.info("Splitting PDF into pages...")
            progress_bar.progress(0.15)
            
            pdf_reader = PdfReader(BytesIO(file_content))
            total_pages = len(pdf_reader.pages)
            
            pages_data = []
            for page_num in range(total_pages):
                # Create a new PDF with just this page
                pdf_writer = PdfWriter()
                pdf_writer.add_page(pdf_reader.pages[page_num])
                
                # Write single page to bytes
                page_buffer = BytesIO()
                pdf_writer.write(page_buffer)
                page_buffer.seek(0)
                page_bytes = page_buffer.read()
                
                # Encode page to base64
                page_base64 = base64.b64encode(page_bytes).decode('utf-8')
                pages_data.append({
                    'page_number': page_num + 1,
                    'data': page_base64,
                    'filename': f"page_{page_num + 1}_{uploaded_file.name}"
                })
            
            status_container.info("Submitting full document and pages to n8n workflow...")
            progress_bar.progress(0.2)
            
            # Prepare payload for n8n workflow - include full document and pages
            webhook_payload = {
                'full_document': {
                    'data': file_base64,
                    'filename': uploaded_file.name,
                    'page_count': total_pages
                },
                'pages': pages_data,
                'session_id': session_id
            }
            
            # Debug logging
            print(f"DEBUG: Sending to n8n webhook - URL: {N8N_CAD_WORKFLOW_URL}")
            print(f"DEBUG: Payload keys: {list(webhook_payload.keys())}")
            print(f"DEBUG: File name: {uploaded_file.name}")
            print(f"DEBUG: Total pages: {total_pages}")
            print(f"DEBUG: Session ID: {session_id}")
            print(f"DEBUG: Full document size: {len(file_content)} bytes")
            print(f"DEBUG: Number of pages to send: {len(pages_data)}")
            
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
            
            result_data = poll_for_cad_results_from_db(session_id, db_engine)
            
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

    def poll_for_cad_results_from_db(session_id, db_engine):
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
                        
                        # Handle nested data structure from n8n
                        # n8n stores data as: {"data": {"data": [{"dimension": "...", "matching": "..."}]}}
                        # We need to extract the actual data from the nested structure
                        if isinstance(db_data, dict) and "data" in db_data:
                            # Check if data.data is a list
                            if isinstance(db_data.get("data"), dict) and isinstance(db_data["data"].get("data"), list):
                                # Extract the actual data from n8n's nested structure
                                actual_data = db_data["data"]["data"][0]  # Get first item from the data array
                                results_list = [actual_data]
                            elif isinstance(db_data.get("data"), list):
                                # Data is already in correct format
                                results_list = db_data["data"]
                            else:
                                results_list = [db_data]
                        else:
                            # No nesting, use data as-is
                            results_list = [db_data]
                        
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
    if 'cad_current' not in st.session_state:
        st.session_state.cad_current = None
    
    # Test button to simulate results with existing session ID
    if st.button("🧪 Test with Existing Session ID", type="secondary"):
        test_session_id = "a363060a-fc8a-4264-b8d3-9c78531b5793"
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
                    
                    # Handle nested data structure from n8n (same as poll function)
                    if isinstance(db_data, dict) and "data" in db_data:
                        if isinstance(db_data.get("data"), dict) and isinstance(db_data["data"].get("data"), list):
                            actual_data = db_data["data"]["data"][0]
                            results_list = [actual_data]
                        elif isinstance(db_data.get("data"), list):
                            results_list = db_data["data"]
                        else:
                            results_list = [db_data]
                    else:
                        results_list = [db_data]
                    
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
            
            # Single analysis button when file is uploaded
            if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
                # Generate a fresh session_id per upload and keep for matching
                session_id = str(uuid.uuid4())
                
                # Save to session state
                st.session_state.cad_current = {
                    "filename": uploaded_file.name,
                    "status": "processing",
                    "session_id": session_id
                }
                
                result = submit_to_n8n_and_poll(uploaded_file, session_id, db_engine)
                
                if result:
                    results_list = result.get("results")
                    if isinstance(results_list, list):
                        st.session_state.cad_results = results_list
                        st.session_state.cad_session_id = session_id
                        st.session_state.cad_current['status'] = 'completed'
                        st.session_state.cad_current['results'] = results_list
        
        else:
            # Show message when no file is uploaded
            st.info("👆 Upload a PDF file above to start analysis!")
        
    # Display submission status if available
    if st.session_state.cad_current:
        st.markdown("---")
        st.markdown("### 📄 Submission Status")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("File", st.session_state.cad_current["filename"])
        with col2:
            st.metric("Status", st.session_state.cad_current["status"].title())
    
    # Always display last results if available (keeps tables visible during filter interactions)
    if st.session_state.cad_results:
        display_base64_results(st.session_state.cad_results, expected_session_id=st.session_state.cad_session_id)
