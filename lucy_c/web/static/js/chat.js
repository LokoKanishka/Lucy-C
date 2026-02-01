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
      const isOllamaManaged = (data.provider === 'ollama' || data.provider === 'clawdbot');
      modelSelector.disabled = !isOllamaManaged;
      modelSelector.style.opacity = !isOllamaManaged ? '0.5' : '1';
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
  const isOllamaManaged = (provider === 'ollama' || provider === 'clawdbot');
  modelSelector.disabled = !isOllamaManaged;
  modelSelector.style.opacity = !isOllamaManaged ? '0.5' : '1';
  if (window.lucySocket) {
    window.lucySocket.emit('update_config', { llm_provider: provider });
  }
  updateStatus(`Provider changed to ${provider}`, 'success');
});

modelSelector.addEventListener('change', () => {
  const selectedModel = modelSelector.value;
  currentModelDisplay.textContent = selectedModel;
  if (window.lucySocket) {
    window.lucySocket.emit('update_config', { ollama_model: selectedModel });
  }
  updateStatus(`Model changed to ${selectedModel}`, 'success');
});

// Wheel scrolling: let the browser handle it (our forced handler can break some devices)

function scrollChatToTop() {
  if (!chatMessages) return;
  chatMessages.scrollTop = 0;
}

function scrollChatToBottom() {
  if (!chatMessages) return;
  // More compatible than Element.scrollTo in some Firefox setups
  chatMessages.scrollTop = chatMessages.scrollHeight;
  // double-tap in next frame in case layout updates after DOM paint
  requestAnimationFrame(() => { chatMessages.scrollTop = chatMessages.scrollHeight; });
}

// Scroll buttons (always visible)
const scrollBottomBtn = document.getElementById('scroll-bottom');
const scrollTopBtn = document.getElementById('scroll-top');
scrollBottomBtn?.addEventListener('click', (e) => {
  e.preventDefault();
  scrollChatToBottom();
});
scrollTopBtn?.addEventListener('click', (e) => {
  e.preventDefault();
  scrollChatToTop();
});

// Expose for debugging
window.scrollChatToBottom = scrollChatToBottom;
window.scrollChatToTop = scrollChatToTop;

function showTypingIndicator() {
  const existing = document.getElementById('typing-indicator');
  if (existing) return;

  const indicator = document.createElement('div');
  indicator.id = 'typing-indicator';
  indicator.className = 'typing-indicator assistant';
  indicator.innerHTML = `
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
  `;
  chatMessages.appendChild(indicator);
  scrollChatToBottom();
}

function hideTypingIndicator() {
  const indicator = document.getElementById('typing-indicator');
  if (indicator) indicator.remove();
}

function addMessage(type, content) {
  hideTypingIndicator();
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

  scrollChatToBottom();
}

async function sendMessage() {
  const message = userInput.value.trim();
  if (!message) {
    updateStatus('Por favor, escribí un mensaje', 'warning');
    return;
  }

  const MAX_LENGTH = 2000;
  if (message.length > MAX_LENGTH) {
    updateStatus(`Mensaje muy largo (${message.length} chars). Máximo: ${MAX_LENGTH}`, 'warning');
    return;
  }

  userInput.value = '';
  userInput.style.height = 'auto';

  // Prefer Socket.IO when connected; fallback to HTTP if not.
  const session_user = getSessionUser();

  if (window.lucySocket && window.lucySocket.connected) {
    lucySocket.emit('chat_message', { message, session_user });
    showTypingIndicator();
    updateStatus('Thinking...', 'info');
    return;
  }

  // HTTP fallback
  addMessage('user', message);
  showTypingIndicator();
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
      audio.play().catch(() => { });
    }

    updateStatus('Ready', 'success');
  } catch (e) {
    console.error(e);
    updateStatus(`Error: ${e.message}`, 'error');
  }
}

if (window.lucySocket) {
  window.lucySocket.on('message', (data) => {
    addMessage(data.type, data.content);
    if (data.type === 'assistant') {
      updateStatus('Ready', 'success');
    }
  });
}

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

// expose for other scripts
window.getSessionUser = getSessionUser;
window.showTypingIndicator = showTypingIndicator;
window.hideTypingIndicator = hideTypingIndicator;

loadModels();
