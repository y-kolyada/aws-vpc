#!/usr/bin/env python3
"""Link ruler: every internal href and src, every #anchor, across the site.

Prints two numbers - links checked and links broken - and exits 1 if any are
broken. Needed most when files move: fifteen hundred links cannot be counted by
hand, and a quietly broken one looks exactly like a working site.

    python3 tools/check-links.py            whole repository
    python3 tools/check-links.py ru en      these folders only

Output is Russian: it speaks to the person who accepts the work.
"""

import os
import re
import sys

SKIP_DIRS = {'.git', 'node_modules', '.claude', '.agents', '__pycache__'}
EXTERNAL = ('http://', 'https://', 'mailto:', 'tel:', 'data:', 'javascript:')

# Code samples and scripts hold no real links: a <pre> block containing
# src="data.csv" is an example of markup, not a link to follow.
STRIP = re.compile(r'<pre\b.*?</pre>|<script\b.*?</script>|<!--.*?-->', re.S | re.I)
LINK = re.compile(r'(?:href|src)\s*=\s*"([^"]*)"', re.I)
ID = re.compile(r'\bid\s*=\s*"([^"]+)"')


def pages(roots):
    for root in roots:
        if os.path.isfile(root):
            yield root
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for name in sorted(filenames):
                if name.endswith('.html'):
                    yield os.path.join(dirpath, name)


def read(path):
    with open(path, encoding='utf-8') as handle:
        return handle.read()


def ids_of(path, cache):
    if path not in cache:
        try:
            cache[path] = set(ID.findall(STRIP.sub(' ', read(path))))
        except OSError:
            cache[path] = set()
    return cache[path]


def main(argv):
    roots = argv[1:] or ['.']
    ids_cache = {}
    checked = anchors = 0
    broken = []
    files = list(pages(roots))

    for page in files:
        text = STRIP.sub(' ', read(page))
        here = os.path.dirname(page) or '.'
        for raw in LINK.findall(text):
            link = raw.strip()
            if not link or link.startswith(EXTERNAL):
                continue
            target, _, anchor = link.partition('#')
            target = target.split('?')[0]
            checked += 1

            if target:
                path = os.path.normpath(os.path.join(here, target))
                if path.endswith(os.sep) or os.path.isdir(path):
                    path = os.path.join(path, 'index.html')
                if not os.path.isfile(path):
                    broken.append((page, link, 'файла нет: ' + path))
                    continue
            else:
                path = page

            if anchor:
                anchors += 1
                if path.endswith('.html') and anchor not in ids_of(path, ids_cache):
                    broken.append((page, link, 'якоря нет в ' + path))

    print()
    print('  Линейка ссылок')
    print('  ' + '-' * 46)
    print('  страниц просмотрено: %d' % len(files))
    print('  ссылок проверено:    %d (из них якорей: %d)' % (checked, anchors))
    print('  битых:               %d' % len(broken))
    for page, link, why in broken[:40]:
        print('        -> %s: %s - %s' % (page, link, why))
    if len(broken) > 40:
        print('        -> ... и ещё %d' % (len(broken) - 40))
    print('  ' + '-' * 46)
    print('  %s' % ('КРАСНОЕ' if broken else 'ЗЕЛЁНОЕ'))
    print()
    return 1 if broken else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
