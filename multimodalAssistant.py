import streamlit as st
import os
import requests
import time
import base64
from typing import List, Dict

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from supabase import create_client, Client

CATEGORIES = ["Stones", "Aluminium and Anodizing", "Electroplating", "Plastics"]

def get_env_vars():
    """Retrieve environment variables specifically for this agent."""
    load_dotenv(override=True)
    vars = {
        "supabase_url": os.environ.get("MULTIMODAL_SUPABASE_URL"),
        "supabase_key": os.environ.get("MULTIMODAL_SUPABASE_KEY"),
        "supabase_bucket": os.environ.get("MULTIMODAL_SUPABASE_BUCKET"),
        "mistral_api_key": os.environ.get("MULTIMODAL_MISTRAL_API_KEY"),
        "openai_api_key": os.environ.get("MULTIMODAL_OPENAI_API_KEY"),
    }
    return vars

def init_supabase() -> Client:
    env = get_env_vars()
    if not env["supabase_url"] or not env["supabase_key"]:
        st.error("Missing Supabase credentials in .env (MULTIMODAL_SUPABASE_URL or MULTIMODAL_SUPABASE_KEY)")
        st.stop()
    return create_client(env["supabase_url"], env["supabase_key"])

def mistral_upload_file(file_bytes, filename, api_key):
    """Step 1: Upload file to Mistral for OCR."""
    url = "https://api.mistral.ai/v1/files"
    headers = {"Authorization": f"Bearer {api_key}"}
    files = {"file": (filename, file_bytes, "application/pdf")}
    data = {"purpose": "ocr"}
    response = requests.post(url, headers=headers, files=files, data=data)
    response.raise_for_status()
    return response.json()

def mistral_get_file_url(file_id, api_key):
    """Step 2: Get signed URL for the uploaded file."""
    url = f"https://api.mistral.ai/v1/files/{file_id}/url"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"expiry": 24}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()["url"]

def mistral_process_ocr(document_url, api_key):
    """Step 3: Process the document via Mistral OCR."""
    url = "https://api.mistral.ai/v1/ocr"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "mistral-ocr-latest",
        "document": {
            "type": "document_url",
            "document_url": document_url
        },
        "bbox_annotation_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "element_summary",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "visual_description": {
                            "type": "string",
                            "description": "A detailed natural language description of the visual element."
                        }
                    },
                    "required": ["visual_description"],
                    "additionalProperties": False
                }
            }
        },
        "include_image_base64": True
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def process_and_ingest_document(file_bytes, filename, category):
    """The ingestion pipeline parsing standard markdown to reconstruct precise sections."""
    env = get_env_vars()
    api_key = env["mistral_api_key"]
    supabase = init_supabase()
    bucket = env["supabase_bucket"]
    
    st.info("Uploading file to AI OCR...")
    upload_res = mistral_upload_file(file_bytes, filename, api_key)
    file_id = upload_res["id"]
    
    st.info("Generating Signed URL...")
    doc_url = mistral_get_file_url(file_id, api_key)
    
    st.info("Extracting Layout and Images from document...")
    ocr_res = mistral_process_ocr(doc_url, api_key)
    
    full_markdown = []
    
    pages = ocr_res.get("pages", [])
    for page in pages:
        markdown_content = page.get("markdown", "")
        images = page.get("images", [])
        
        # Upload images & fix links
        for img in images:
            img_id = img.get("id")
            img_b64 = img.get("image_base64", "")
            if img_b64 and img_b64.startswith("data:image"):
                img_b64 = img_b64.split(",")[1]
            if img_b64 and img_id:
                try:
                    img_data = base64.b64decode(img_b64)
                    new_filename = f"{int(time.time())}_{img_id}.jpg"
                    supabase.storage.from_(bucket).upload(
                        path=new_filename,
                        file=img_data,
                        file_options={"content-type": "image/jpeg"}
                    )
                    public_url = supabase.storage.from_(bucket).get_public_url(new_filename)
                    local_pattern = f"![{img_id}]({img_id})"
                    hosted_pattern = f"![{img_id}]({public_url})"
                    markdown_content = markdown_content.replace(local_pattern, hosted_pattern)
                except Exception as e:
                    st.warning(f"Failed to process image {img_id}: {str(e)}")
        full_markdown.append(markdown_content)
    
    combined_markdown = "\n\n".join(full_markdown)
    
    st.info("Chunking document by Logical Sections...")
    # 1. Split logically by Headers
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    md_header_splits = markdown_splitter.split_text(combined_markdown)
    
    # 2. Mathematical chunking underneath headers for the LLM window
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(md_header_splits)
    
    # 3. Build precise Section IDs
    for i, doc in enumerate(docs):
        h1 = doc.metadata.get("Header 1", "")
        h2 = doc.metadata.get("Header 2", "")
        h3 = doc.metadata.get("Header 3", "")
        
        base_section = f"{h1}|{h2}|{h3}".strip("|")
        if not base_section:
            base_section = "global_document_body"
            
        # Clean section string to be safe
        safe_section = base_section.replace(" ", "_").lower()
        section_id = f"{filename}_{safe_section}"
        
        doc.metadata.update({
            "category": category,
            "source": filename,
            "section_id": section_id,
            "chunk_id": i,
        })
        
    embeddings = OpenAIEmbeddings(api_key=env["openai_api_key"])
    
    vector_store = SupabaseVectorStore(
        client=supabase,
        embedding=embeddings,
        table_name="documents",
        query_name="match_documents"
    )
    vector_store.add_documents(docs)
    st.success(f"Successfully processed and ingested '{filename}' under category: {category}!")

def identify_category_from_query(query: str, chat_history: List[Dict[str, str]]) -> str:
    env = get_env_vars()
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=env["openai_api_key"], temperature=0)
    history_str = "".join([f"{m['role'].capitalize()}: {m['content']}\n" for m in chat_history[-4:]])
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"Your job is to classify the user's latest query into one of these exact categories: {', '.join(CATEGORIES)}.\n"
                   "If the query explicitly or implicitly matches one of the categories, respond with ONLY the exact category name.\n"
                   "If unsure or unrelated, respond ONLY with 'Unknown'."),
        ("user", "Chat History:\n{history}\n\nUser Query:\n{query}")
    ])
    chain = prompt | llm
    return chain.invoke({"history": history_str, "query": query}).content.strip()

def multimodal_assistant_page():
    st.title("🧩 Multimodal RAG Agent")
    st.markdown("### Upload Documents and Query them via OCR & Vector Search")
    
    env = get_env_vars()
    if missing := [k for k, v in env.items() if not v]:
        st.warning(f"Please configure missing `.env` variables: {', '.join(missing)}")
        return

    with st.expander("📁 Upload & Process PDF", expanded=False):
        uploaded_file = st.file_uploader("Upload a PDF document to the Vector Database", type=["pdf"])
        category = st.radio("Select Document Category", CATEGORIES, horizontal=True)
        if uploaded_file and st.button("Process & Upload Document"):
            process_and_ingest_document(uploaded_file.getvalue(), uploaded_file.name, category)
            
    st.markdown("---")
    
    if 'mm_chat_history' not in st.session_state:
        st.session_state.mm_chat_history = []
        
    for message in st.session_state.mm_chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
    if prompt := st.chat_input("Ask a question about the uploaded materials..."):
        st.session_state.mm_chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            with st.spinner("Analyzing intent..."):
                predicted_category = identify_category_from_query(prompt, st.session_state.mm_chat_history)
                
            if predicted_category == "Unknown":
                clarify_msg = f"I'm not quite sure which material category you are asking about. Please specify one of: {', '.join(CATEGORIES)}."
                st.session_state.mm_chat_history.append({"role": "assistant", "content": clarify_msg})
                message_placeholder.markdown(clarify_msg)
            else:
                st.caption(f"*Filtering search for category: {predicted_category}*")
                with st.spinner("Searching for sections and expanding context..."):
                    supabase = init_supabase()
                    embeddings = OpenAIEmbeddings(api_key=env["openai_api_key"])
                    vector_store = SupabaseVectorStore(
                        client=supabase,
                        embedding=embeddings,
                        table_name="documents",
                        query_name="match_documents"
                    )
                    
                    # 1. Strict mathematical hit to locate the most relevant chunks
                    filter_dict = {"category": predicted_category}
                    retrieved_docs = vector_store.similarity_search(prompt, k=3, filter=filter_dict)
                    
                    if not retrieved_docs:
                        msg = f"I didn't find any relevant documents in the {predicted_category} category."
                        message_placeholder.markdown(msg)
                        st.session_state.mm_chat_history.append({"role": "assistant", "content": msg})
                    else:
                        print(f"\n--- Initial Vector Hits ({len(retrieved_docs)} chunks) ---")
                        for i, doc in enumerate(retrieved_docs):
                            print(f"Hit {i+1}: Source: {doc.metadata.get('source')} | Section: {doc.metadata.get('section_id')}")
                        
                        # 2. Logic-based SECTION EXPANSION
                        expanded_context = ""
                        
                        # Find unique section_ids targeted by our vector search
                        hit_sections = set(doc.metadata.get("section_id") for doc in retrieved_docs if doc.metadata.get("section_id"))
                        
                        print(f"--- Expanding into {len(hit_sections)} Logical Sections ---")
                        for section_id in hit_sections:
                            print(f"Fetching full content for section: {section_id}")
                            # Direct standard API call to fetch EVERY piece of that document section
                            res = supabase.table("documents").select("content, metadata").contains("metadata", {"section_id": section_id}).execute()
                            section_chunks = res.data
                            
                            # Order sub-chunks perfectly
                            section_chunks.sort(key=lambda x: x["metadata"].get("chunk_id", 0))
                            
                            expanded_context += f"--- Document Section Identified: {section_id} ---\n"
                            for chunk in section_chunks:
                                expanded_context += chunk["content"] + "\n\n"
                            expanded_context += f"--- End of Section ---\n\n"
                                
                        # Gen Answer
                        llm = ChatOpenAI(model="gpt-4o", api_key=env["openai_api_key"], temperature=0.1)
                        
                        system_msg = (
                            "You are a highly precise technical assistant. Your goal is to answer questions based STRICTLY on the provided Document Sections.\n\n"
                            "RULES:\n"
                            "1. FIDELITY: Use the EXACT terminology and wording found in the source text as much as possible. Do not rephrase technical details into generic language.\n"
                            "2. INTEGRATION: You may streamline, summarize, or combine information logically to answer the user, but you must not change the meaning or the specific values/data points.\n"
                            "3. ZERO EXTERNAL KNOWLEDGE: Answer using ONLY the provided context. If the answer is not in the context, state that clearly.\n"
                            "4. VISUALS: If any images (markdown format) are present in the retrieved sections, you MUST include them at the relevant point in your response.\n"
                            "5. GROUNDING: If you are combining multiple sections, prioritize showing the most important technical highlights first."
                        )
                        qa_prompt = ChatPromptTemplate.from_messages([
                            ("system", system_msg),
                            ("user", "Retrieved Document Sections:\n{context}\n\nUser Question: {question}")
                        ])
                        
                        response = (qa_prompt | llm).invoke({"context": expanded_context, "question": prompt})
                        
                        msg = response.content
                        message_placeholder.markdown(msg)
                        st.session_state.mm_chat_history.append({"role": "assistant", "content": msg})
