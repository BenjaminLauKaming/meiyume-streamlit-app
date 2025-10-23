import streamlit as st
import requests
import time
from datetime import datetime
import os
from dotenv import load_dotenv
import base64
import json as _json
import pandas as pd
from io import StringIO


load_dotenv()

# Prefer explicit COMPLIANCE_BACKEND_URL, else fall back to DJANGO_API_URL, else localhost
COMPLIANCE_BACKEND_URL = (
    os.getenv("COMPLIANCE_BACKEND_URL")
    or os.getenv("DJANGO_API_URL")
    or "http://localhost:8000"
)


def compliance_assistant():
    """Compliance Checker for MSDS upload and validation via n8n form."""
    st.title("🧪 Compliance Checker")
    st.markdown("### Upload MSDS (PDF) for compliance check")
    st.caption("The file will be securely sent to the compliance workflow.")

    if 'compliance_history' not in st.session_state:
        st.session_state.compliance_history = []
    if 'compliance_current' not in st.session_state:
        st.session_state.compliance_current = None

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Choose an MSDS PDF",
            type=['pdf'],
            help="Upload a Material Safety Data Sheet in PDF format"
        )

        if uploaded_file is not None:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            st.info(f"File size: {uploaded_file.size / 1024:.2f} KB")

            with st.expander("Optional details", expanded=False):
                product_name = st.text_input("Product name", value="")
                supplier_name = st.text_input("Supplier", value="")

            if st.button("🚀 Submit for Compliance Check", type="primary", use_container_width=True):
                submit_msds_to_n8n(uploaded_file, product_name, supplier_name)
                # Start polling for results if backend is configured
                poll_for_compliance_results(uploaded_file.name)

        if st.session_state.compliance_current:
            display_compliance_result(st.session_state.compliance_current)

    with col2:
        st.markdown("#### 📊 Submission History")
        display_compliance_history()


def submit_msds_to_n8n(uploaded_file, product_name: str, supplier_name: str) -> None:
    """Send the uploaded MSDS PDF to the provided n8n form endpoint."""
    workflow_url = "https://meiyume.app.n8n.cloud/form/e0c116b6-e2a6-4dac-8fe7-913da4296755"

    with st.spinner("Submitting MSDS to compliance workflow..."):
        try:
            files = {
                'pdfFile': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or 'application/pdf')
            }
            data = {
                'document_type': 'msds',
                'filename': uploaded_file.name,
                'product_name': product_name,
                'supplier_name': supplier_name,
                # If your n8n workflow posts back results, set this webhook to your backend
                'webhook_url': f"{COMPLIANCE_BACKEND_URL}/api/compliance/webhook/"
            }

            response = requests.post(workflow_url, files=files, data=data, timeout=30)

            if response.status_code == 200:
                st.success("✅ MSDS submitted successfully!")
                st.info("🔄 Processing... Results will appear when ready.")

                record = {
                    "timestamp": datetime.now(),
                    "filename": uploaded_file.name,
                    "file_size": uploaded_file.size,
                    "status": "submitted",
                    "results": {"message": "Submission successful. Awaiting processing."}
                }
                st.session_state.compliance_current = record
                st.session_state.compliance_history.append(record)
            else:
                st.error(f"❌ Submission failed: {response.status_code}")
                st.error(response.text)
        except requests.exceptions.Timeout:
            st.error("⏱️ Submission timed out. Please try again.")
        except requests.exceptions.RequestException as e:
            st.error(f"🔗 Network error: {str(e)}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")


def poll_for_compliance_results(filename: str) -> None:
    """Poll backend for latest compliance result, similar to ESG assistant."""
    max_attempts = 12
    attempt = 0
    status_placeholder = st.empty()

    while attempt < max_attempts:
        try:
            time.sleep(10)
            attempt += 1

            response = requests.get(f"{COMPLIANCE_BACKEND_URL}/api/compliance/latest/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    latest = data.get('data') or {}

                    completed_record = {
                        "timestamp": datetime.now(),
                        "filename": filename,
                        "file_size": st.session_state.compliance_current.get('file_size', 0) if st.session_state.compliance_current else 0,
                        "status": "completed",
                        "results": latest
                    }

                    st.session_state.compliance_current = completed_record
                    if (st.session_state.compliance_history and 
                        st.session_state.compliance_history[-1].get('status') == 'submitted'):
                        st.session_state.compliance_history[-1] = completed_record

                    status_placeholder.success("✅ Compliance analysis completed! Results are ready.")
                    st.rerun()
                    return

            status_placeholder.info(f"🔄 Still processing... (attempt {attempt}/{max_attempts})")

        except Exception as e:
            status_placeholder.warning(f"⚠️ Error checking results: {str(e)}")
            continue

    status_placeholder.warning("⏱️ Analysis is taking longer than expected. Results will appear when ready.")


def display_compliance_result(record):
    st.markdown("---")
    st.markdown("### 📄 Submission Status")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("File", record["filename"])
    with col2:
        st.metric("Status", record["status"].title())

    results = record.get("results")
    if not results:
        return

    if isinstance(results, dict):
        st.markdown("### ✅ Compliance Results")
        # High-level fields if present
        meta_cols = st.columns(3)
        with meta_cols[0]:
            st.write("**Filename**")
            st.write(results.get("filename") or record.get("filename") or "-")
        with meta_cols[1]:
            st.write("**Product**")
            st.write(results.get("product_name", "-"))
        with meta_cols[2]:
            st.write("**Supplier**")
            st.write(results.get("supplier_name", "-"))

        # Structured block from backend (parsed n8n answer)
        structured = results.get("structured") if isinstance(results.get("structured"), dict) else None
        if structured:
            st.markdown("#### Structured Data")
            st.json(structured)
        else:
            # Fallback: show full dict
            st.markdown("#### Raw Result")
            st.json(results)

        # Attempt to detect and decode base64 fields
        with st.expander("CSV Data", expanded=False):
            render_decoded_base64(results)

      
    else:
        st.write(str(results))


def render_decoded_base64(results: dict) -> None:
    """Detect base64 in common fields and render as JSON/CSV/text."""
    if not isinstance(results, dict):
        st.info("No decodable data")
        return

    # Look into top-level and full_payload for 'result' or 'answer'
    candidates = []
    for key in ["result", "answer"]:
        if key in results:
            candidates.append((key, results.get(key)))
    payload = results.get("full_payload") if isinstance(results.get("full_payload"), dict) else None
    if payload:
        for key in ["result", "answer"]:
            if key in payload:
                candidates.append((f"full_payload.{key}", payload.get(key)))

    if not candidates:
        st.info("No base64 fields detected in expected keys.")
        return

    any_decoded = False
    for label, value in candidates:
        if not isinstance(value, str):
            continue
        try:
            decoded_bytes = base64.b64decode(value, validate=True)
            decoded_text = decoded_bytes.decode("utf-8", errors="replace")
            any_decoded = True
            st.markdown(f"**Decoded `{label}`**")
            # Try JSON
            try:
                obj = _json.loads(decoded_text)
                st.json(obj)
                continue
            except Exception:
                pass
            # Try CSV
            try:
                df = pd.read_csv(StringIO(decoded_text))
                if not df.empty:
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    continue
            except Exception:
                pass
            # Fallback to text
            st.text_area("Text", decoded_text, height=200)
        except Exception:
            continue

    if not any_decoded:
        st.info("No decodable base64 content found.")


def display_compliance_history():
    if not st.session_state.compliance_history:
        st.info("No submissions yet")
        return
    recent = st.session_state.compliance_history[-5:]
    for i, rec in enumerate(reversed(recent)):
        with st.expander(f"📄 {rec['filename'][:24]}... - {rec['timestamp'].strftime('%H:%M')}"):
            st.write(f"**File:** {rec['filename']}")
            st.write(f"**Size:** {rec['file_size'] / 1024:.2f} KB")
            st.write(f"**Status:** {rec['status'].title()}")
            st.write(f"**Time:** {rec['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    compliance_assistant()


