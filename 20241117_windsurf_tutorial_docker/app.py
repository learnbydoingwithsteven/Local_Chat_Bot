import streamlit as st
import requests
import json
import os

# Get Ollama host from environment variable or use default
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')

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

def pull_model(model_name):
    """Pull a model from Ollama"""
    try:
        with st.spinner(f'Pulling model {model_name}... This may take a while.'):
            response = requests.post(
                f'{OLLAMA_HOST}/api/pull',
                json={"name": model_name}
            )
            if response.status_code == 200:
                return True
            return False
    except Exception as e:
        st.error(f"Error pulling model: {str(e)}")
        return False

def get_available_models():
    """Fetch available models from Ollama"""
    try:
        response = requests.get(f'{OLLAMA_HOST}/api/tags')
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
            f'{OLLAMA_HOST}/api/generate',
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

# Sidebar for model selection and pulling
st.sidebar.title("🤖 Ollama Chat Settings")

# Model pulling section
st.sidebar.subheader("Pull a Model")
model_to_pull = st.sidebar.text_input("Enter model name to pull (e.g., llama2, mistral, tinyllama)")
if st.sidebar.button("Pull Model"):
    if model_to_pull:
        success = pull_model(model_to_pull)
        if success:
            st.sidebar.success(f"Successfully pulled model: {model_to_pull}")
        else:
            st.sidebar.error(f"Failed to pull model: {model_to_pull}")

st.sidebar.markdown("---")

# Model selection section
available_models = get_available_models()
if available_models:
    selected_model = st.sidebar.selectbox(
        "Select Model",
        available_models,
        index=0
    )
else:
    st.sidebar.error("No models found. Please pull a model using the form above.")
    selected_model = None

st.sidebar.markdown("---")
st.sidebar.markdown("""
### How to use:
1. Pull a model using the form above (if not already available)
2. Select a model from the dropdown
3. Type your message and press Enter
4. Wait for the AI to respond
""")

# Main chat interface
st.title("💬 Chat with Ollama")

# Chat input
if selected_model:
    with st.form("chat_input", clear_on_submit=True):
        user_input = st.text_area("Type your message:", key="user_input", height=100)
        submitted = st.form_submit_button("Send")

        if submitted and user_input:
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Get bot response
            bot_response = chat_with_ollama(user_input, selected_model)
            
            # Add bot response to chat history
            st.session_state.messages.append({"role": "assistant", "content": bot_response})

    # Display chat history
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
                        <div><strong>Assistant:</strong></div>
                        <div>{message["content"]}</div>
                    </div>
                """, unsafe_allow_html=True)
else:
    st.info("Please select a model from the sidebar to start chatting.")
