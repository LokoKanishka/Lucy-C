// Chat functionality
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const modelSelector = document.getElementById('model-selector');
const currentModelDisplay = document.getElementById('current-model');

async function loadModels() {
  try {
    const response = await fetch('/api/models');
    const data = await response.json();

    if (data.models && data.models.length > 0) {
      modelSelector.innerHTML = '';
      data.models.forEach(model => {
        const option = document.createElement('option');
        option.value = model;
        option.textContent = model;
        modelSelector.appendChild(option);
      });
      currentModelDisplay.textContent = data.current || data.models[0];
      if (data.current) modelSelector.value = data.current;
    }
  } catch (error) {
    console.error('Error loading models:', error);
    modelSelector.innerHTML = '<option>Error loading models</option>';
  }
}

modelSelector.addEventListener('change', () => {
  const selectedModel = modelSelector.value;
  currentModelDisplay.textContent = selectedModel;
  lucySocket.emit('update_config', { ollama_model: selectedModel });
  updateStatus(`Model changed to ${selectedModel}`, 'success');
});

function addMessage(type, content) {
  const welcomeMsg = chatMessages.querySelector('.welcome-message');
  if (welcomeMsg) welcomeMsg.remove();

  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${type}`;

  const header = document.createElement('div');
  header.className = 'message-header';
  header.textContent = type === 'user' ? 'Diego' : 'lucy';

  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';
  contentDiv.textContent = content;

  messageDiv.appendChild(header);
  messageDiv.appendChild(contentDiv);
  chatMessages.appendChild(messageDiv);

  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;

  userInput.value = '';
  userInput.style.height = 'auto';

  lucySocket.emit('chat_message', { message });
  updateStatus('Thinking...', 'info');
}

lucySocket.on('message', (data) => {
  addMessage(data.type, data.content);
  if (data.type === 'assistant') {
    updateStatus('Ready', 'success');
  }
});

sendBtn.addEventListener('click', sendMessage);

userInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

userInput.addEventListener('input', () => {
  userInput.style.height = 'auto';
  userInput.style.height = userInput.scrollHeight + 'px';
});

loadModels();
