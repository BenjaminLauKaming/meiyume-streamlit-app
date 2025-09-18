import streamlit as st
import requests
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import uuid

def serialize_datetime(obj):
    """Helper function to serialize datetime objects for JSON"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

load_dotenv()

# Configuration
DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://localhost:8000")
N8N_WEBHOOK_URL = "https://meiyume.app.n8n.cloud/webhook/9c73c27e-0fd2-470f-9064-5d3e55ee08ef/chat"

# Debug mode - set to True to show debug information (set to False for production)
DEBUG_MODE = False  # Set to True if you need to debug response structure

def quality_rag_chat():
    """Quality RAG Chat Assistant main interface"""
    st.title("🤖 Quality RAG Chat Assistant")
    st.markdown("### AI-Powered Quality Control Chat Interface")
    
    # Initialize chat history in session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'chat_id' not in st.session_state:
        st.session_state.chat_id = f"chat_{int(time.time())}"
    
    # Initialize suggested question in session state
    if 'suggested_question' not in st.session_state:
        st.session_state.suggested_question = ""
    
    # Quick info banner
    st.info("💡 Ask questions about complaints. The AI will provide detailed answers based on complaints data.")
    
    # Chat interface
    st.markdown("---")
    
    # Display chat history
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
            elif message["role"] == "assistant":
                with st.chat_message("assistant"):
                    st.write(message["content"])
                    if "metadata" in message and message["metadata"]:
                        with st.expander("📊 Response Details"):
                            st.json(message["metadata"])
    
    # Chat input with suggested question support
    chat_input_key = f"chat_input_{st.session_state.chat_id}"
    

    
    # Use regular chat_input for better chat experience
    prompt = st.chat_input(
        "Ask about quality control, testing protocols, standards...",
        key=chat_input_key
    )
    
    if prompt:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt, "timestamp": datetime.now()})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("🤖 AI is thinking..."):
                try:
                    # Prepare the request to n8n webhook
                    # Serialize chat history to handle datetime objects
                    chat_history_serialized = []
                    for msg in st.session_state.chat_history[-5:]:  # Last 5 messages for context
                        msg_copy = msg.copy()
                        if 'timestamp' in msg_copy and isinstance(msg_copy['timestamp'], datetime):
                            msg_copy['timestamp'] = msg_copy['timestamp'].isoformat()
                        chat_history_serialized.append(msg_copy)
                    
                    payload = {
                        "chatInput": prompt,  # Standardized field name for n8n
                        "sessionId": st.session_state.chat_id,  # Standardized field name for n8n
                        "message": prompt,  # Keep for backward compatibility
                        "chat_id": st.session_state.chat_id,  # Keep for backward compatibility
                        "user_id": st.session_state.user_info.get('username', 'anonymous'),
                        "timestamp": datetime.now().isoformat(),
                        "session_data": {
                            "chat_history": chat_history_serialized,
                            "user_preferences": st.session_state.user_info
                        }
                    }
                    
                    # Send request to n8n webhook
                    response = requests.post(
                        N8N_WEBHOOK_URL,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        try:
                            result = response.json()
                            
                            # Try different possible field names for the response
                            ai_response = None
                            if "response" in result:
                                ai_response = result["response"]
                            elif "message" in result:
                                ai_response = result["message"]
                            elif "content" in result:
                                ai_response = result["content"]
                            elif "text" in result:
                                ai_response = result["text"]
                            elif "answer" in result:
                                ai_response = result["answer"]
                            elif "output" in result:
                                ai_response = result["output"]
                            elif "result" in result:
                                ai_response = result["result"]
                            else:
                                # If no standard field found, use the entire response as string
                                ai_response = str(result)
                            
                            metadata = result.get("metadata", {})
                            
                            # Add assistant response to chat history
                            st.session_state.chat_history.append({
                                "role": "assistant", 
                                "content": ai_response, 
                                "timestamp": datetime.now(),
                                "metadata": metadata
                            })
                            
                            # Display the AI response cleanly
                            st.write(ai_response)
                            
                            # Show metadata if available
                            if metadata:
                                with st.expander("📊 Response Details"):
                                    st.json(metadata)
                                    
                        except json.JSONDecodeError:
                            # Handle plain text response
                            ai_response = response.text
                            st.session_state.chat_history.append({
                                "role": "assistant", 
                                "content": ai_response, 
                                "timestamp": datetime.now()
                            })
                            st.write(ai_response)
                            
                    else:
                        error_msg = f"Error: Unable to get response (Status: {response.status_code})"
                        st.error(error_msg)
                        st.session_state.chat_history.append({
                            "role": "assistant", 
                            "content": error_msg, 
                            "timestamp": datetime.now()
                        })
                        
                except requests.exceptions.RequestException as e:
                    error_msg = f"Connection error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": error_msg, 
                        "timestamp": datetime.now()
                    })
    
    # Sidebar with chat controls and information
    with st.sidebar:
    
        
        # Suggested questions
        st.subheader("💡 Suggested Questions")
        st.info("Click any question below to load it into the input field for editing:")
        suggested_questions = [
            "How many complaints did we get from LVMH?",
            "Do we have any complaints about Retail solutions products?",
            "Can you list the root cause of all the complaints we had from Chanel?",
            "Have we had a contamination issue before?",
            "Can you list out the name of the factories and how many complaints we received with each of them?",
            "Who was the responsible quality person for the PO number 4520016450?",
            "What are our top 5 quality complaints ranked by order quantity?"
        ]
        
        for question in suggested_questions:
            if st.button(question, key=f"suggest_{question[:20]}", use_container_width=True):
                st.session_state.suggested_question = question
                st.rerun()
        
       
    

def create_sample_files():
    """Create sample files for demonstration"""
    sample_files = [
        {
            "id": "sample_1",
            "name": "LVMH_Complaint_Report_2024.pdf",
            "type": "Complaint Record",
            "priority": "High",
            "category": "Customer Complaints",
            "tags": ["LVMH", "urgent", "contamination", "retail"],
            "description": "Complaint report from LVMH regarding product contamination issues in retail stores. Contains detailed investigation findings and corrective actions.",
            "size": 2457600,
            "upload_date": "2024-01-15 14:30:22",
            "status": "Processed",
            "file_content": b"Sample PDF content for LVMH complaint report"
        },
        {
            "id": "sample_2", 
            "name": "Chanel_Quality_Audit_Report.docx",
            "type": "Detail Report",
            "priority": "High",
            "category": "Quality Audit",
            "tags": ["Chanel", "audit", "quality", "factory"],
            "description": "Comprehensive quality audit report for Chanel production facilities. Includes inspection results, compliance findings, and improvement recommendations.",
            "size": 1894400,
            "upload_date": "2024-01-14 09:15:45",
            "status": "Processed",
            "file_content": b"Sample DOCX content for Chanel audit report"
        },
        {
            "id": "sample_3",
            "name": "Contamination_Incident_Log.csv",
            "type": "Complaint Record", 
            "priority": "High",
            "category": "Incident Reports",
            "tags": ["contamination", "incident", "urgent", "safety"],
            "description": "Detailed log of contamination incidents across multiple production facilities. Includes root cause analysis and preventive measures.",
            "size": 512000,
            "upload_date": "2024-01-13 16:45:12",
            "status": "Processed",
            "file_content": b"Date,Facility,Product,Issue,Severity,Action\n2024-01-10,Factory A,Product X,Contamination,High,Immediate Recall\n2024-01-12,Factory B,Product Y,Contamination,Medium,Investigation"
        },
        {
            "id": "sample_4",
            "name": "Retail_Solutions_Complaints.txt",
            "type": "Complaint Record",
            "priority": "Medium", 
            "category": "Retail Complaints",
            "tags": ["retail", "solutions", "customer", "feedback"],
            "description": "Collection of customer complaints related to retail solutions products. Contains feedback analysis and improvement suggestions.",
            "size": 128000,
            "upload_date": "2024-01-12 11:20:33",
            "status": "Processed",
            "file_content": b"Customer Complaint Summary:\n- Product packaging issues\n- Delivery delays\n- Quality inconsistencies\n- Customer service feedback"
        },
        {
            "id": "sample_5",
            "name": "Factory_Compliance_Report.pdf",
            "type": "Detail Report",
            "priority": "Medium",
            "category": "Compliance",
            "tags": ["compliance", "factory", "standards", "regulations"],
            "description": "Annual compliance report for all production facilities. Documents adherence to quality standards and regulatory requirements.",
            "size": 3072000,
            "upload_date": "2024-01-11 13:55:18",
            "status": "Processed", 
            "file_content": b"Sample PDF content for factory compliance report"
        },
        {
            "id": "sample_6",
            "name": "PO_4520016450_Quality_Report.docx",
            "type": "Detail Report",
            "priority": "Low",
            "category": "Purchase Orders",
            "tags": ["PO", "4520016450", "quality", "inspection"],
            "description": "Quality inspection report for Purchase Order 4520016450. Details inspection results, responsible quality personnel, and approval status.",
            "size": 1024000,
            "upload_date": "2024-01-10 08:30:45",
            "status": "Processed",
            "file_content": b"Sample DOCX content for PO quality report"
        },
        {
            "id": "sample_7",
            "name": "Top_Complaints_Analysis.csv",
            "type": "Detail Report",
            "priority": "Medium",
            "category": "Analytics",
            "tags": ["analysis", "top", "complaints", "ranking"],
            "description": "Analysis of top 5 quality complaints ranked by order quantity. Includes trend analysis and recommendations for improvement.",
            "size": 256000,
            "upload_date": "2024-01-09 15:10:27",
            "status": "Processing",
            "file_content": b"Rank,Complaint_Type,Order_Quantity,Percentage,Trend\n1,Contamination,1250,35%,Increasing\n2,Packaging Issues,890,25%,Stable\n3,Delivery Delays,650,18%,Decreasing"
        },
        {
            "id": "sample_8",
            "name": "Quality_Standards_Handbook.pdf",
            "type": "Detail Report",
            "priority": "Low",
            "category": "Standards",
            "tags": ["standards", "handbook", "guidelines", "reference"],
            "description": "Comprehensive quality standards handbook for all production processes. Contains guidelines, procedures, and best practices.",
            "size": 5120000,
            "upload_date": "2024-01-08 10:45:12",
            "status": "Processed",
            "file_content": b"Sample PDF content for quality standards handbook"
        }
    ]
    return sample_files

def rag_file_management():
    """RAG File Management Interface"""
    st.title("📁 RAG File Management")
    st.markdown("### Manage documents for the Quality RAG Database")
    
    # Initialize file storage in session state
    if 'rag_files' not in st.session_state:
        st.session_state.rag_files = []
    
    # Add sample data button
    if not st.session_state.rag_files:
        if st.button("🎭 Load Sample Files", type="primary", use_container_width=True):
            st.session_state.rag_files = create_sample_files()
            st.success("✅ Sample files loaded! You can now explore the file management features.")
            st.rerun()
    
    # Create tabs for different functionalities
    tab1, tab2 = st.tabs(["📤 Upload Documents", "📋 File Management"])
    
    with tab1:
        st.markdown("## 📤 Upload Documents")
        st.info("Upload documents to enhance the RAG knowledge base. Supported file types: PDF, DOCX, TXT, CSV")
        
        # File type selection
        col1, col2 = st.columns(2)
        
        with col1:
            file_type = st.selectbox(
                "📂 Document Type",
                ["Complaint Record", "Detail Report"],
                help="Select the type of document you're uploading"
            )
        
        with col2:
            priority = st.selectbox(
                "⭐ Priority Level",
                ["High", "Medium", "Low"],
                index=1,
                help="Set the priority level for this document"
            )
        
        # File upload
        uploaded_files = st.file_uploader(
            "Choose files to upload",
            type=['pdf', 'docx', 'txt', 'csv'],
            accept_multiple_files=True,
            help="Select one or more files to upload to the RAG database"
        )
        
        # Additional metadata
        col1, col2 = st.columns(2)
        with col1:
            category = st.text_input(
                "📋 Category",
                placeholder="e.g., Quality Control, Manufacturing, Customer Service",
                help="Categorize the document for better organization"
            )
        
        with col2:
            tags = st.text_input(
                "🏷️ Tags",
                placeholder="e.g., urgent, LVMH, contamination",
                help="Add comma-separated tags for better searchability"
            )
        
        description = st.text_area(
            "📝 Description",
            placeholder="Brief description of the document content...",
            help="Provide a brief description of the document"
        )
        
        # Upload button
        if st.button("📤 Upload Documents", type="primary", use_container_width=True):
            if uploaded_files:
                success_count = 0
                for uploaded_file in uploaded_files:
                    # Create file record
                    file_record = {
                        "id": str(uuid.uuid4()),
                        "name": uploaded_file.name,
                        "type": file_type,
                        "priority": priority,
                        "category": category if category else "Uncategorized",
                        "tags": [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else [],
                        "description": description,
                        "size": uploaded_file.size,
                        "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "Processing",
                        "file_content": uploaded_file.read()  # In real app, this would be stored properly
                    }
                    
                    # Add to session state (in real app, this would be sent to backend)
                    st.session_state.rag_files.append(file_record)
                    success_count += 1
                
                st.success(f"✅ Successfully uploaded {success_count} file(s)!")
                st.balloons()
                
                # Show uploaded files summary
                st.markdown("### 📋 Upload Summary")
                for file_record in st.session_state.rag_files[-success_count:]:
                    with st.expander(f"📄 {file_record['name']}"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Type:** {file_record['type']}")
                            st.write(f"**Priority:** {file_record['priority']}")
                        with col2:
                            st.write(f"**Category:** {file_record['category']}")
                            st.write(f"**Size:** {file_record['size']} bytes")
                        with col3:
                            st.write(f"**Upload Date:** {file_record['upload_date']}")
                            st.write(f"**Status:** {file_record['status']}")
                        
                        if file_record['tags']:
                            st.write(f"**Tags:** {', '.join(file_record['tags'])}")
                        if file_record['description']:
                            st.write(f"**Description:** {file_record['description']}")
            else:
                st.error("❌ Please select at least one file to upload.")
    
    with tab2:
        st.markdown("## 📋 File Management")
        
        if not st.session_state.rag_files:
            st.info("📂 No files uploaded yet. Go to the Upload Documents tab to add files.")
            return
        
        # Filter and search options
        col1, col2 = st.columns(2)
        
        with col1:
            type_filter = st.selectbox(
                "Filter by Type",
                ["All", "Complaint Record", "Detail Report"],
                help="Filter files by document type"
            )
        
        
        with col2:
            search_term = st.text_input(
                "🔍 Search",
                placeholder="Search by name, category, or tags...",
                help="Search files by name, category, or tags"
            )
        
        # Apply filters
        filtered_files = st.session_state.rag_files.copy()
        
        if type_filter != "All":
            filtered_files = [f for f in filtered_files if f['type'] == type_filter]
        
        
        if search_term:
            search_term_lower = search_term.lower()
            filtered_files = [f for f in filtered_files if 
                            search_term_lower in f['name'].lower() or 
                            search_term_lower in f['category'].lower() or 
                            any(search_term_lower in tag.lower() for tag in f['tags'])]
        
        # Display statistics
        st.markdown("### 📊 File Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Files", len(st.session_state.rag_files))
        
        with col2:
            complaint_count = len([f for f in st.session_state.rag_files if f['type'] == 'Complaint Record'])
            st.metric("Complaint Records", complaint_count)
        
        with col3:
            report_count = len([f for f in st.session_state.rag_files if f['type'] == 'Detail Report'])
            st.metric("Detail Reports", report_count)
        
        with col4:
            high_priority_count = len([f for f in st.session_state.rag_files if f['priority'] == 'High'])
            st.metric("High Priority", high_priority_count)
        
        st.markdown("---")
        
        # Display files
        if filtered_files:
            st.markdown(f"### 📄 Files ({len(filtered_files)} found)")

            # File list
            for i, file_record in enumerate(filtered_files):
                with st.expander(f"📄 {file_record['name']} ({file_record['type']})", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # File information
                        info_col1, info_col2 = st.columns(2)
                        
                        with info_col1:
                            st.write(f"**📂 Type:** {file_record['type']}")
   

                        
                        with info_col2:
                            st.write(f"**📅 Upload Date:** {file_record['upload_date']}")

  
                        
                        if file_record['description']:
                            st.write(f"**📝 Description:** {file_record['description']}")
                    
                    with col2:
                        # Action buttons
                        st.markdown("**Actions:**")
                        
                        if st.button("👁️ View", key=f"view_{file_record['id']}", use_container_width=True):
                            st.session_state.selected_file_id = file_record['id']
                            st.session_state.show_file_viewer = True
                        

                        
                        if st.button("🗑️ Delete", key=f"delete_{file_record['id']}", type="secondary", use_container_width=True):
                            if st.button(f"⚠️ Confirm Delete", key=f"confirm_delete_{file_record['id']}", type="secondary"):
                                st.session_state.rag_files = [f for f in st.session_state.rag_files if f['id'] != file_record['id']]
                                st.success(f"✅ Deleted {file_record['name']}")
                                st.rerun()
        else:
            st.info("📂 No files match the current filters.")
        
        # File viewer modal
        if st.session_state.get('show_file_viewer', False):
            selected_file = next((f for f in st.session_state.rag_files if f['id'] == st.session_state.selected_file_id), None)
            if selected_file:
                st.markdown("---")
                st.markdown(f"## 👁️ Viewing: {selected_file['name']}")
                
                # File details
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Type:** {selected_file['type']}")
 
                
                with col2:
                    st.write(f"**Upload Date:** {selected_file['upload_date']}")
                
                
                if selected_file['description']:
                    st.write(f"**Description:** {selected_file['description']}")
                
                # File content preview
                st.markdown("### 📄 Content Preview")
                if selected_file['name'].lower().endswith(('.txt', '.csv')):
                    try:
                        content = selected_file['file_content'].decode('utf-8')
                        st.text_area("File Content", content, height=300, disabled=True)
                    except:
                        st.warning("⚠️ Unable to display file content as text")
                else:
                    st.info("📄 Binary file - content preview not available")
                
                if st.button("❌ Close Viewer"):
                    st.session_state.show_file_viewer = False
                    st.rerun()

if __name__ == "__main__":
    quality_rag_chat() 