// swa.js - Simple Web Architecture utilities: theme, font scale & dynamic in-page TOC
(function () {
  // 1. Theme: restore and toggle
  // Storage belongs to the origin, not to the folder, so every key carries the
  // site: swa-<site>-<key>. The site name is read from the markup, which keeps
  // this file byte-identical across every site of the series.
  const SITE = document.documentElement.dataset.site || 'swa';
  const key = (name) => 'swa-' + SITE + '-' + name;

  const savedTheme = localStorage.getItem(key('theme'));
  if (savedTheme) {
    document.documentElement.setAttribute('data-theme', savedTheme);
  }

  // Inline SVG for the same reason as every other icon: the sun and moon
  // characters are missing from many fonts and render as empty boxes.
  const icon = (name, body) => '<svg class="icon" data-icon="' + name + '"'
    + ' viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor"'
    + ' stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"'
    + ' aria-hidden="true">' + body + '</svg>';
  const SUN = icon('sun', '<circle cx="10" cy="10" r="3.8"/><path d="M10 1.2v2.2M10 16.6v2.2'
    + 'M1.2 10h2.2M16.6 10h2.2M3.7 3.7l1.6 1.6M14.7 14.7l1.6 1.6M16.3 3.7l-1.6 1.6'
    + 'M5.3 14.7l-1.6 1.6"/>');
  const MOON = icon('moon', '<path d="M16.4 12.6A7.4 7.4 0 0 1 7.4 3.6a7.4 7.4 0 1 0 9 9z"/>');

  const themeToggle = document.getElementById('themeToggle');
  function updateThemeUI() {
    if (!themeToggle) return;
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const isDark = currentTheme === 'dark' ||
      (!currentTheme && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
    const icon = themeToggle.querySelector('.theme-icon');
    if (icon) {
      icon.innerHTML = isDark ? MOON : SUN;
    }
  }

  if (themeToggle) {
    updateThemeUI();
    themeToggle.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme');
      const isDark = currentTheme === 'dark' ||
        (!currentTheme && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
      const nextTheme = isDark ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', nextTheme);
      localStorage.setItem(key('theme'), nextTheme);
      updateThemeUI();
    });
  }

  // 2. Font size: S / M / L
  const savedFont = localStorage.getItem(key('font')) || 'm';
  document.documentElement.setAttribute('data-font', savedFont);

  const fontBtns = document.querySelectorAll('.font-btn');
  function updateFontUI(activeSize) {
    fontBtns.forEach((btn) => {
      btn.classList.toggle('active', btn.getAttribute('data-size') === activeSize);
    });
  }
  updateFontUI(savedFont);

  fontBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      const size = btn.getAttribute('data-size');
      if (!size) return;
      document.documentElement.setAttribute('data-font', size);
      localStorage.setItem(key('font'), size);
      updateFontUI(size);
    });
  });

  // 3. Pinned header height. Anchor offset and sidebar position depend on it,
  //    and CSS cannot compute it: it follows the font size and the tagline.
  const header = document.querySelector('header.top');

  function fitHeader() {
    if (!header) return;
    const stuck = getComputedStyle(header).position === 'sticky';
    const height = stuck ? Math.round(header.getBoundingClientRect().height) : 0;
    document.documentElement.style.setProperty('--header-h', height + 'px');
  }

  // 4. In-page table of contents and scroll spy
  let fitNav = function () {};
  let markActive = function () {};

  const tocContainer = document.getElementById('pageToc');
  const tocList = document.getElementById('tocList');
  if (tocContainer && tocList) {
    const items = Array.from(document.querySelectorAll('main h2[id], main .glossary-term[id]'));
    if (items.length > 0) {
      tocList.innerHTML = '';
      items.forEach((item) => {
        const li = document.createElement('li');
        const a = document.createElement('a');
        a.href = '#' + item.id;
        // A term card keeps its title in a nested h2/h3; a section is its own title.
        const titleEl = item.matches('.glossary-term')
          ? item.querySelector('h2, h3')
          : item;
        const text = titleEl ? titleEl.cloneNode(true) : item.cloneNode(true);
        const anchor = text.querySelector('.anchor-link');
        if (anchor) anchor.remove();
        const obj = text.querySelector('.glossary-object');
        if (obj) obj.remove();
        a.textContent = text.textContent.trim();
        li.appendChild(a);
        tocList.appendChild(li);
      });
      // РАЗДЕЛЫ СТОЯТ ВНУТРИ ПУНКТА СВОЕЙ СТРАНИЦЫ. Отдельным блоком под всеми
      // пятнадцатью разделами они оказывались за кромкой панели: на окне 900px
      // первая ссылка лежала на 28px ниже видимой части, и навигатор, которым
      // пользуются постоянно, приходилось искать прокруткой. Словарь помечен
      // текущим вне списка, поэтому берётся ближайший li, а если его нет - сам
      // родитель ссылки.
      // У лендинга своего пункта в меню нет: он не входит в пятнадцать разделов.
      // Тогда разделы встают над списком - это страница, которую читают сейчас,
      // и её содержание важнее карты сайта, до которой ещё дойдут.
      const here = document.querySelector('nav.contents [aria-current="page"]');
      const host = here && (here.closest('li') || here.parentElement);
      const panel = document.querySelector('nav.contents');
      if (host) host.appendChild(tocContainer);
      else if (panel) panel.insertBefore(tocContainer, panel.firstElementChild);

      tocContainer.hidden = false;

      // Computed from position, not from IntersectionObserver: section is active
      // when its heading reaches the reading line just below the sticky header.
      // At the bottom of a page the last section is active by definition.
      markActive = function () {
        const stuck = header && getComputedStyle(header).position === 'sticky';
        const topOffset = stuck ? header.getBoundingClientRect().bottom : 0;
        const line = topOffset + 34;
        let current = items[0];
        for (const item of items) {
          if (item.getBoundingClientRect().top <= line) current = item;
        }
        const doc = document.scrollingElement || document.documentElement;
        if (doc.scrollTop + window.innerHeight >= doc.scrollHeight - 2) {
          current = items[items.length - 1];
        }
        tocList.querySelectorAll('a').forEach((link) => {
          link.classList.toggle('active', link.getAttribute('href') === '#' + current.id);
        });
        carryAnchor(current.id);
      };

      // Switching language keeps the place: anchors are identical in every
      // language, so the switcher only has to carry the current one. At the top
      // of a page the links stay clean; a language that lacks the section simply
      // opens at its beginning.
      function carryAnchor(id) {
        const doc = document.scrollingElement || document.documentElement;
        const keep = doc.scrollTop > 40;
        document.querySelectorAll('.lang-switcher a').forEach((link) => {
          const base = (link.getAttribute('href') || '').split('#')[0];
          link.setAttribute('href', keep ? base + '#' + id : base);
        });
      }

      // The sidebar is as tall as what is visible below it, not as the window:
      // otherwise its last items sit off screen while the header is still there.
      const nav = tocContainer.closest('nav.contents');

      fitNav = function () {
        if (!nav || getComputedStyle(nav).position !== 'sticky') {
          if (nav) nav.style.maxHeight = '';
          return;
        }
        const top = Math.max(nav.getBoundingClientRect().top, 0);
        nav.style.maxHeight = Math.max(240, Math.round(window.innerHeight - top - 18)) + 'px';
      };
    }
  }

  // 5. Search. The button lives in the tray; the panel and the index for this
  //    language are fetched on the first click, so a reader who never searches
  //    pays nothing for it.
  const FIND = { ru: 'Искать по сайту', en: 'Search the site',
                 uk: 'Шукати на сайті', de: 'Website durchsuchen' };
  const CLEAR_MARK = { ru: 'Снять подсветку найденных слов', en: 'Clear word highlighting',
                       uk: 'Зняти підсвічування знайдених слів', de: 'Wortmarkierung aufheben' };

  const tray = document.querySelector('.utility-tray');

  if (tray && document.querySelector('nav.contents')) {
    const langCode = document.documentElement.lang || 'ru';
    const label = FIND[langCode] || FIND.ru;
    const clearLabel = CLEAR_MARK[langCode] || CLEAR_MARK.ru;

    const clearBtn = document.createElement('button');
    clearBtn.type = 'button';
    clearBtn.className = 'clear-mark-btn';
    clearBtn.hidden = true;
    clearBtn.setAttribute('aria-label', clearLabel);
    clearBtn.title = clearLabel;
    clearBtn.innerHTML = '<svg class="icon" data-icon="clear-mark" viewBox="0 0 20 20" width="16"'
      + ' height="16" fill="none" stroke="currentColor" stroke-width="1.7"'
      + ' stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
      + '<path d="M12.5 3.5l4 4L8 16H4v-4L12.5 3.5z"/><path d="M3 18h14"/><path d="M14.5 11.5l3.5 3.5M18 11.5l-3.5 3.5"/></svg>';

    const find = document.createElement('button');
    find.type = 'button';
    find.className = 'find-btn';
    find.setAttribute('aria-label', label);
    find.title = label;
    find.innerHTML = '<svg class="icon" data-icon="find" viewBox="0 0 20 20" width="16"'
      + ' height="16" fill="none" stroke="currentColor" stroke-width="1.7"'
      + ' stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
      + '<circle cx="8.6" cy="8.6" r="5.4"/><path d="M12.6 12.6l4 4"/></svg>';

    const norm = (s) => s.toLowerCase().replace(/ё/g, 'е');

    function clearSearchHighlight(keepState) {
      document.querySelectorAll('mark.search-mark').forEach((m) => {
        const parent = m.parentNode;
        if (!parent) return;
        parent.replaceChild(document.createTextNode(m.textContent), m);
        parent.normalize();
      });
      clearBtn.hidden = true;
      if (!keepState) {
        try {
          const raw = sessionStorage.getItem(key('search'));
          if (raw) {
            const state = JSON.parse(raw);
            state.active = false;
            sessionStorage.setItem(key('search'), JSON.stringify(state));
          }
        } catch (_) {}
      }
    }

    function applySearchHighlight(anchorId, query) {
      clearSearchHighlight(true);
      const needle = norm((query || '').trim());
      if (!anchorId || needle.length < 2) return 0;
      const target = document.getElementById(anchorId);
      if (!target) return 0;

      const roots = [target];
      if (target.tagName === 'H2') {
        let sib = target.nextElementSibling;
        while (sib && sib.tagName !== 'H2' && !sib.classList.contains('glossary-term')) {
          roots.push(sib);
          sib = sib.nextElementSibling;
        }
      }

      let count = 0;
      roots.forEach((root) => {
        const nodes = [];
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        let n;
        while ((n = walker.nextNode())) {
          const p = n.parentElement;
          if (!p || p.closest('.anchor-link, script, style, mark.search-mark')) continue;
          if (norm(n.nodeValue).indexOf(needle) >= 0) nodes.push(n);
        }
        nodes.forEach((textNode) => {
          const text = textNode.nodeValue;
          const lower = norm(text);
          const frag = document.createDocumentFragment();
          let pos = 0;
          let at;
          while ((at = lower.indexOf(needle, pos)) >= 0) {
            if (at > pos) frag.appendChild(document.createTextNode(text.slice(pos, at)));
            const mark = document.createElement('mark');
            mark.className = 'search-mark';
            mark.textContent = text.slice(at, at + needle.length);
            frag.appendChild(mark);
            count++;
            pos = at + needle.length;
          }
          if (pos < text.length) frag.appendChild(document.createTextNode(text.slice(pos)));
          textNode.parentNode.replaceChild(frag, textNode);
        });
      });

      clearBtn.hidden = count === 0;
      return count;
    }

    clearBtn.addEventListener('click', () => clearSearchHighlight(false));
    window.applySearchHighlight = applySearchHighlight;
    window.clearSearchHighlight = clearSearchHighlight;

    try {
      const saved = JSON.parse(sessionStorage.getItem(key('search')) || 'null');
      if (saved && saved.active && saved.q) {
        const hashAnchor = location.hash ? decodeURIComponent(location.hash.slice(1)) : '';
        const savedAnchor = (saved.url && saved.url.includes('#')) ? saved.url.split('#')[1] : '';
        const anchor = hashAnchor || savedAnchor;
        if (anchor) applySearchHighlight(anchor, saved.q);
      }
    } catch (_) {}

    let loading = false;
    find.addEventListener('click', () => {
      if (window.openSearch) { window.openSearch(); return; }
      if (loading) return;
      loading = true;
      const lang = document.documentElement.lang || 'ru';
      load('../assets/search-' + lang + '.js', () => load('../assets/search.js', () => {
        loading = false;
      }));
    });
    tray.insertBefore(find, tray.firstChild);
    tray.insertBefore(clearBtn, find);
  }

  // A cached engine is a stale engine, so every asset URL carries ?v=N. The
  // number lives in one place, tools/build-nav.py, which writes it into the
  // page. The files loaded from here take it from the URL this very file
  // arrived by, so the number is never written twice.
  function stamp() {
    const self = document.querySelector('script[src*="swa.js?v="]');
    const query = self ? self.src.split('?v=')[1] : '';
    return query ? '?v=' + query : '';
  }

  function load(src, done) {
    const tag = document.createElement('script');
    tag.src = src + stamp();
    tag.onload = done;
    tag.onerror = done;
    document.head.appendChild(tag);
  }

  // Page size in words. The number is baked into the markup by
  // tools/build-meta.py, and this is only the stand-in: if the line is missing
  // altogether, it is counted here and written in. It never argues with a
  // number that is already there and never checks it - a stale number is the
  // generator's business, and ./check.sh catches it.
  const SIZE_SAY = { ru: 'Слов:', en: 'Words:', uk: 'Слів:', de: 'Wörter:' };
  const main = document.querySelector('main');
  if (main && !document.querySelector('.page-size')) {
    const copy = main.cloneNode(true);
    copy.querySelectorAll('.anchor-link, .pager').forEach((el) => el.remove());
    const words = copy.textContent.split(/\s+/).filter((w) => /[^\W_]/.test(w)).length;
    const line = document.createElement('p');
    line.className = 'page-size';
    line.setAttribute('data-words', String(words));
    line.textContent = (SIZE_SAY[document.documentElement.lang] || SIZE_SAY.ru) + ' ' + words;
    const h1 = main.querySelector('h1');
    if (h1 && h1.parentNode) h1.parentNode.insertBefore(line, h1.nextSibling);
  }

  // Phone: the menu used to hold the whole first screen - the page title began
  // at 901px on an 844px tall screen. It folds into one line that names the
  // current page and opens on a tap. On a wide screen the line does not exist:
  // the panel is sticky there and has room. The label comes from the nav's own
  // aria-label, so every language already has it.
  const panel = document.querySelector('nav.contents');
  if (panel && panel.querySelector('a')) {
    const fold = document.createElement('button');
    fold.type = 'button';
    fold.className = 'nav-fold';
    fold.setAttribute('aria-expanded', 'false');

    const here = panel.querySelector('[aria-current="page"]');
    const num = here && here.querySelector('.num');
    const title = here
      ? here.textContent.replace(num ? num.textContent : '', '').trim()
      : '';
    const say = document.createElement('span');
    say.className = 'nav-fold-say';
    say.textContent = (panel.getAttribute('aria-label') || '') + (title ? ' · ' + title : '');

    fold.appendChild(say);
    fold.insertAdjacentHTML('beforeend',
      arrow('fold', '<path d="M5 7.5l5 5 5-5"/>'));
    panel.insertBefore(fold, panel.firstChild);
    panel.classList.add('nav-folded');

    function setFolded(folded) {
      panel.classList.toggle('nav-folded', folded);
      fold.setAttribute('aria-expanded', String(!folded));
    }

    fold.addEventListener('click', () => setFolded(!panel.classList.contains('nav-folded')));

    // Касание ссылки оставляет читателя с текстом, а не с меню: и переход на
    // другую страницу, и прыжок по якорю внутри этой.
    panel.addEventListener('click', (event) => {
      if (event.target.closest('a')) setFolded(true);
    });
  }

  // 6. Floating scroll buttons: to the top and to the bottom. Paging by screen
  //    is left to the finger and the wheel. Built here, not in the markup, so
  //    no page has to be edited to gain them.
  const SAY = {
    ru: ['В начало страницы', 'В конец страницы'],
    en: ['To the top of the page', 'To the bottom of the page'],
    uk: ['На початок сторінки', 'У кінець сторінки'],
    de: ['Zum Anfang der Seite', 'Zum Ende der Seite'],
  };
  const LONG_ENOUGH = 1.5; // shorter than this many screens needs no buttons

  function arrow(name, body) {
    return '<svg class="icon" data-icon="' + name + '" viewBox="0 0 20 20" width="22"'
      + ' height="22" fill="none" stroke="currentColor" stroke-width="1.7"'
      + ' stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + body + '</svg>';
  }

  const floats = document.createElement('div');
  floats.className = 'floats';
  floats.hidden = true;

  const says = SAY[document.documentElement.lang] || SAY.ru;
  const steps = [
    [says[0], arrow('to-top', '<path d="M5 10.5l5-5 5 5"/><path d="M5 15l5-5 5 5"/>'), 0],
    [says[1], arrow('to-bottom', '<path d="M5 5l5 5 5-5"/><path d="M5 9.5l5 5 5-5"/>'), 1],
  ];

  steps.forEach(([label, svg, toEnd]) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'float-btn';
    btn.setAttribute('aria-label', label);
    btn.title = label;
    btn.innerHTML = svg;
    btn.addEventListener('click', () => {
      const doc = document.scrollingElement || document.documentElement;
      // Плавность - по желанию системы. У людей с вестибулярными нарушениями
      // плавная прокрутка вызывает головокружение, и это настройка системы, а
      // не вопрос вкуса: её читают, а не переспрашивают.
      const calm = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      window.scrollTo({ top: toEnd ? doc.scrollHeight : 0, behavior: calm ? 'auto' : 'smooth' });
    });
    floats.appendChild(btn);
  });

  document.body.appendChild(floats);

  function fitFloats() {
    const doc = document.scrollingElement || document.documentElement;
    floats.hidden = doc.scrollHeight < window.innerHeight * LONG_ENOUGH;
  }

  // 7. One handler for everything that depends on scrolling and window size,
  //    throttled to an animation frame to avoid forced layout on every event.
  let ticking = false;

  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(() => {
      ticking = false;
      fitHeader();
      fitNav();
      fitFloats();
      markActive();
    });
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  window.addEventListener('load', onScroll);
  fontBtns.forEach((btn) => btn.addEventListener('click', onScroll));

  // First pass runs now, not in the next frame: until that frame the stack is
  // still hidden and the sidebar unsized, which is what a checker reads.
  fitHeader();
  fitNav();
  fitFloats();
  markActive();
})();
