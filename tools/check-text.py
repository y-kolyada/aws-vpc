"""Punctuation of the pages: one rule, held by a machine rather than by memory.

    python3 tools/check-text.py

WHY THIS EXISTS. The em dash is forbidden everywhere in this project - in text,
in code and in commit messages. The rule had been broken twice by hand before
anything checked it: a rule nobody enforces is a rule nobody keeps. Output is
Russian: it speaks to the person who accepts the work.
"""
import glob
import pathlib
import re
import sys

LANGS = ('ru', 'en', 'uk', 'de')
DASH = '—'
WHERE_DASH = re.compile(r'[^<>]{0,40}' + DASH + r'[^<>]{0,40}')
WHERE_ROSIYSK = re.compile(r'[^<>]{0,40}російськ[^<>]{0,40}', re.I)


def main():
    bad_dash = []
    bad_name = []
    pages = sorted(page for lang in LANGS for page in glob.glob('%s/*.html' % lang))
    for page in pages:
        text = pathlib.Path(page).read_text(encoding='utf-8')
        for found in WHERE_DASH.finditer(text):
            bad_dash.append((page, re.sub(r'\s+', ' ', found.group(0)).strip()))
        for found in WHERE_ROSIYSK.finditer(text):
            bad_name.append((page, re.sub(r'\s+', ' ', found.group(0)).strip()))

    print()
    print('  Текст и пунктуация страниц')
    print('  ' + '-' * 46)
    print('  страниц просмотрено: %d' % len(pages))
    print('  длинных тире:        %d' % len(bad_dash))
    for page, piece in bad_dash[:8]:
        print('        -> %s: %s' % (page, piece[:70]))
    if len(bad_dash) > 8:
        print('        -> ... и ещё %d' % (len(bad_dash) - 8))
    if bad_name:
        print('  несоответствий «російськ»: %d' % len(bad_name))
        for page, piece in bad_name[:8]:
            print('        -> %s: %s' % (page, piece[:70]))
        if len(bad_name) > 8:
            print('        -> ... и ещё %d' % (len(bad_name) - 8))
    print('  ' + '-' * 46)
    if bad_dash:
        print('  \033[31mКРАСНОЕ\033[0m  - длинное тире запрещено: дефис с пробелами')
        print()
        return 1
    if bad_name:
        print('  \033[31mКРАСНОЕ\033[0m  - формулировка «російська/російською» не используется: исходный русский язык / руська мова')
        print()
        return 1
    print('  \033[32mЗЕЛЁНОЕ\033[0m')
    print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
