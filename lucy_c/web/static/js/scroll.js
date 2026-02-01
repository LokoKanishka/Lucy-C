// Dedicated scroll controls (buttons + slider)
(function () {
  const chat = document.getElementById('chat-messages');
  const btnTop = document.getElementById('scroll-top');
  const btnBottom = document.getElementById('scroll-bottom');
  const slider = document.getElementById('scroll-slider');

  if (!chat) return;

  function maxScrollTop() {
    return Math.max(0, chat.scrollHeight - chat.clientHeight);
  }

  // State to track if user is reading previous messages
  let userIsScrolling = false;
  const AUTOSCROLL_THRESHOLD = 50; // px

  function checkScrollPosition() {
    if (!chat) return;
    const distanceToBottom = chat.scrollHeight - (chat.scrollTop + chat.clientHeight);
    // If user is within threshold of bottom, they follow the conversation
    userIsScrolling = distanceToBottom > AUTOSCROLL_THRESHOLD;

    // Update FAB visibility
    if (btnBottom) {
      btnBottom.style.opacity = userIsScrolling ? '1' : '0.3';
      btnBottom.style.pointerEvents = userIsScrolling ? 'auto' : 'none';
    }
  }

  function scrollToBottom(force = false) {
    if (!chat) return;
    // Only scroll if forced OR if the user was already at the bottom
    if (force || !userIsScrolling) {
      chat.scrollTop = chat.scrollHeight;
    }
  }

  function updateSliderFromScroll() {
    if (!slider) return;
    const max = maxScrollTop();
    const pct = max === 0 ? 100 : Math.round((chat.scrollTop / max) * 100);
    slider.value = String(pct);
  }

  function scrollToPct(pct) {
    const max = maxScrollTop();
    chat.scrollTop = Math.round((pct / 100) * max);
  }

  btnTop?.addEventListener('click', (e) => {
    e.preventDefault();
    chat.scrollTop = 0;
  });

  btnBottom?.addEventListener('click', (e) => {
    e.preventDefault();
    scrollToBottom(true);
  });

  slider?.addEventListener('input', () => {
    const pct = Number(slider.value || '0');
    scrollToPct(pct);
  });

  chat.addEventListener('scroll', () => {
    updateSliderFromScroll();
    checkScrollPosition();
  });

  window.addEventListener('resize', () => {
    updateSliderFromScroll();
    checkScrollPosition();
  });

  // Expose for external calls (e.g. from chat.js on new message)
  window.scrollToBottom = scrollToBottom;

  // Initial check
  setInterval(checkScrollPosition, 500);
  checkScrollPosition();
})();
