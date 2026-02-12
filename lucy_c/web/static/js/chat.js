const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const modelSelector = document.getElementById('model-selector');
const currentModelDisplay = document.getElementById('current-model');
const logsContent = document.getElementById('logs-content');

// Shared elements (already declared in voice.js or other scripts)
// Note: We don't redeclare them with const to avoid SyntaxErrors.
// We just ensure we have references if they weren't defined elsewhere.
if (typeof handsfreeToggle === 'undefined') window.handsfreeToggle = document.getElementById('handsfree-toggle');
if (typeof autoSpeakToggle === 'undefined') window.autoSpeakToggle = document.getElementById('auto-speak-toggle');
if (typeof voiceBtn === 'undefined') window.voiceBtn = document.getElementById('voice-btn');

// stable per-browser id to keep session consistent
function getSessionUser() {
  let id = localStorage.getItem('lucy_session_user');
  if (!id) {
    id = 'lucy-c:' + crypto.randomUUID();
    localStorage.setItem('lucy_session_user', id);
  }
  return id;
}

function addLog(message, type = 'info') {
  if (!logsContent) return;
  const entry = document.createElement('div');
  entry.className = `log-entry log-${type}`;
  const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  entry.textContent = `[${time}] ${message}`;
  logsContent.appendChild(entry);

  // Auto-scroll log panel
  logsContent.scrollTop = logsContent.scrollHeight;

  // Keep only last 50 logs for performance
  if (logsContent.children.length > 50) {
    logsContent.removeChild(logsContent.firstChild);
  }
}

async function loadModels() {
  console.log('loadModels: Started');
  try {
    const response = await fetch('/api/models');
    const data = await response.json();
    console.log('loadModels: Data received', data);

    if (data.models && data.models.length > 0) {
      console.log('loadModels: Populating selector with', data.models.length, 'models');
      if (modelSelector) {
        modelSelector.innerHTML = '';
        data.models.forEach(model => {
          const option = document.createElement('option');
          option.value = model.name;
          option.textContent = model.name;
          modelSelector.appendChild(option);
        });
        if (data.current) modelSelector.value = data.current;
      }
      if (currentModelDisplay) {
        currentModelDisplay.textContent = data.current || (data.models && data.models[0]?.name) || '---';
      }
      const providerDisplay = document.getElementById('current-provider');
      if (providerDisplay && data.provider) {
        providerDisplay.textContent = data.provider.charAt(0).toUpperCase() + data.provider.slice(1);
      }
      console.log('loadModels: UI updated');
    } else {
      console.warn('loadModels: No models found or invalid shape');
    }
  } catch (error) {
    console.error('loadModels: Error', error);
    if (modelSelector) {
      modelSelector.innerHTML = '<option>Error cargando modelos</option>';
    }
  }
}

modelSelector?.addEventListener('change', () => {
  const selectedModel = modelSelector.value;
  if (currentModelDisplay) currentModelDisplay.textContent = selectedModel;
  if (window.lucySocket) {
    const session_user = getSessionUser();
    window.lucySocket.emit('update_config', {
      ollama_model: selectedModel,
      session_user: session_user
    });
  }
  updateStatus(`Cerebro cambiado a ${selectedModel}`, 'success');
  addLog(`🔄 Cambio de cerebro: ${selectedModel}`, 'brain');
});

if (window.lucySocket) {
  window.lucySocket.on('moltbot_log', (data) => {
    addLog(data.message, data.type || 'info');
  });
}

function scrollChatToTop() {
  if (!chatMessages) return;
  chatMessages.scrollTop = 0;
}

function scrollChatToBottom() {
  if (!chatMessages) return;
  chatMessages.scrollTop = chatMessages.scrollHeight;
  requestAnimationFrame(() => { chatMessages.scrollTop = chatMessages.scrollHeight; });
}

// Scroll buttons
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

  // Parse tool results like [[TAG]]: Content
  // We'll split the content by double newlines or single newlines that look like tool tags
  const blocks = content.split('\n\n');
  blocks.forEach(block => {
    const trimmed = block.trim();
    if (!trimmed) return;

    // Check for [TAG]: pattern
    const toolMatch = trimmed.match(/^\[(.*?)\]:\s*(.*)/s);
    if (toolMatch) {
      const tag = toolMatch[1];
      const result = toolMatch[2];

      const toolBadge = document.createElement('div');
      toolBadge.className = 'tool-result-badge';

      // Map some emojis to classes for better coloring if needed
      let typeClass = 'generic';
      if (tag.includes('🖐️') || tag.includes('MANOS')) typeClass = 'actuator';
      if (tag.includes('👁️') || tag.includes('OJOS')) typeClass = 'sensor';
      if (tag.includes('🧠') || tag.includes('MEMORIA')) typeClass = 'memory';
      if (tag.includes('⚠️') || tag.includes('ERROR')) typeClass = 'error';
      if (tag.includes('🛡️') || tag.includes('SEGURIDAD')) typeClass = 'security';

      toolBadge.classList.add(`tool-${typeClass}`);
      toolBadge.innerHTML = `<span class="tag">${tag}</span><span class="res">${result}</span>`;
      contentDiv.appendChild(toolBadge);
    } else {
      const p = document.createElement('p');
      p.textContent = trimmed;
      contentDiv.appendChild(p);
    }
  });

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

  userInput.value = '';
  userInput.style.height = 'auto';

  const session_user = getSessionUser();

  if (window.lucySocket && window.lucySocket.connected) {
    lucySocket.emit('chat_message', { message, session_user });
    showTypingIndicator();
    updateStatus('Pensando...', 'info');
    return;
  }

  // Fallback HTTP si Socket.IO falla
  addMessage('user', message);
  showTypingIndicator();
  updateStatus('Pensando (HTTP)...', 'info');
  try {
    const r = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_user })
    });
    const data = await r.json();
    if (!data.ok) throw new Error(data.error || 'Chat falló');

    addMessage('assistant', data.reply);
    updateStatus('Lista', 'success');
  } catch (e) {
    console.error(e);
    updateStatus(`Error: ${e.message}`, 'error');
  }
}

if (window.lucySocket) {
  window.lucySocket.on('message', (data) => {
    addMessage(data.type, data.content);
    if (data.type === 'assistant') {
      updateStatus('Lista', 'success');
      // Signal start of response (voice should pause)
      window.dispatchEvent(new Event('lucy:response_start'));
    }
  });
}

sendBtn?.addEventListener('click', sendMessage);

userInput?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

userInput?.addEventListener('input', () => {
  userInput.style.height = 'auto';
  userInput.style.height = userInput.scrollHeight + 'px';
});

// Keyboard Shortcuts
window.addEventListener('keydown', (e) => {
  // Focus Input (Esc)
  if (e.key === 'Escape') {
    userInput.focus();
  }

  // Commands with Ctrl
  if (e.ctrlKey) {
    switch (e.key.toLowerCase()) {
      case 'm': // Toggle Mic
        e.preventDefault();
        voiceBtn?.click();
        addLog('Command: Toggle Mic', 'info');
        break;
      case 'h': // Toggle Hands-free
        e.preventDefault();
        if (handsfreeToggle) {
          handsfreeToggle.checked = !handsfreeToggle.checked;
          handsfreeToggle.dispatchEvent(new Event('change'));
          addLog('Command: Toggle Hands-free', hfEnabled ? 'success' : 'info');
        }
        break;
      case 'l': // Clear View
        e.preventDefault();
        chatMessages.innerHTML = '';
        addLog('Command: Visual Clear', 'info');
        updateStatus('Vista de chat limpia', 'info');
        break;
    }
  }
});

async function loadHistory() {
  const session_user = getSessionUser();
  try {
    const response = await fetch(`/api/history?session_user=${session_user}`);
    const data = await response.json();
    if (data.ok && data.items) {
      // Clear welcome message if there is history
      if (data.items.length > 0) {
        const welcomeMsg = chatMessages.querySelector('.welcome-message');
        if (welcomeMsg) welcomeMsg.remove();
      }

      data.items.forEach(item => {
        // Render user message (transcript if voice, user_text if text)
        const userText = item.kind === 'voice' ? item.transcript : item.user_text;
        if (userText) {
          addMessage('user', userText);
        }
        // Render assistant reply
        if (item.reply) {
          addMessage('assistant', item.reply);
        }
      });
      scrollChatToBottom();
    }
  } catch (error) {
    console.error('Error loading history:', error);
    addLog('Falló al cargar el historial.', 'error');
  }
}

// Persist settings
handsfreeToggle?.addEventListener('change', () => {
  localStorage.setItem('lucy_handsfree', handsfreeToggle?.checked);
});

autoSpeakToggle?.addEventListener('change', () => {
  localStorage.setItem('lucy_autospeak', autoSpeakToggle?.checked);
});

function restoreSettings() {
  if (localStorage.getItem('lucy_handsfree') === 'true' && handsfreeToggle) {
    handsfreeToggle.checked = true;
    // Trigger the event manually to start logic
    handsfreeToggle.dispatchEvent(new Event('change'));
  }
  if (localStorage.getItem('lucy_autospeak') === 'false' && autoSpeakToggle) {
    autoSpeakToggle.checked = false;
  }
}

loadModels().then(() => {
  restoreSettings();
  loadHistory();
});
