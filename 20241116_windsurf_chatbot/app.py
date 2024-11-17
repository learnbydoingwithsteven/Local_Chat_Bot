from flask import Flask, render_template, request, jsonify, send_file, Response
import requests
import json
import subprocess
import sys
import tempfile
import os
import re
from contextlib import contextmanager
import wikipedia
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import hashlib
import pickle
import base64
import io

app = Flask(__name__)

# Cache directory for installed packages
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'package_cache')
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# List of allowed packages for security
ALLOWED_PACKAGES = {
    'numpy',
    'pandas',
    'matplotlib',
    'seaborn',
    'scikit-learn',
    'yfinance',
    'requests',
    'beautifulsoup4',
    'plotly',
    'scipy',
    'pillow',
}

def extract_imports(code):
    """Extract import statements from the code."""
    imports = set()
    # Match both 'import package' and 'from package import stuff'
    import_patterns = [
        r'^import\s+(\w+)',
        r'from\s+(\w+)\s+import',
    ]
    
    for pattern in import_patterns:
        matches = re.finditer(pattern, code, re.MULTILINE)
        for match in matches:
            package = match.group(1)
            # Get base package name (e.g., 'pandas' from 'pandas.DataFrame')
            base_package = package.split('.')[0]
            imports.add(base_package)
    
    return imports

def get_wikipedia_context(query, max_results=2):
    """Get relevant context from Wikipedia."""
    try:
        # Search Wikipedia
        search_results = wikipedia.search(query, results=max_results)
        context = []
        for title in search_results:
            try:
                page = wikipedia.page(title)
                context.append({
                    'source': 'Wikipedia',
                    'title': title,
                    'content': page.summary[:500]  # First 500 chars
                })
            except:
                continue
        return context
    except:
        return []

def get_google_news(query, max_results=3):
    """Get relevant news from Google News."""
    try:
        url = f"https://news.google.com/rss/search?q={query}"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')[:max_results]
        
        return [{
            'source': 'Google News',
            'title': item.title.text,
            'content': item.description.text if item.description else ''
        } for item in items]
    except:
        return []

def get_duckduckgo_results(query, max_results=3):
    """Get search results from DuckDuckGo."""
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json"
        response = requests.get(url)
        data = response.json()
        
        results = []
        if data.get('AbstractText'):
            results.append({
                'source': 'DuckDuckGo',
                'title': data.get('Heading', ''),
                'content': data.get('AbstractText', '')
            })
        
        return results[:max_results]
    except:
        return []

def get_package_cache_path(package):
    """Generate a unique cache path for a package."""
    return os.path.join(CACHE_DIR, f"{package}.cache")

def is_package_cached(package):
    """Check if a package is already cached."""
    cache_path = get_package_cache_path(package)
    return os.path.exists(cache_path)

def install_dependencies(required_packages):
    """Install required packages if they're in the allowed list, using cache when possible."""
    packages_to_install = required_packages.intersection(ALLOWED_PACKAGES)
    if not packages_to_install:
        return True, "No packages to install"
    
    try:
        # Use cached packages when available
        for package in packages_to_install:
            if not is_package_cached(package):
                # Install only if not cached
                try:
                    subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', package],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    # Cache the successful installation
                    cache_path = get_package_cache_path(package)
                    with open(cache_path, 'wb') as f:
                        pickle.dump({'installed_at': datetime.now()}, f)
                except subprocess.CalledProcessError as e:
                    return False, f"Failed to install {package}: {e.stderr}"
        
        return True, f"Successfully installed: {', '.join(packages_to_install)}"
    except Exception as e:
        return False, f"Error setting up environment: {str(e)}"

def get_context(message, sources):
    context = []
    citations = []
    
    try:
        if 'wikipedia' in sources:
            wiki_results = get_wikipedia_context(message)
            context.extend(wiki_results)
            citations.extend([{
                'source': 'Wikipedia',
                'title': item.get('title', ''),
                'content': item.get('content', '')[:200]
            } for item in wiki_results])
            
        if 'google_news' in sources:
            news_results = get_google_news(message)
            context.extend(news_results)
            citations.extend([{
                'source': 'Google News',
                'title': item.get('title', ''),
                'content': item.get('content', '')[:200]
            } for item in news_results])
            
        if 'duckduckgo' in sources:
            ddg_results = get_duckduckgo_results(message)
            context.extend(ddg_results)
            citations.extend([{
                'source': 'DuckDuckGo',
                'title': item.get('title', ''),
                'content': item.get('content', '')[:200]
            } for item in ddg_results])
    except Exception as e:
        print(f"Error gathering context: {str(e)}")
    
    return context, citations

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['GET'])
def chat():
    user_message = request.args.get('message', '')
    selected_sources = json.loads(request.args.get('sources', '["llm"]'))
    selected_model = request.args.get('model', 'llama2')
    
    # Only gather context if sources other than LLM are selected
    context = []
    citations = []
    if set(selected_sources) - {'llm'}:
        context, citations = get_context(user_message, selected_sources)
    
    # Format context for the prompt
    context_text = "\n\n".join([
        f"{item['source']}: {item['content']}"
        for item in context
    ]) if context else ""
    
    # Prepare the prompt based on available context
    if context_text:
        prompt = f"""Context information:
{context_text}

User question: {user_message}

Please provide a helpful response based on the context above. If you want to include code examples, wrap them in ```python and ``` tags."""
    else:
        prompt = f"""User question: {user_message}

Please provide a helpful response. If you want to include code examples, wrap them in ```python and ``` tags."""
    
    # Prepare the request to Ollama
    ollama_url = "http://localhost:11434/api/generate"
    payload = {
        "model": selected_model,
        "prompt": prompt,
        "stream": True
    }

    def generate():
        # Create a session for better connection management
        session = requests.Session()
        
        try:
            # First yield citations if any
            if citations:
                yield f"data: {json.dumps({'citations': citations})}\n\n"
            
            # Make the request with a timeout
            response = session.post(ollama_url, json=payload, stream=True)
            if response.status_code != 200:
                yield f"data: {json.dumps({'error': 'Failed to get response from Ollama'})}\n\n"
                return

            # Stream the response
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    if chunk.get('done', False):
                        break
                    if 'response' in chunk:
                        yield f"data: {json.dumps({'text': chunk['response']})}\n\n"
                except json.JSONDecodeError:
                    continue
                except GeneratorExit:
                    # Client disconnected, close the response
                    response.close()
                    session.close()
                    return
                
        except requests.exceptions.Timeout:
            yield f"data: {json.dumps({'error': 'Request timed out'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            session.close()
            
        yield "data: [DONE]\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

@app.route('/models', methods=['GET'])
def get_models():
    try:
        response = requests.get('http://localhost:11434/api/tags')
        if response.status_code == 200:
            models = response.json().get('models', [])
            return jsonify([model['name'] for model in models])
        return jsonify([])
    except Exception as e:
        print(f"Error getting models: {str(e)}")
        return jsonify([])

def run_code_in_sandbox(code):
    try:
        # Create a temporary directory for code execution
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create virtual environment
            venv_path = os.path.join(temp_dir, 'venv')
            python_path = os.path.join(venv_path, 'Scripts', 'python.exe')
            
            subprocess.run(
                [sys.executable, '-m', 'venv', venv_path],
                check=True,
                capture_output=True
            )
            
            # Create the script file
            script_path = os.path.join(temp_dir, 'script.py')
            with open(script_path, 'w') as f:
                # Add matplotlib configuration for non-interactive backend
                setup_code = """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import sys
import traceback

try:
"""
                # Indent the user's code
                indented_code = '\n'.join('    ' + line for line in code.splitlines())
                
                # Add error handling and figure saving
                cleanup_code = """
except Exception as e:
    print(traceback.format_exc(), file=sys.stderr)
    sys.exit(1)

# Save any plots to a bytes buffer
if plt.get_fignums():
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    with open('plot.png', 'wb') as f:
        f.write(buf.getvalue())
    plt.close('all')
"""
                f.write(setup_code + indented_code + cleanup_code)
            
            # Run the script and capture output
            result = subprocess.run(
                [python_path, script_path],
                capture_output=True,
                text=True,
                cwd=temp_dir
            )
            
            # Check for plot file
            plot_path = os.path.join(temp_dir, 'plot.png')
            plot_data = None
            if os.path.exists(plot_path):
                with open(plot_path, 'rb') as f:
                    plot_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Prepare the response
            if result.returncode != 0:
                return {'error': result.stderr}
            
            output = result.stdout.strip()
            if plot_data:
                output = f"{output}\n\n<img src='data:image/png;base64,{plot_data}' />"
            
            return output if output else "Code executed successfully"
            
    except subprocess.CalledProcessError as e:
        return {'error': f"Error setting up environment: {str(e)}"}
    except Exception as e:
        return {'error': f"Error executing code: {str(e)}"}

@app.route('/run_code', methods=['POST'])
def run_code():
    data = request.json
    code = data.get('code', '')
    
    if not code:
        return jsonify({'error': 'No code provided'})
    
    result = run_code_in_sandbox(code)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
