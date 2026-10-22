#!/usr/bin/env python3
"""Search index: one file per language, built from the pages themselves.

    python3 tools/build-search.py            every language
    python3 tools/build-search.py --check    rebuild and compare, change nothing

The index is a .js file assigning a global, not .json: a page opened from the
file system cannot fetch JSON, and the site has to work that way.

A unit of search is a section with an anchor, a glossary term, or a single
question out of the bank - that is what a reader looks for before an interview.
Stub pages hold no sections, so they stay out of the index by themselves.

Output is Russian: it speaks to the person who accepts the work.
"""

import html
import json
import os
import re
import sys

LANGS = ('ru', 'en', 'uk', 'de')
OUT = 'assets/search-%s.js'
STRIP = re.compile(r'<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->', re.S | re.I)
MAIN = re.compile(r'<main\b[^>]*>(.*?)</main>', re.S | re.I)
H1 = re.compile(r'<h1\b[^>]*>(.*?)</h1>', re.S | re.I)
H2 = re.compile(r'<h2\b[^>]*\bid="([^"]+)"[^>]*>(.*?)</h2>', re.S | re.I)
TERM = re.compile(r'<div class="glossary-term" id="([^"]+)">(.*?)</h2>(.*?)(?=<div class="glossary-term"|<h2\b|</section>|$)', re.S | re.I)
QA = re.compile(r'<ol class="qa"[^>]*>(.*?)</ol>', re.S | re.I)
LI = re.compile(r'<li>(.*?)</li>', re.S | re.I)
STRONG = re.compile(r'<strong\b[^>]*>(.*?)</strong>', re.S | re.I)
TAG = re.compile(r'<[^>]+>')
ANCHOR_LINK = re.compile(r'<a class="anchor-link".*?</a>', re.S | re.I)
# Служебные блоки, которые печёт tools/build-meta.py: в поиске они были бы
# шумом - «Следующая тема» нашлась бы на каждой странице.
SERVICE = re.compile(r'<nav class="pager".*?</nav>|<p class="page-size".*?</p>', re.S | re.I)
GAP = re.compile(r'\s+([?!,.:;)])')


def text_of(chunk):
    plain = ' '.join(html.unescape(TAG.sub(' ', SERVICE.sub(' ', ANCHOR_LINK.sub(' ', chunk)))).split())
    return GAP.sub(r'\1', plain)


def entries(path, page):
    raw = STRIP.sub(' ', open(path, encoding='utf-8').read())
    body = MAIN.search(raw)
    if not body:
        return []
    body = body.group(1)
    title = text_of(H1.search(body).group(1)) if H1.search(body) else page
    found = []

    cuts = [(m.start(), m.group(1), text_of(m.group(2)).rstrip(' #')) for m in H2.finditer(body)]
    for n, (start, anchor, head) in enumerate(cuts):
        end = cuts[n + 1][0] if n + 1 < len(cuts) else len(body)
        chunk = body[start:end]
        # A glossary block heading holds the terms that follow; they are indexed
        # one by one, so the heading keeps only its own lead text.
        own = chunk.split('<div class="glossary-term"')[0]
        found.append([page + '#' + anchor, head, title, text_of(own)])

        for block in QA.findall(chunk):
            for item in LI.findall(block):
                ask = STRONG.search(item)
                if not ask:
                    continue
                found.append([page + '#' + anchor, text_of(ask.group(1)), title, text_of(item)])

    for anchor, head, rest in TERM.findall(body):
        found.append([page + '#' + anchor, text_of(head).rstrip(' #'), title, text_of(rest)])

    return found


def build(lang):
    items = []
    for name in sorted(os.listdir(lang)):
        if name.endswith('.html'):
            items += entries(os.path.join(lang, name), name)
    data = json.dumps({'l': lang, 'i': items}, ensure_ascii=False, separators=(',', ':'))
    return 'window.SEARCH=' + data + ';\n', len(items)


def main(argv):
    check = '--check' in argv[1:]
    langs = [a for a in argv[1:] if not a.startswith('--')] or list(LANGS)
    stale = []
    rows = []

    for lang in langs:
        if not os.path.isdir(lang):
            continue
        fresh, count = build(lang)
        path = OUT % lang
        old = open(path, encoding='utf-8').read() if os.path.isfile(path) else ''
        rows.append((lang, len(fresh.encode('utf-8')), count, fresh != old))
        if fresh != old:
            if check:
                stale.append(path)
            else:
                with open(path, 'w', encoding='utf-8') as handle:
                    handle.write(fresh)

    print()
    print('  Индекс поиска')
    print('  ' + '-' * 46)
    for lang, size, count, changed in rows:
        mark = 'устарел' if (changed and check) else ('пересобран' if changed else 'без изменений')
        print('  %s: %5d записей, %4d КБ - %s' % (lang, count, size // 1024, mark))
    print('  ' + '-' * 46)
    if check:
        print('  %s' % ('КРАСНОЕ' if stale else 'ЗЕЛЁНОЕ'))
        if stale:
            print('        -> пересоберите: python3 tools/build-search.py')
    print()
    return 1 if stale else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
