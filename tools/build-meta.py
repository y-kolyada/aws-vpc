"""Page metadata: the size in words and the links to the neighbouring topics.

    python3 tools/build-meta.py                  write it into the pages
    python3 tools/build-meta.py --check          tell whether the pages are stale
    python3 tools/build-meta.py --descriptions   list the descriptions for proof-reading

WHY IT IS BAKED AND NOT COUNTED IN THE BROWSER. A number written into the markup
is visible in the browser's reading mode, in print, to a search engine and to a
reader without JavaScript, and it does not jump into place after the paint. The
price is that it goes stale when the text changes, so --check is wired into
./check.sh: edit the text, forget to rebuild, and the check turns red.

WHAT COUNTS AS A WORD. Everything inside <main>, code blocks included: that is
what the reader scrolls through. The two blocks this tool writes are stripped
before counting - otherwise the count would feed on itself.

The chain of topics is index -> 01 .. 15 -> glossary. The landing has no
previous topic, the glossary has no next one, and no empty line is printed
there. Link text is the target page's own <h1>.
"""
import html
import json
import pathlib
import re
import sys

import siteconf

LANGS = ('ru', 'en', 'uk', 'de')
CHAIN = ['index'] + ['%02d' % n for n in range(1, 16)] + ['glossary']
if pathlib.Path('ru/navigator.html').exists():
    CHAIN.append('navigator')

SAY = {
    'ru': {'size': 'Слов:', 'next': 'Следующая тема:', 'prev': 'Предыдущая тема:',
           'nav': 'Соседние темы', 'home': 'Посадочная страница',
           'footer': 'Сайт серии AI Factory. Сделан той же оснасткой, что и остальные: обычный HTML и CSS, проверка на bash, публикация через GitHub Pages.'},
    'en': {'size': 'Words:', 'next': 'Next topic:', 'prev': 'Previous topic:',
           'nav': 'Neighbouring topics', 'home': 'Landing page',
           'footer': 'An AI Factory series site. Built with the same harness: plain HTML and CSS, checked with bash, published via GitHub Pages.'},
    'uk': {'size': 'Слів:', 'next': 'Наступна тема:', 'prev': 'Попередня тема:',
           'nav': 'Сусідні теми', 'home': 'Посадкова сторінка',
           'footer': 'Сайт серії AI Factory. Зроблений тим самим оснащенням: звичайний HTML і CSS, перевірка на bash, публікація через GitHub Pages.'},
    'de': {'size': 'Wörter:', 'next': 'Nächstes Thema:', 'prev': 'Vorheriges Thema:',
           'nav': 'Benachbarte Themen', 'home': 'Landingpage',
           'footer': 'Eine Website der AI Factory-Serie. Mit denselben Werkzeugen erstellt: einfaches HTML und CSS, Bash-Prüfung, Veröffentlichung über GitHub Pages.'},
}

# Живой адрес сайта - одной константой. Канонический адрес, который не
# отвечает, выбрасывает страницу из индекса, поэтому здесь стоит то, что
# отдаётся сегодня. Переезд на свой домен - правка этой строки и пересборка.
CONF = siteconf.conf()
SITE = CONF['url']
SITE_NAME = CONF['name']
LOCALE = {'ru': 'ru_RU', 'en': 'en_US', 'uk': 'uk_UA', 'de': 'de_DE'}
HEAD_OPEN = '<!-- meta: built by tools/build-meta.py - do not edit by hand -->'
HEAD_SHUT = '<!-- /meta -->'

MAIN = re.compile(r'<main.*?</main>', re.S)
LEAD = re.compile(r'<p class="lead"[^>]*>(.*?)</p>', re.S)
# Ищется по форме, а не по тексту маркера: если текст однажды поменять, блок
# со старым текстом перестал бы опознаваться, и генератор дописал бы вторую
# голову вместо замены первой. Поймано ровно так.
HEAD_BLOCK = re.compile(r'\n?<!-- meta:.*?<!-- /meta -->', re.S)
QA_ITEM = re.compile(r'<li>(.*?)</li>', re.S)
QA_LIST = re.compile(r'<ol class="qa"[^>]*>(.*?)</ol>', re.S)
TERM = re.compile(r'<div class="glossary-term" id="([^"]+)">(.*?)</div>\s*</div>', re.S)
TERM_NAME = re.compile(r'<span class="glossary-title">(.*?)</span>', re.S)
TERM_LEAD = re.compile(r'<p class="glossary-lead">(.*?)</p>', re.S)
H1 = re.compile(r'<h1[^>]*>(.*?)</h1>', re.S)
# Заголовок вкладки собирается из <h1> по тому же канону, что ставит new-site.py:
# «<h1> · имя сайта · ai|». Без этого переименование раздела меняло og:title и
# схему, но оставляло вкладку, закладку и выдачу поиска со старым названием, и
# ни одна проверка не возражала (находка 6 сайта devops-kubernetes).
TITLE_TAG = re.compile(r'<title>.*?</title>', re.S)
SIZE_BLOCK = re.compile(r'\n?[ \t]*<p class="page-size".*?</p>', re.S)
PAGER_BLOCK = re.compile(r'\n?[ \t]*<nav class="pager".*?</nav>', re.S)
FOOTER_BLOCK = re.compile(r'\s*<footer\b[^>]*>.*?</footer>', re.S)
ANCHOR = re.compile(r'<a class="anchor-link".*?</a>', re.S)
TAG = re.compile(r'<[^>]+>')
WORD = re.compile(r'[^\W_]', re.UNICODE)


def plain(markup):
    return html.unescape(TAG.sub(' ', markup))


def title(page):
    text = pathlib.Path(page).read_text(encoding='utf-8')
    found = H1.search(text)
    return re.sub(r'\s+', ' ', plain(found.group(1))).strip() if found else ''


def count_words(text):
    body = MAIN.search(text)
    if not body:
        return 0
    inner = SIZE_BLOCK.sub('', body.group(0))
    inner = PAGER_BLOCK.sub('', inner)
    inner = FOOTER_BLOCK.sub('', inner)
    inner = ANCHOR.sub(' ', inner)
    return sum(1 for w in re.split(r'\s+', plain(inner)) if WORD.search(w))


def one_line(markup):
    """Текст без разметки, в одну строку.

    Снятый тег оставляет пробел, и перед знаком препинания он виден: «bash ?».
    Поэтому пробел перед точкой, запятой и прочими знаками убирается.
    """
    text = re.sub(r'\s+', ' ', plain(markup)).strip()
    return re.sub(r'\s+([.,;:!?»)])', r'\1', text)


def description(text):
    """Описание страницы - первое предложение лида, не длиннее 160 знаков.

    Лид написан ровно для этого: он говорит, о чём страница, одним абзацем.
    Если первое предложение длиннее 160 знаков, оно режется по границе слова -
    поисковик всё равно обрежет, но лучше обрезать осмысленно.
    """
    found = LEAD.search(text)
    if not found:
        return ''
    lead = one_line(found.group(1))
    first = re.split(r'(?<=[.!?])\s+', lead)[0]
    if len(first) <= 160:
        return first
    cut = first[:160].rsplit(' ', 1)[0]
    return cut.rstrip(' ,;:-') + '...'


def questions(text):
    """Пары «вопрос - ответ» со страницы банка.

    Строка «Зачем спрашивают» в ответ не идёт: это замечание автора читателю,
    а не ответ на вопрос.
    """
    out = []
    for block in QA_LIST.findall(text):
        for item in QA_ITEM.findall(block):
            ask = re.search(r'<strong>(.*?)</strong>', item, re.S)
            if not ask:
                continue
            rest = item[item.index('</strong>') + len('</strong>'):]
            rest = re.split(r'<span class="dim">', rest)[0]
            answer = one_line(rest)
            if answer:
                out.append((one_line(ask.group(1)), answer))
    return out


def terms(text):
    """Термины словаря: имя и первая фраза определения."""
    out = []
    for term_id, body in TERM.findall(text):
        name = TERM_NAME.search(body)
        lead = TERM_LEAD.search(body)
        if name and lead:
            out.append((term_id, one_line(name.group(1)), one_line(lead.group(1))))
    return out


def schema(lang, name, title, desc, url, text):
    """Разметка смысла по виду страницы. Одна схема на страницу, не больше."""
    if name == 'index':
        data = {'@context': 'https://schema.org', '@type': 'WebSite',
                'name': SITE_NAME, 'url': SITE, 'inLanguage': lang,
                'description': desc}
    elif name in ('13', '14', '15') and questions(text):
        # На заглушке вопросов нет, и FAQPage с пустым списком был бы ложью:
        # такая страница размечается как обычная статья.
        pairs = questions(text)
        data = {'@context': 'https://schema.org', '@type': 'FAQPage',
                'inLanguage': lang,
                'mainEntity': [{'@type': 'Question', 'name': ask,
                                'acceptedAnswer': {'@type': 'Answer', 'text': answer}}
                               for ask, answer in pairs]}
    elif name == 'glossary' and terms(text):
        data = {'@context': 'https://schema.org', '@type': 'DefinedTermSet',
                'name': title, 'url': url, 'inLanguage': lang,
                'hasDefinedTerm': [{'@type': 'DefinedTerm', 'name': term,
                                    'description': lead, 'url': url + '#' + term_id}
                                   for term_id, term, lead in terms(text)]}
    else:
        data = {'@context': 'https://schema.org', '@type': 'TechArticle',
                'headline': title, 'description': desc, 'url': url,
                'inLanguage': lang, 'isPartOf': {'@type': 'WebSite', 'name': SITE_NAME,
                                                 'url': SITE}}
    return json.dumps(data, ensure_ascii=False, separators=(',', ':'))


def head_block(lang, name, title, text):
    """Голова страницы: что о ней знает поисковик и мессенджер."""
    desc = description(text)
    url = '%s%s/%s.html' % (SITE, lang, name)
    esc = lambda s: html.escape(s, quote=True)
    rows = [HEAD_OPEN,
            '<meta name="description" content="%s">' % esc(desc),
            '<link rel="canonical" href="%s">' % url]
    for other in LANGS:
        rows.append('<link rel="alternate" hreflang="%s" href="%s%s/%s.html">'
                    % (other, SITE, other, name))
    rows.append('<link rel="alternate" hreflang="x-default" href="%s">' % SITE)
    rows += ['<meta property="og:type" content="%s">'
             % ('website' if name == 'index' else 'article'),
             '<meta property="og:site_name" content="%s">' % SITE_NAME,
             '<meta property="og:title" content="%s">' % esc(title),
             '<meta property="og:description" content="%s">' % esc(desc),
             '<meta property="og:url" content="%s">' % url,
             '<meta property="og:locale" content="%s">' % LOCALE[lang],
             '<meta name="twitter:card" content="summary">',
             '<link rel="icon" href="../assets/img/favicon.svg" type="image/svg+xml">',
             '<script type="application/ld+json">%s</script>'
             % schema(lang, name, title, desc, url, text),
             HEAD_SHUT]
    return '\n'.join(rows)


def size_line(lang, words):
    return ('\n    <p class="page-size" data-words="%d">%s %d</p>'
            % (words, SAY[lang]['size'], words))


def pager_block(lang, prev_page, next_page, titles):
    say = SAY[lang]
    rows = []
    if next_page:
        rows.append('        <p class="pager-next">%s <a href="%s.html">%s</a></p>'
                    % (say['next'], next_page, titles[next_page]))
    if prev_page:
        rows.append('        <p class="pager-prev">%s <a href="%s.html">%s</a></p>'
                    % (say['prev'], prev_page, titles[prev_page]))
    if not rows:
        return ''
    return ('\n      <nav class="pager" aria-label="%s">\n%s\n      </nav>'
            % (say['nav'], '\n'.join(rows)))


def rebuild(lang, name, titles):
    page = '%s/%s.html' % (lang, name)
    text = pathlib.Path(page).read_text(encoding='utf-8')

    text = SIZE_BLOCK.sub('', text)
    text = PAGER_BLOCK.sub('', text)
    text = FOOTER_BLOCK.sub('', text)
    text = HEAD_BLOCK.sub('', text)

    spot = CHAIN.index(name)
    prev_page = CHAIN[spot - 1] if spot > 0 else None
    next_page = CHAIN[spot + 1] if spot + 1 < len(CHAIN) else None
    pager = pager_block(lang, prev_page, next_page, titles)

    words = count_words(text)
    text = re.sub(r'(</h1>)', lambda m: m.group(1) + size_line(lang, words), text, count=1)

    if pager and '<div class="stub-card">' not in text:
        footer_text = CONF.get('footer') if (CONF.get('footer') and lang == 'ru') else SAY[lang]['footer']
        footer_html = ('\n\n    <footer>' + pager + '\n'
                       '      <p class="footer-note">' + footer_text + '</p>\n    </footer>')
        text = text.replace('</main>', footer_html + '\n  </main>', 1)

    # Голова страницы собирается последней: описание берётся из лида, а схема
    # FAQPage - из вопросов, то есть из уже готового тела.
    heading = title(page)
    text = TITLE_TAG.sub(
        lambda m: '<title>%s · %s · ai|</title>' % (html.escape(heading, quote=False), SITE_NAME),
        text, count=1)
    head = head_block(lang, name, heading, text)
    text = text.replace('</title>', '</title>\n' + head, 1)
    return page, text


KINDS = [
    ('разбор темы (01-09)', ['%02d' % n for n in range(1, 10)]),
    ('примеры (10-12)', ['10', '11', '12']),
    ('банк вопросов (13-15)', ['13', '14', '15']),
    ('словарь', ['glossary']),
    ('посадочная', ['index']),
]


def report_sizes(sizes):
    """Отчёт, а не вердикт: на зелёное и красное эти числа не влияют.

    Ориентир полезен одним: страница, заметно вылезшая за него, чаще всего
    содержит две темы вместо одной. Это повод посмотреть на неё, а не повод
    резать текст.
    """
    print()
    print('  Объём страниц в словах - ориентир, на вердикт не влияет')
    print('  ' + '-' * 54)
    print('  %-24s %s' % ('вид страницы', ' '.join('%9s' % lang for lang in LANGS)))
    for name, pages in KINDS:
        cells = []
        for lang in LANGS:
            got = sorted(sizes[lang][page] for page in pages)
            cells.append('%9s' % ('%d-%d' % (got[0], got[-1]) if got[0] != got[-1] else got[0]))
        print('  %-24s %s' % (name, ' '.join(cells)))
    print('  ' + '-' * 54)


def audit(sizes):
    """Что проверка смотрит кроме свежести: схема разбирается, числа сходятся.

    Генератор строит схему из самой страницы, поэтому расхождение означает, что
    разметка страницы ушла от того, что генератор умеет читать, - например,
    вопросы стали записываться иначе. Это сигнал, а не придирка.
    """
    trouble = []
    for lang in LANGS:
        for name in CHAIN:
            page = '%s/%s.html' % (lang, name)
            text = pathlib.Path(page).read_text(encoding='utf-8')
            found = re.search(r'<script type="application/ld\+json">(.*?)</script>', text, re.S)
            if not found:
                trouble.append('%s: разметки смысла нет' % page)
                continue
            try:
                data = json.loads(found.group(1))
            except ValueError as e:
                trouble.append('%s: разметка смысла не разбирается: %s' % (page, e))
                continue
            if data.get('@type') == 'FAQPage':
                on_page = sum(len(QA_ITEM.findall(block)) for block in QA_LIST.findall(text))
                if len(data['mainEntity']) != on_page:
                    trouble.append('%s: вопросов в схеме %d, на странице %d'
                                   % (page, len(data['mainEntity']), on_page))
            if data.get('@type') == 'DefinedTermSet':
                on_page = len(TERM.findall(text))
                if len(data['hasDefinedTerm']) != on_page:
                    trouble.append('%s: терминов в схеме %d, на странице %d'
                                   % (page, len(data['hasDefinedTerm']), on_page))
            found = re.search(r'<meta name="description" content="([^"]*)">', text)
            # Заглушке описание взять негде: лида на ней нет. Это не дефект,
            # а состояние - ровно как схема TechArticle вместо FAQPage на
            # странице без вопросов.
            if not (found and found.group(1)) and 'stub-card' not in text:
                trouble.append('%s: описание пустое' % page)
            if '<footer' not in text and 'stub-card' not in text:
                trouble.append('%s: подвала (<footer>) нет' % page)
    return trouble


def write_sitemap(check):
    """Карта сайта: все страницы четырёх языков и корневая дверь.

    Без дат изменения: они менялись бы при каждой правке, а карта - список
    адресов, а не журнал.
    """
    rows = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
            '  <url><loc>%s</loc></url>' % SITE]
    for lang in LANGS:
        for name in CHAIN:
            rows.append('  <url><loc>%s%s/%s.html</loc></url>' % (SITE, lang, name))
    rows.append('</urlset>')
    body = '\n'.join(rows) + '\n'
    path = pathlib.Path('sitemap.xml')
    before = path.read_text(encoding='utf-8') if path.exists() else ''
    if body == before:
        return False
    if not check:
        path.write_text(body, encoding='utf-8')
    return True


def report_descriptions():
    """Все описания страниц одним списком: что о странице прочтут в выдаче.

    Описание живёт не на странице, а рядом с ней: в выдаче поисковика и в
    карточке мессенджера оно стоит без текста, картинок и заголовков раздела.
    Поэтому его вычитывают отдельно, и этот список - рабочий лист вычитки.

    Три состояния считаются дефектом: пусто, длиннее 160 знаков и обрезано
    по границе слова. Обрезка правится в лиде, а не здесь: генератор берёт
    первое предложение лида, и если оно не укладывается в 160 знаков, коротким
    должно стать предложение.

    У заглушки лида нет, брать описание негде - она только считается.

    Описание считается из лида, а не читается из собранной головы: правка лида
    видна в этом списке сразу, без пересборки страниц. Свежесть самой головы -
    дело --check.
    """
    rows = []
    for lang in LANGS:
        for name in CHAIN:
            page = '%s/%s.html' % (lang, name)
            text = pathlib.Path(page).read_text(encoding='utf-8')
            desc = description(text)
            stub = 'stub-card' in text
            if stub:
                flaw = ''
            elif not desc:
                flaw = 'пусто'
            elif desc.endswith('...'):
                flaw = 'обрезано'
            elif len(desc) > 160:
                flaw = 'длинно'
            else:
                flaw = ''
            rows.append((page, desc, stub, flaw))

    print()
    print('  Описания страниц: что о странице прочтут в выдаче')
    print('  ' + '-' * 46)
    for page, desc, stub, flaw in rows:
        if stub:
            print('  [ --- ] %-16s заглушка, лида нет' % page)
            continue
        print('  [ %s ] %-16s %3d знаков%s'
              % ('ДА ' if not flaw else 'НЕТ', page, len(desc),
                 '' if not flaw else ', ' + flaw))
        print('          %s' % desc)
    print('  ' + '-' * 46)
    live = [r for r in rows if not r[2]]
    bad = [r for r in live if r[3]]
    print('  описаний: %d, заглушек: %d, с дефектом: %d'
          % (len(live), len(rows) - len(live), len(bad)))
    if bad:
        for page, desc, stub, flaw in bad:
            print('        -> %s: %s' % (page, flaw))
        print('  обрезка и длина правятся в лиде: первое предложение лида')
        print('  должно укладываться в 160 знаков')
        print('  ' + '-' * 46)
        print('  \033[31mКРАСНОЕ\033[0m')
        print()
        return 1
    print('  ' + '-' * 46)
    print('  \033[32mЗЕЛЁНОЕ\033[0m')
    print()
    return 0


def main():
    if '--descriptions' in sys.argv:
        return report_descriptions()
    check = '--check' in sys.argv
    stale = []
    done = 0
    sizes = {lang: {} for lang in LANGS}
    for lang in LANGS:
        titles = {name: title('%s/%s.html' % (lang, name)) for name in CHAIN}
        # Заголовок лендинга - предложение, в ссылке оно нечитаемо.
        titles['index'] = SAY[lang]['home']
        for name in CHAIN:
            page, text = rebuild(lang, name, titles)
            sizes[lang][name] = count_words(text)
            before = pathlib.Path(page).read_text(encoding='utf-8')
            if text == before:
                continue
            if check:
                stale.append(page)
            else:
                pathlib.Path(page).write_text(text, encoding='utf-8')
                done += 1

    if write_sitemap(check) and check:
        stale.append('sitemap.xml')

    print()
    print('  Данные страниц: голова, объём, соседние темы')
    print('  ' + '-' * 46)
    if check:
        if stale:
            print('  устарело страниц: %d' % len(stale))
            for page in stale[:8]:
                print('        -> %s' % page)
            if len(stale) > 8:
                print('        -> ... и ещё %d' % (len(stale) - 8))
            print('  пересобрать: python3 tools/build-meta.py')
            print('  ' + '-' * 46)
            print('  \033[31mКРАСНОЕ\033[0m')
            print()
            return 1
        trouble = audit(sizes)
        if trouble:
            print('  разметка разошлась со страницей: %d' % len(trouble))
            for line in trouble[:8]:
                print('        -> %s' % line)
            print('  ' + '-' * 46)
            print('  \033[31mКРАСНОЕ\033[0m')
            print()
            return 1
        print('  страниц в порядке: %d' % (len(LANGS) * len(CHAIN)))
        print('  ' + '-' * 46)
        print('  \033[32mЗЕЛЁНОЕ\033[0m')
        report_sizes(sizes)
        print()
        return 0
    print('  страниц переписано: %d из %d' % (done, len(LANGS) * len(CHAIN)))
    print('  ' + '-' * 46)
    report_sizes(sizes)
    print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
