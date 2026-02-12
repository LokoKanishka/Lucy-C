// Virtual Display Control
// Add this at the end of chat.js or as a separate file

(function () {
    const toggle = document.getElementById('virtual-display-toggle');
    const displayText = document.getElementById('display-text');
    const displayIndicator = document.getElementById('display-indicator');

    if (!toggle) {
        console.warn('Virtual display toggle not found');
        return;
    }

    // Load initial status
    async function loadDisplayStatus() {
        try {
            const response = await fetch('/api/settings/virtual_display');
            const data = await response.json();

            toggle.checked = data.enabled;
            updateDisplayUI(data);
        } catch (error) {
            console.error('Failed to load display status:', error);
        }
    }

    // Toggle virtual display
    toggle.addEventListener('change', async (e) => {
        const enabled = e.target.checked;

        try {
            const response = await fetch('/api/settings/virtual_display', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled })
            });

            const data = await response.json();

            if (data.success) {
                updateDisplayUI(data);

                // Notify via socket if available
                if (window.socket) {
                    window.socket.emit('status', {
                        message: enabled ? '🖥️ Modo Fantasma activado' : '🖥️ Modo Principal activado',
                        type: 'info'
                    });
                }
            } else {
                console.error('Toggle failed:', data.error);
                // Revert on error
                toggle.checked = !enabled;
            }
        } catch (error) {
            console.error('Failed to toggle display:', error);
            // Revert on error
            toggle.checked = !enabled;
        }
    });

    function updateDisplayUI(data) {
        if (!displayText || !displayIndicator) return;

        if (data.enabled && data.status === 'active') {
            displayText.textContent = `Display: Virtual ${data.display || ':99'}`;
            displayIndicator.className = 'w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)] animate-pulse';
        } else if (data.enabled && data.status !== 'active') {
            displayText.textContent = 'Display: Iniciando...';
            displayIndicator.className = 'w-2 h-2 rounded-full bg-yellow-500 animate-pulse';
        } else {
            displayText.textContent = 'Display: Principal';
            displayIndicator.className = 'w-2 h-2 rounded-full bg-slate-500';
        }
    }

    // Load on page load
    loadDisplayStatus();

    // Refresh status every 10 seconds
    setInterval(loadDisplayStatus, 10000);
})();
