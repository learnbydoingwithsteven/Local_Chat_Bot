# Ollama Chat Interface

A sleek and modern chat interface for Ollama models built with Streamlit.

## Features

- 🤖 Connect to local Ollama instance
- 📋 Dynamic model selection from available Ollama models
- 💬 Clean chat interface with message history
- 🎨 Modern UI design with custom styling
- ⚡ Real-time responses from AI models
- 🔄 Pull new models directly from the UI
- 🐳 Docker support for easy deployment

## Prerequisites

Choose one of the following setup options:

### Local Setup
1. Python 3.7+
2. Ollama installed and running locally
3. pip (Python package manager)

### Docker Setup
1. Docker and Docker Compose installed
2. Internet connection for pulling Docker images

## Installation

### Local Installation
1. Clone this repository:
```bash
git clone <repository-url>
cd ollama-chat
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

### Docker Installation
1. Clone this repository
2. No additional installation needed - Docker will handle dependencies

## Running the Application

### Local Run
1. Make sure Ollama is running on your system
2. Run the Streamlit application:
```bash
streamlit run app.py
```
3. Open your browser and navigate to http://localhost:8501

### Docker Run
1. Start the application using Docker Compose:
```bash
docker-compose up -d
```
2. Open your browser and navigate to http://localhost:8502
3. To stop the application:
```bash
docker-compose down
```

## Docker Configuration

The application runs in two containers:
- Streamlit UI container (exposed on port 8502)
- Ollama service container (internal port 11434)

Environment variables:
- `OLLAMA_HOST`: Set to 'http://ollama:11434' in Docker environment
- `PORT`: Streamlit port (default: 8502)

Volume mounts:
- Ollama data is persisted in a named volume

## Usage

1. If using a new model:
   - Enter the model name in the "Pull New Model" field in the sidebar
   - Click "Pull Model" and wait for the download to complete
2. Select an available model from the dropdown in the sidebar
3. Type your message in the text area
4. Click "Send" or press Enter to send your message
5. Wait for the AI to respond
6. Your chat history will be maintained during the session

## Note

- When running locally, ensure Ollama is running on port 11434 (default port)
- The application will automatically detect available models
- Chat history is maintained only during the current session
- Docker deployment handles all networking automatically
- Large models may take several minutes to pull
