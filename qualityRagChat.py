import streamlit as st
import requests
from datetime import datetime

# Please fill in your n8n webhook URL for the RAG chat
N8N_WEBHOOK_URL = "https://meiyume.app.n8n.cloud/webhook/9c73c27e-0fd2-470f-9064-5d3e55ee08ef/chat"

def quality_rag_chat():
    """Quality RAG Chat Assistant main interface"""
    st.title("🤖 Quality RAG Chat Assistant")
    st.markdown("### AI-Powered Quality Control Chat Interface")

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'chat_id' not in st.session_state:
        st.session_state.chat_id = f"chat_{int(datetime.now().timestamp())}"

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is your question?"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            try:
                payload = {
                    "chatInput": prompt,
                    "sessionId": st.session_state.chat_id,
                }
                response = requests.post(
                    N8N_WEBHOOK_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                if response.status_code == 200:
                    result = response.json()
                    
                    # Try different possible field names for the response
                    ai_response = None
                    if "output" in result:
                        ai_response = result["output"]
                    elif "response" in result:
                        ai_response = result["response"]
                    elif "result" in result:
                        ai_response = result["result"]
                    elif "message" in result:
                        ai_response = result["message"]
                    elif "text" in result:
                        ai_response = result["text"]
                    else:
                        # If no standard field found, use the entire response as string
                        ai_response = str(result)
                    
                    full_response = ai_response if ai_response else "Sorry, I could not get a response."
                else:
                    full_response = f"Error: {response.status_code}"
            except Exception as e:
                full_response = f"An error occurred: {e}"
            
            message_placeholder.markdown(full_response)
            st.session_state.chat_history.append({"role": "assistant", "content": full_response})

def rag_file_management():
    """RAG File Management Interface"""
    st.title("📁 RAG File Management")
    st.markdown("### Manage documents for the Quality RAG Database")
    st.info("This is a placeholder for the RAG file management interface.")
