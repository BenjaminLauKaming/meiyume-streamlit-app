import streamlit as st
import requests
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv

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
    st.info("💡 Ask questions about quality control, testing protocols, standards, and best practices. The AI will provide detailed answers based on quality control knowledge.")
    
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
        st.subheader("💬 Chat Controls")
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.chat_id = f"chat_{int(time.time())}"
            st.rerun()
        
        # Export chat button
        if st.button("📥 Export Chat", use_container_width=True):
            if st.session_state.chat_history:
                # Serialize chat history for export
                messages_serialized = []
                for msg in st.session_state.chat_history:
                    msg_copy = msg.copy()
                    if 'timestamp' in msg_copy and isinstance(msg_copy['timestamp'], datetime):
                        msg_copy['timestamp'] = msg_copy['timestamp'].isoformat()
                    messages_serialized.append(msg_copy)
                
                chat_export = {
                    "chat_id": st.session_state.chat_id,
                    "timestamp": datetime.now().isoformat(),
                    "messages": messages_serialized
                }
                st.download_button(
                    label="📥 Download Chat JSON",
                    data=json.dumps(chat_export, indent=2, default=serialize_datetime),
                    file_name=f"quality_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        st.markdown("---")
        

        
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
        
       
    

if __name__ == "__main__":
    quality_rag_chat() 