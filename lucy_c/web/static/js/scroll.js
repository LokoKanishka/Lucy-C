// Dedicated scroll controls (buttons + slider)
(function(){
  const chat = document.getElementById('chat-messages');
  const btnTop = document.getElementById('scroll-top');
  const btnBottom = document.getElementById('scroll-bottom');
  const slider = document.getElementById('scroll-slider');

  if (!chat) return;

  function maxScrollTop() {
    return Math.max(0, chat.scrollHeight - chat.clientHeight);
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
    chat.scrollTop = chat.scrollHeight;
    requestAnimationFrame(() => { chat.scrollTop = chat.scrollHeight; });
  });

  slider?.addEventListener('input', () => {
    const pct = Number(slider.value || '0');
    scrollToPct(pct);
  });

  chat.addEventListener('scroll', updateSliderFromScroll);
  window.addEventListener('resize', updateSliderFromScroll);

  // Keep it in sync periodically in case messages append
  setInterval(updateSliderFromScroll, 250);
  updateSliderFromScroll();
})();
