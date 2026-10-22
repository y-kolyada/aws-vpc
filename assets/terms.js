// terms.js - interactive term cards on phones and wide screens
(function () {
  function closeAllTerms() {
    document.querySelectorAll('.term[data-open]').forEach((term) => {
      term.removeAttribute('data-open');
      const btn = term.querySelector('.term-btn');
      if (btn) btn.setAttribute('aria-expanded', 'false');
      const card = term.querySelector('.term-card');
      if (card) card.setAttribute('hidden', '');
    });
  }

  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.term-btn');
    const closeBtn = e.target.closest('.term-close');
    const card = e.target.closest('.term-card');

    if (closeBtn) {
      closeAllTerms();
      return;
    }

    if (btn) {
      const term = btn.closest('.term');
      if (!term) return;
      const isOpen = term.hasAttribute('data-open');
      closeAllTerms();
      if (!isOpen) {
        term.setAttribute('data-open', '');
        btn.setAttribute('aria-expanded', 'true');
        const termCard = term.querySelector('.term-card');
        if (termCard) termCard.removeAttribute('hidden');
      }
      return;
    }

    if (!card) {
      closeAllTerms();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeAllTerms();
    }
  });
})();
