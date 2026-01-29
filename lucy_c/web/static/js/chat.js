// Chat functionality
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const providerSelector = document.getElementById('provider-selector');
const modelSelector = document.getElementById('model-selector');
const currentModelDisplay = document.getElementById('current-model');
const currentProviderDisplay = document.getElementById('current-provider');

// stable per-browser id to keep the Clawdbot session consistent
function getSessionUser() {
  let id = localStorage.getItem('lucy_session_user');
  if (!id) {
    id = 'lucy-c:' + crypto.randomUUID();
    localStorage.setItem('lucy_session_user', id);
  }
  return id;
}

async function loadModels() {
  try {
    const response = await fetch('/api/models');
    const data = await response.json();

    if (data.provider && providerSelector) {
      providerSelector.value = data.provider;
      currentProviderDisplay.textContent = `provider: ${data.provider}`;
      // Hide/show model selector depending on provider
      modelSelector.disabled = (data.provider !== 'ollama');
      modelSelector.style.opacity = (data.provider !== 'ollama') ? '0.5' : '1';
    }

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

providerSelector?.addEventListener('change', () => {
  const provider = providerSelector.value;
  currentProviderDisplay.textContent = `provider: ${provider}`;
  modelSelector.disabled = (provider !== 'ollama');
  modelSelector.style.opacity = (provider !== 'ollama') ? '0.5' : '1';
  lucySocket.emit('update_config', { llm_provider: provider });
  updateStatus(`Provider changed to ${provider}`, 'success');
});

modelSelector.addEventListener('change', () => {
  const selectedModel = modelSelector.value;
  currentModelDisplay.textContent = selectedModel;
  lucySocket.emit('update_config', { ollama_model: selectedModel });
  updateStatus(`Model changed to ${selectedModel}`, 'success');
});

// Wheel scrolling: let the browser handle it (our forced handler can break some devices)

// Scroll-to-bottom button
const scrollBtn = document.getElementById('scroll-bottom');
function updateScrollBtn() {
  if (!chatMessages || !scrollBtn) return;
  const nearBottom = (chatMessages.scrollHeight - chatMessages.scrollTop - chatMessages.clientHeight) < 80;
  scrollBtn.style.display = nearBottom ? 'none' : 'block';
}
chatMessages?.addEventListener('scroll', updateScrollBtn);
scrollBtn?.addEventListener('click', () => {
  if (!chatMessages) return;
  chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: 'smooth' });
});
setInterval(updateScrollBtn, 500);

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

async function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;

  userInput.value = '';
  userInput.style.height = 'auto';

  // Prefer Socket.IO when connected; fallback to HTTP if not.
  const session_user = getSessionUser();

  if (window.lucySocket && window.lucySocket.connected) {
    lucySocket.emit('chat_message', { message, session_user });
    updateStatus('Thinking...', 'info');
    return;
  }

  // HTTP fallback
  addMessage('user', message);
  updateStatus('Thinking (HTTP)...', 'info');
  try {
    const r = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_user })
    });
    const data = await r.json();
    if (!data.ok) throw new Error(data.error || 'HTTP chat failed');

    addMessage('assistant', data.reply);

    const autoSpeak = document.getElementById('auto-speak-toggle');
    if (autoSpeak && autoSpeak.checked && data.audio && data.audio.wav_base64) {
      const audio = new Audio(`data:${data.audio.mime || 'audio/wav'};base64,${data.audio.wav_base64}`);
      window.__lucy_lastAudio = audio;
      audio.play().catch(() => {});
    }

    updateStatus('Ready', 'success');
  } catch (e) {
    console.error(e);
    updateStatus(`Error: ${e.message}`, 'error');
  }
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

// expose for voice.js
window.getSessionUser = getSessionUser;

loadModels();
