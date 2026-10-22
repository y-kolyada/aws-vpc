#!/usr/bin/env python3
"""Page shell: asset paths, links between languages, inline icons.

Header, navigation and the language switcher must be identical on every page.
By hand that does not hold: one forgotten page and a reader lands in a 404 or
loses the copy button. The mechanics live in this script so they can be run
again after any move or new page.

    python3 tools/build-nav.py              every language
    python3 tools/build-nav.py ru en        these folders only
    python3 tools/build-nav.py --relink en  repoint cross-page anchors
    python3 tools/build-nav.py --migrate    one-off rule for the folder move

Idempotent: a second run changes nothing.

--migrate adds the rule that only held while pages lived in a flat root, where
a name without a language suffix meant the Russian page. It switches itself off
on a page that already moved, because a second run with it would otherwise
repoint every non-Russian navigation link at the Russian pages.

What it rewrites: asset paths into ../assets/; links between pages, where the
filename is the same in every language and the folder carries the language;
links to lesson files in lessons/; and icons, as inline SVG rather than emoji,
which render as empty boxes without an emoji font.

Output is Russian: it speaks to the person who accepts the work.
"""

import os
import re
import sys

import siteconf

LANGS = ('ru', 'en', 'uk', 'de')

# Доступность, которую нельзя сделать стилями: ссылка в начало содержания и
# язык у ссылок переключателя. Подписи - на языке страницы, имя языка - на
# самом языке: читалка произносит их по его правилам, а не по правилам текущего.
SKIP = {'ru': 'К содержанию', 'en': 'Skip to content',
        'uk': 'До змісту', 'de': 'Zum Inhalt springen'}
LANG_NAME = {'ru': 'Русский', 'en': 'English', 'uk': 'Українська', 'de': 'Deutsch'}
LANG_GROUP = {'ru': 'Язык страницы', 'en': 'Page language',
              'uk': 'Мова сторінки', 'de': 'Seitensprache'}
SKIP_LINK = re.compile(r'\s*<a class="skip"[^>]*>.*?</a>', re.S)
SWITCHER = re.compile(r'<(div|nav) class="lang-switcher"[^>]*>(.*?)</\1>', re.S)
SWITCH_LINK = re.compile(r'<a ([^>]*?)href="([^"]+)"([^>]*)>(.*?)</a>', re.S)
ASSETS = ('style.css', 'swa.js', 'terms.js', 'cp.js')
NAV_ITEM = re.compile(r'(<nav class="contents"[^>]*>.*?</nav>)', re.S | re.I)
NAV_LINK = re.compile(r'(<a\b[^>]*href="(?:\.\./\w\w/)?(\d\d)\.html"[^>]*>)(.*?)(</a>)', re.S | re.I)

# Версия оснастки в ссылке. Браузер кэширует файл по адресу, а адрес без
# версии не меняется, когда меняется файл: вернувшийся читатель получает
# старый движок. Номер равен номеру релиза и стоит здесь один раз - в
# страницах его пишет генератор, а загрузчик индекса поиска берёт его из
# адреса, по которому пришёл сам swa.js.
CONF = siteconf.conf()
VERSION = int(CONF['version'])
# Имя сайта стоит в разметке, а не в движке: тогда assets/swa.js одинаков на
# всех сайтах серии, а ключи хранилища всё равно остаются своими -
# swa-<сайт>-*. Ставит его генератор, поэтому потеряться оно не может.
HTML_TAG = re.compile(r'<html lang="(\w+)"[^>]*>')
ASSET_LINK = re.compile(r'((?:href|src)="(?:\.\./)?assets/(?:%s))(?:\?v=[0-9]+)?"'
                        % '|'.join(a.replace('.', r'\.') for a in ASSETS))
PAGE = re.compile(r'(?P<attr>href=")(?P<name>index|glossary|navigator|[0-9]{2})(?:-(?P<lang>en|uk|de))?\.html')
LESSON = re.compile(r'(href=")((?:step|record|notes)-[0-9]+\.md|backlog\.md)"')

# Icons live here, not in the pages: each one carries data-icon, so the shape
# can be redrawn everywhere at once. The drawing fills its box, or the icon
# reads as a superscript next to text.
def icon(name, body):
    return ('<svg class="icon" data-icon="%s" viewBox="0 0 20 20" width="16" height="16" '
            'fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
            'stroke-linejoin="round" aria-hidden="true">%s</svg>' % (name, body))


BOOK = icon('book',
            '<path d="M2.6 3.8h4.8a2.6 2.6 0 0 1 2.6 2.6v10a2.2 2.2 0 0 0-2.2-1.8H2.6z"/>'
            '<path d="M17.4 3.8h-4.8a2.6 2.6 0 0 0-2.6 2.6v10a2.2 2.2 0 0 1 2.2-1.8h5.2z"/>')
TARGET = icon('target',
              '<circle cx="10" cy="10" r="7.4"/><circle cx="10" cy="10" r="3.6"/>'
              '<circle cx="10" cy="10" r="0.7" fill="currentColor"/>')
SUN = icon('sun',
           '<circle cx="10" cy="10" r="3.8"/><path d="M10 1.2v2.2M10 16.6v2.2M1.2 10h2.2'
           'M16.6 10h2.2M3.7 3.7l1.6 1.6M14.7 14.7l1.6 1.6M16.3 3.7l-1.6 1.6'
           'M5.3 14.7l-1.6 1.6"/>')
ICONS = {'book': BOOK, 'target': TARGET, 'sun': SUN}
REDRAW = re.compile(r'<svg class="icon".*?</svg>', re.S)


def which(svg):
    """Which icon this is: by data-icon, or for older markup by its drawing -
    two paths and no circles is a book, three circles a target, both a sun."""
    mark = re.search(r'data-icon="([a-z]+)"', svg)
    if mark:
        return mark.group(1) if mark.group(1) in ICONS else None
    circles, paths = svg.count('<circle'), svg.count('<path')
    if circles and paths:
        return 'sun'
    if circles:
        return 'target'
    return 'book' if paths == 2 else None


def accessible(text, lang):
    """Две правки, которые видит только тот, кто ими пользуется."""
    count = 0

    # 1. Ссылка «к содержанию» - первая в порядке обхода, и у main есть якорь.
    text = SKIP_LINK.sub('', text)
    if '<main' in text:
        if re.search(r'<main(?![^>]*\bid=)', text):
            text = re.sub(r'<main\b', '<main id="main"', text, count=1)
            count += 1
        link = '\n<a class="skip" href="#main">%s</a>' % SKIP[lang]
        text = text.replace('<body>', '<body>' + link, 1)
        count += 1

    # 2. Переключатель языков: область с подписью, у ссылок язык и имя языка.
    def switcher(m):
        inner = m.group(2)

        def link(one):
            href = one.group(2)
            other = re.search(r'\.\./(\w\w)/', href)
            code = other.group(1) if other else lang
            keep = (one.group(1) + one.group(3)).replace('\n', ' ')
            keep = re.sub(r'\s*(lang|hreflang|aria-label|aria-current)="[^"]*"', '', keep)
            keep = re.sub(r'\s*class="[^"]*"', '', keep).strip()
            if code == lang:
                keep = ('class="active" aria-current="page" ' + keep).strip()
            keep = (' ' + keep) if keep else ''
            return ('<a href="%s" lang="%s" hreflang="%s" aria-label="%s"%s>%s</a>'
                    % (href, code, code, LANG_NAME[code], keep, code.upper()))

        return ('<nav class="lang-switcher" aria-label="%s">%s</nav>'
                % (LANG_GROUP[lang], SWITCH_LINK.sub(link, inner)))

    text, switched = SWITCHER.subn(switcher, text, count=1)
    return text, count + switched


def version(text, counts):
    """Номер версии во всех ссылках на оснастку этой страницы."""
    def stamp(found):
        link = '%s?v=%d"' % (found.group(1), VERSION)
        if link != found.group(0):
            counts['version'] += 1
        return link
    return ASSET_LINK.sub(stamp, text)


def number_nav(text, counts):
    """Каждый из 15 разделов в навигаторе несёт <span class="num">N</span>.

    Стили отключают стандартную нумерацию списка ol, чтобы номер стоял
    приглушённым и фиксированной ширины. Если номер потерялся при правке,
    генератор возвращает его на место."""
    def fix_nav(nav_match):
        nav_block = nav_match.group(1)

        def fix_link(m):
            num = int(m.group(2))
            open_tag = m.group(1)
            inner = m.group(3)
            close_tag = m.group(4)
            clean = re.sub(r'^\s*<span class="num">\d+</span>\s*', '', inner)
            new_inner = '<span class="num">%d</span>%s' % (num, clean)
            if new_inner != inner:
                counts['nav_num'] = counts.get('nav_num', 0) + 1
            return open_tag + new_inner + close_tag

        return NAV_LINK.sub(fix_link, nav_block)

    return NAV_ITEM.sub(fix_nav, text)


def current_nav(text, page_name, counts):
    """Активная ссылка текущей страницы в навигаторе несёт aria-current="page".

    Движок swa.js опирается на этот атрибут для размещения вложенного оглавления
    #pageToc. На посадочной странице активного пункта в навигаторе нет.
    """
    def fix_nav(nav_match):
        nav_block = nav_match.group(1)
        cleaned = re.sub(r'\s+aria-current="page"', '', nav_block)

        if page_name and page_name != 'index.html':
            pattern = re.compile(r'(<a\b[^>]*\bhref="%s"[^>]*)>' % re.escape(page_name))
            cleaned = pattern.sub(r'\1 aria-current="page">', cleaned, count=1)

        if cleaned != nav_block:
            counts['nav_current'] = counts.get('nav_current', 0) + 1
        return cleaned

    return NAV_ITEM.sub(fix_nav, text)


def rewrite(text, lang, migrate=False, page_name=''):
    counts = {'assets': 0, 'pages': 0, 'lessons': 0, 'icons': 0, 'access': 0, 'version': 0,
              'site': 0, 'nav_num': 0, 'nav_current': 0}

    def house(found):
        tag = '<html lang="%s" data-site="%s">' % (found.group(1), CONF['key'])
        if tag != found.group(0):
            counts['site'] += 1
        return tag
    text = HTML_TAG.sub(house, text, count=1)
    if '../assets/' in text:
        migrate = False  # page already moved, the one-off rule is done

    for name in ASSETS:
        for attr in ('href', 'src'):
            before = text
            text = text.replace('%s="%s' % (attr, name), '%s="../assets/%s' % (attr, name))
            if text != before:
                counts['assets'] += 1

    def page(m):
        other = m.group('lang')
        name = m.group('name')
        attr = m.group('attr')
        if other is None:
            if lang == 'ru' or not migrate:
                return m.group(0)
            counts['pages'] += 1
            return '%s../ru/%s.html' % (attr, name)
        counts['pages'] += 1
        if other == lang:
            return '%s%s.html' % (attr, name)
        return '%s../%s/%s.html' % (attr, other, name)

    text = PAGE.sub(page, text)

    # The small-font button was labelled with a Cyrillic A: same glyph, wrong
    # alphabet, and the only Cyrillic character on an English page.
    before_font = text
    text = re.sub(r'(class="font-btn font-s"[^>]*>)\u0410(</button>)', r'\1A\2', text)
    if text != before_font:
        counts['icons'] += 1

    # A link to a folder lists the folder when the page is opened from the
    # file system, so the path is always explicit.
    before_dir = text
    text = text.replace('href="./"', 'href="index.html"')
    if text != before_dir:
        counts['pages'] += 1

    def lesson(m):
        counts['lessons'] += 1
        return '%s../lessons/%s"' % (m.group(1), m.group(2))

    text = LESSON.sub(lesson, text)

    for emoji, svg in (('📖', BOOK), ('🎯', TARGET), ('☼', SUN), ('☾', SUN)):
        counts['icons'] += text.count(emoji)
        text = text.replace(emoji, svg)

    def redraw(m):
        name = which(m.group(0))
        if name is None:
            return m.group(0)
        fresh = ICONS[name]
        if fresh != m.group(0):
            counts['icons'] += 1
        return fresh

    text = REDRAW.sub(redraw, text)

    text, fixed = accessible(text, lang)
    counts['access'] = fixed

    text = number_nav(text, counts)

    text = current_nav(text, page_name, counts)

    text = version(text, counts)
    return text, counts


ANCHOR_LINK = re.compile(r'href="(?:\.\./ru/)?(index|glossary|navigator|[0-9]{2})\.html#([A-Za-z0-9_-]+)"')


def anchors_of(path):
    if path not in anchors_of.cache:
        try:
            with open(path, encoding='utf-8') as handle:
                anchors_of.cache[path] = set(re.findall(r'\bid="([^"]+)"', handle.read()))
        except OSError:
            anchors_of.cache[path] = set()
    return anchors_of.cache[path]


anchors_of.cache = {}


def cross_links(text, lang):
    """A section link points where that section exists.

    While a page is still a stub it has no anchors, so a cross-page link
    dangles. Until then the link points at the Russian page, and it returns to
    its own language as soon as the anchor appears there.
    """
    moved = [0]

    def fix(m):
        page, anchor = m.group(1), m.group(2)
        here = anchors_of(os.path.join(lang, page + '.html'))
        if anchor in here:
            link = 'href="%s.html#%s"' % (page, anchor)
        else:
            link = 'href="../ru/%s.html#%s"' % (page, anchor)
        if link != m.group(0):
            moved[0] += 1
        return link

    return ANCHOR_LINK.sub(fix, text), moved[0]


def main(argv):
    args = [a for a in argv[1:] if not a.startswith('--')]
    migrate = '--migrate' in argv[1:]
    relink = '--relink' in argv[1:]
    check_only = '--check' in argv[1:]
    roots = [d for d in (args or LANGS) if os.path.isdir(d)]
    if not roots:
        print('нет папок языков - запускайте из корня репозитория')
        return 2

    total = {'files': 0, 'touched': 0, 'assets': 0, 'pages': 0, 'lessons': 0, 'icons': 0,
             'access': 0, 'version': 0, 'site': 0, 'nav_num': 0, 'nav_current': 0}
    for lang in roots:
        for name in sorted(os.listdir(lang)):
            if not name.endswith('.html'):
                continue
            path = os.path.join(lang, name)
            with open(path, encoding='utf-8') as handle:
                before = handle.read()
            after, counts = rewrite(before, lang, migrate, name)
            if relink and lang != 'ru':
                after, moved = cross_links(after, lang)
                counts['pages'] += moved
            total['files'] += 1
            for key in counts:
                total[key] += counts[key]
            if after != before:
                total['touched'] += 1
                if not check_only:
                    with open(path, 'w', encoding='utf-8') as handle:
                        handle.write(after)

    # Корневая дверь лежит не в папке языка, а в корне. Из всей оболочки ей
    # нужна одна правка - версия в ссылке на таблицу стилей.
    door = 'index.html'
    if os.path.isfile(door):
        with open(door, encoding='utf-8') as handle:
            before = handle.read()
        counts = {'version': 0, 'site': 0}
        after = version(before, counts)
        after = HTML_TAG.sub(
            lambda m: '<html lang="%s" data-site="%s">' % (m.group(1), CONF['key']), after, count=1)
        total['files'] += 1
        total['version'] += counts['version']
        if after != before:
            total['touched'] += 1
            if not check_only:
                with open(door, 'w', encoding='utf-8') as handle:
                    handle.write(after)

    if check_only:
        print()
        print('  Оболочка страниц (--check)')
        print('  ' + '-' * 46)
        print('  страниц просмотрено:   %d' % total['files'])
        if total['touched'] > 0:
            print('  страниц устарело:      %d' % total['touched'])
            if total['nav_num'] > 0:
                print('  номеров разделов:      %d' % total['nav_num'])
            if total['nav_current'] > 0:
                print('  активных пунктов:      %d' % total['nav_current'])
            print('  ' + '-' * 46)
            print('  \033[31mКРАСНОЕ\033[0m  - запустите python3 tools/build-nav.py')
            print()
            return 1
        print('  ' + '-' * 46)
        print('  \033[32mЗЕЛЁНОЕ\033[0m')
        print()
        return 0

    print()
    print('  Оболочка страниц')
    print('  ' + '-' * 46)
    print('  страниц просмотрено:   %d' % total['files'])
    print('  страниц изменено:      %d' % total['touched'])
    print('  номеров разделов:      %d' % total['nav_num'])
    print('  активных пунктов:      %d' % total['nav_current'])
    print('  путей к оснастке:      %d' % total['assets'])
    print('  ссылок между страницами: %d' % total['pages'])
    print('  ссылок на занятия:     %d' % total['lessons'])
    print('  значков заменено:      %d' % total['icons'])
    print('  правок доступности:    %d' % total['access'])
    print('  версий оснастки:       %d' % total['version'])
    print('  имён сайта в разметке: %d' % total['site'])
    print('  ' + '-' * 46)
    print()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
