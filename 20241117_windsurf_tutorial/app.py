import streamlit as st
import requests
import json

# Set page config
st.set_page_config(
    page_title="Ollama Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better UI
st.markdown("""
<style>
    .stTextInput > div > div > input {
        background-color: #f0f2f6;
    }
    .stTextArea > div > div > textarea {
        background-color: #f0f2f6;
    }
    .main {
        padding: 2rem;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .bot-message {
        background-color: #f5f5f5;
    }
    .stButton button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

def get_available_models():
    """Fetch available models from Ollama"""
    try:
        response = requests.get('http://localhost:11434/api/tags')
        if response.status_code == 200:
            models = response.json()
            return [model['name'] for model in models['models']]
        return []
    except:
        return []

def chat_with_ollama(message, model):
    """Send a message to Ollama and get the response"""
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                "model": model,
                "prompt": message,
                "stream": False
            }
        )
        if response.status_code == 200:
            return response.json().get('response', 'No response from the model.')
        return "Error: Unable to get response from the model."
    except Exception as e:
        return f"Error: {str(e)}"

# Sidebar for model selection
st.sidebar.title("🤖 Ollama Chat Settings")
available_models = get_available_models()
if available_models:
    selected_model = st.sidebar.selectbox(
        "Select Model",
        available_models,
        index=0
    )
else:
    st.sidebar.error("No models found. Please make sure Ollama is running.")
    selected_model = None

st.sidebar.markdown("---")
st.sidebar.markdown("""
### How to use:
1. Make sure Ollama is running locally
2. Select a model from the dropdown
3. Type your message and press Enter
4. Wait for the AI to respond
""")

# Main chat interface
st.title("🤖 Ollama Chat")

# Display chat messages
for message in st.session_state.messages:
    with st.container():
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <div><strong>You:</strong></div>
                <div>{message["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message bot-message">
                <div><strong>AI:</strong></div>
                <div>{message["content"]}</div>
            </div>
            """, unsafe_allow_html=True)

# Chat input
if selected_model:
    with st.form(key='chat_form'):
        user_input = st.text_area("Type your message:", key="chat_input", height=100)
        submit_button = st.form_submit_button("Send")
        
        if submit_button and user_input.strip():
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Get AI response
            with st.spinner("AI is thinking..."):
                ai_response = chat_with_ollama(user_input, selected_model)
                
            # Add AI response to chat history
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            
            # Force a rerun to update the chat
            st.rerun()
else:
    st.warning("Please make sure Ollama is running and select a model to start chatting.")
