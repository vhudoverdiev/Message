document.querySelectorAll('[data-confirm]').forEach((el) => {
  el.addEventListener('submit', (e) => {
    const text = el.getAttribute('data-confirm') || 'Подтвердить действие?';
    if (!window.confirm(text)) {
      e.preventDefault();
    }
  });
});
