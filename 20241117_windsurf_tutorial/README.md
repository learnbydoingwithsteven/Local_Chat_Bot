# Ollama Chat Interface

A sleek and modern chat interface for Ollama models built with Streamlit.

## Features

- 🤖 Connect to local Ollama instance
- 📋 Dynamic model selection from available Ollama models
- 💬 Clean chat interface with message history
- 🎨 Modern UI design with custom styling
- ⚡ Real-time responses from AI models

## Prerequisites

1. Python 3.7+
2. Ollama installed and running locally
3. pip (Python package manager)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd ollama-chat
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Make sure Ollama is running on your system
2. Run the Streamlit application:
```bash
streamlit run app.py
```
3. Open your browser and navigate to the URL shown in the terminal (usually http://localhost:8501)

## Usage

1. Select an available Ollama model from the dropdown in the sidebar
2. Type your message in the text area
3. Click "Send" or press Enter to send your message
4. Wait for the AI to respond
5. Your chat history will be maintained during the session

## Note

- Ensure Ollama is running locally on port 11434 (default port)
- The application will automatically detect available models from your Ollama installation
- Chat history is maintained only during the current session
