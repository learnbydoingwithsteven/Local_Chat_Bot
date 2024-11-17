document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    // Function to format text with basic markdown and code blocks
    function formatText(text) {
        // Handle code blocks first
        text = text.replace(/```python\n([\s\S]*?)```/g, (match, code) => {
            const uniqueId = 'code-' + Math.random().toString(36).substr(2, 9);
            return `
                <div class="code-block-container" id="${uniqueId}">
                    <div class="code-block-header">
                        <span>Python</span>
                        <div class="code-block-buttons">
                            <button class="code-block-button" onclick="copyCode('${uniqueId}')">
                                <svg class="code-icon" viewBox="0 0 24 24">
                                    <path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>
                                </svg>
                                Copy
                            </button>
                            <button class="code-block-button run-button" onclick="runCode('${uniqueId}')">
                                <svg class="code-icon" viewBox="0 0 24 24">
                                    <path d="M8 5v14l11-7z"/>
                                </svg>
                                Run
                            </button>
                        </div>
                    </div>
                    <pre class="code-block-content"><code class="language-python">${code.trim()}</code></pre>
                    <div class="code-progress-bar">
                        <div class="progress-indicator"></div>
                    </div>
                </div>`;
        });

        // Convert numbered lists
        text = text.replace(/^\d+\.\s+/gm, '<li>') + '</li>';
        text = text.replace(/(?=<li>)([\s\S]*?)(?=(?:<li>|$))/g, function(match) {
            return match.trim() ? '<ol>' + match + '</ol>' : match;
        });

        // Convert bullet points
        text = text.replace(/^[*-]\s+/gm, '<li>') + '</li>';
        text = text.replace(/(?=<li>)([\s\S]*?)(?=(?:<li>|$))/g, function(match) {
            return match.trim() ? '<ul>' + match + '</ul>' : match;
        });

        // Convert bold text
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Convert paragraphs (double newlines)
        text = text.replace(/\n\n/g, '</p><p>');
        text = '<p>' + text + '</p>';

        // Clean up any empty paragraphs
        text = text.replace(/<p>\s*<\/p>/g, '');

        return text;
    }

    // Function to add a message to the chat
    function addMessage(content, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (isUser) {
            messageContent.textContent = content;
        } else {
            messageContent.innerHTML = formatText(content);
            // Highlight code blocks
            messageContent.querySelectorAll('pre code').forEach((block) => {
                Prism.highlightElement(block);
            });
        }
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Function to show typing indicator
    function showTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'message bot-message';
        indicator.innerHTML = `
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        indicator.id = 'typing-indicator';
        chatMessages.appendChild(indicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Function to remove typing indicator
    function removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    // Function to send message to the server
    async function sendMessage(message) {
        try {
            showTypingIndicator();
            
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });
            
            removeTypingIndicator();
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            const data = await response.json();
            addMessage(data.response);
        } catch (error) {
            removeTypingIndicator();
            addMessage('Sorry, I encountered an error. Please try again.');
            console.error('Error:', error);
        }
    }

    // Handle send button click
    sendButton.addEventListener('click', () => {
        const message = userInput.value.trim();
        if (message) {
            addMessage(message, true);
            userInput.value = '';
            sendMessage(message);
        }
    });

    // Handle enter key press
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendButton.click();
        }
    });

    // Auto-resize textarea
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = Math.min(userInput.scrollHeight, 150) + 'px';
    });
});

// Function to copy code to clipboard
window.copyCode = async function(containerId) {
    const container = document.getElementById(containerId);
    const codeElement = container.querySelector('code');
    const code = codeElement.textContent;
    
    try {
        await navigator.clipboard.writeText(code);
        const copyButton = container.querySelector('button');
        copyButton.textContent = 'Copied!';
        setTimeout(() => {
            copyButton.textContent = 'Copy';
        }, 2000);
    } catch (err) {
        console.error('Failed to copy code:', err);
    }
};

// Function to run Python code
window.runCode = async function(containerId) {
    const container = document.getElementById(containerId);
    const codeElement = container.querySelector('code');
    const code = codeElement.textContent;
    const runButton = container.querySelector('.run-button');
    const progressBar = container.querySelector('.code-progress-bar');
    
    // Remove previous output if it exists
    const previousOutput = container.querySelector('.code-output');
    if (previousOutput) {
        previousOutput.remove();
    }
    
    // Show progress bar and disable button
    progressBar.style.display = 'block';
    runButton.disabled = true;
    runButton.innerHTML = `
        <svg class="code-icon spin" viewBox="0 0 24 24">
            <path d="M12 6v3l4-4-4-4v3c-4.42 0-8 3.58-8 8 0 1.57.46 3.03 1.24 4.26L6.7 14.8c-.45-.83-.7-1.79-.7-2.8 0-3.31 2.69-6 6-6zm6.76 1.74L17.3 9.2c.44.84.7 1.79.7 2.8 0 3.31-2.69 6-6 6v-3l-4 4 4 4v-3c4.42 0 8-3.58 8-8 0-1.57-.46-3.03-1.24-4.26z"/>
        </svg>
        Running
    `;
    
    try {
        const response = await fetch('/run_code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ code: code })
        });
        
        const data = await response.json();
        
        // Create output element
        const outputDiv = document.createElement('div');
        outputDiv.className = `code-output${data.error ? ' error' : ''}`;
        outputDiv.textContent = data.error || data.output || 'Code executed successfully!';
        container.appendChild(outputDiv);
        
    } catch (error) {
        const outputDiv = document.createElement('div');
        outputDiv.className = 'code-output error';
        outputDiv.textContent = 'Failed to execute code. Please try again.';
        container.appendChild(outputDiv);
    } finally {
        // Hide progress bar and restore button
        progressBar.style.display = 'none';
        runButton.disabled = false;
        runButton.innerHTML = `
            <svg class="code-icon" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z"/>
            </svg>
            Run
        `;
    }
};
