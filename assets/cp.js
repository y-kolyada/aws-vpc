// cp.js - a copy button in every code block. Loaded only on pages that have
// code, so a stub page does not carry it.
(function () {
  // Labels follow the page language, so one file serves every language.
  var LANG = (document.documentElement.getAttribute('lang') || 'ru').slice(0, 2);
  var LABELS = {
    ru: { copy: 'Скопировать код', done: 'Скопировано', fail: 'Не удалось' },
    en: { copy: 'Copy code',       done: 'Copied',      fail: 'Failed' },
    uk: { copy: 'Скопіювати код',  done: 'Скопійовано', fail: 'Не вдалося' },
    de: { copy: 'Code kopieren',   done: 'Kopiert',     fail: 'Fehlgeschlagen' }
  };
  var label = LABELS[LANG] || LABELS.ru;

  // The fallback runs on any rejection, not on a missing API: file:// is a
  // secure context, so the clipboard exists there, yet writeText is still
  // refused without permission or focus.
  function fallbackCopy(text) {
    var area = document.createElement('textarea');
    area.value = text;
    area.setAttribute('readonly', '');
    // Moved off-screen rather than hidden: a hidden field cannot be selected,
    // and without a selection there is nothing to copy.
    area.style.position = 'fixed';
    area.style.left = '-9999px';
    area.style.top = '0';
    document.body.appendChild(area);
    area.select();
    var copied = false;
    try { copied = document.execCommand('copy'); } catch (e) { copied = false; }
    area.remove();
    return copied;
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).catch(function () {
        return fallbackCopy(text) ? Promise.resolve()
                                  : Promise.reject(new Error('both paths refused'));
      });
    }
    return fallbackCopy(text) ? Promise.resolve()
                              : Promise.reject(new Error('both paths refused'));
  }

  var blocks = document.querySelectorAll('pre > code');
  for (var i = 0; i < blocks.length; i++) {
    (function (code) {
      var pre = code.parentNode;
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'cp-btn';
      button.setAttribute('aria-label', label.copy);
      // An image, not a character: the typographic glyph rendered as an empty
      // box in standard fonts. Hidden from screen readers, which announce the
      // button's aria-label instead.
      button.innerHTML =
        '<svg class="cp-ico" aria-hidden="true" width="13" height="13" viewBox="0 0 16 16"'
        + ' fill="none" stroke="currentColor" stroke-width="1.6"'
        + ' stroke-linejoin="round">'
        + '<rect x="5.2" y="5.2" width="9" height="9" rx="1.6"/>'
        + '<path d="M10.8 2.5H3.3a1.6 1.6 0 0 0-1.6 1.6v7.5"/>'
        + '</svg>'
        + '<span class="cp-say" role="status"></span>';
      var status = button.querySelector('.cp-say');
      var timer = null;

      button.addEventListener('click', function () {
        // textContent, not innerHTML: exactly the visible text, with no markup.
        copyText(code.textContent).then(function () {
          respond(label.done, 'ok');
        }, function () {
          respond(label.fail, 'fail');
        });
      });

      function respond(message, state) {
        clearTimeout(timer);
        status.textContent = message;
        button.classList.add(state);
        timer = setTimeout(function () {
          status.textContent = '';
          button.classList.remove('ok', 'fail');
        }, 1500);
      }

      pre.appendChild(button);
    })(blocks[i]);
  }
})();
