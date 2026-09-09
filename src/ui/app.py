import streamlit as st
import requests

# FastAPI Backend URL
API_URL = "http://localhost:8000"

st.set_page_config(page_title="AntiRag System", page_icon="📚")

st.title("AntiRag: Document QA System")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for document upload
with st.sidebar:
    st.header("Upload Document")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if st.button("Process Document"):
        if uploaded_file is not None:
            with st.spinner("Uploading and processing..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                try:
                    response = requests.post(f"{API_URL}/documents/upload", files=files)
                    if response.status_code == 200:
                        st.success(response.json().get("message", "Document processed successfully!"))
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Failed to process document.')}")
                except Exception as e:
                    st.error(f"Connection error: {e}")
        else:
            st.warning("Please select a file first.")

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask a question about your documents..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Send request to backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(f"{API_URL}/ask", json={"question": prompt})
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "")
                    sources = data.get("sources", [])
                    
                    # Format response
                    full_response = answer
                    if sources:
                        full_response += "\n\n**Sources:**\n"
                        for src in sources:
                            full_response += f"- {src['source']} (Page {src['page']})\n"
                            
                    st.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                else:
                    error_msg = f"Error: {response.json().get('detail', 'Unknown error occurred.')}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                st.error(f"Connection error: {e}")
                st.session_state.messages.append({"role": "assistant", "content": f"Connection error: {e}"})
