#!/usr/bin/env python3
"""Check terms: bilateral contract between glossary.html and in-page .term cards.

Every concept in ru/glossary.html must have at least one interactive in-page
card (.term > .term-btn + .term-card) placed at its primary introduction in the
chapters (01-15), the Engineering Navigator (navigator.html), the Landing page
(index.html), or as an in-page reference in glossary.html itself.

Conversely, every .term card on any page must link to a valid #term-* anchor
defined in ru/glossary.html.

    python3 tools/check-terms.py
"""

import glob
import os
import re
import sys

GLOSSARY_PATH = os.path.join('ru', 'glossary.html')
GLOSSARY_TERM_RE = re.compile(r'<div class="glossary-term"\s+id="([^"]+)">')
IN_PAGE_TERM_RE = re.compile(
    r'<span class="term">.*?<span class="term-links"><a href="([^"]+)"',
    re.DOTALL
)


def main():
    if not os.path.isfile(GLOSSARY_PATH):
        print()
        print('  Двусторонний контракт терминов')
        print('  ' + '-' * 46)
        print('  терминов в словаре: 0 (словарь ещё не создан)')
        print('  ----------------------------------------------')
        print('  ЗЕЛЁНОЕ')
        print()
        return 0

    with open(GLOSSARY_PATH, encoding='utf-8') as f:
        glossary_html = f.read()

    glossary_terms = GLOSSARY_TERM_RE.findall(glossary_html)
    if not glossary_terms:
        print()
        print('  Двусторонний контракт терминов')
        print('  ' + '-' * 46)
        print('  терминов в словаре: 0 (пустой каркас словаря)')
        print('  ----------------------------------------------')
        print('  ЗЕЛЁНОЕ')
        print()
        return 0

    glossary_term_set = set(glossary_terms)

    # Scan all Russian pages
    ru_files = sorted(glob.glob(os.path.join('ru', '*.html')))
    term_counts = {}
    found_term_links = {}  # term_id -> list of (file, href)
    broken_links = []      # (file, href, reason)

    total_cards = 0
    landing_cards = 0
    chapter_cards = 0
    navigator_cards = 0
    glossary_cards = 0

    for file_path in ru_files:
        basename = os.path.basename(file_path)
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        matches = IN_PAGE_TERM_RE.findall(content)
        count = len(matches)
        total_cards += count
        term_counts[basename] = count

        if basename == 'index.html':
            landing_cards += count
        elif basename == 'navigator.html':
            navigator_cards += count
        elif basename == 'glossary.html':
            glossary_cards += count
        elif re.match(r'^\d{2}\.html$', basename):
            chapter_cards += count

        for href in matches:
            target_page, _, anchor = href.partition('#')
            if not anchor:
                broken_links.append((basename, href, 'ссылка не содержит якоря'))
                continue

            if anchor not in glossary_term_set:
                broken_links.append((basename, href, f'якорь #{anchor} отсутствует в словаре'))
                continue

            found_term_links.setdefault(anchor, []).append((basename, href))

    # Identify glossary terms missing in-page markup
    missing_in_pages = [t for t in glossary_terms if t not in found_term_links]

    has_errors = bool(broken_links or missing_in_pages)

    print()
    print('  Двусторонний контракт терминов')
    print('  ' + '-' * 46)
    print(f'  терминов в словаре:          {len(glossary_terms)}')
    print(f'  карточек .term на страницах: {total_cards}')
    print(f'    из них на посадочной:      {landing_cards}')
    print(f'    из них в главах (01-15):   {chapter_cards}')
    print(f'    из них в навигаторе:       {navigator_cards}')
    print(f'    из них в словаре:          {glossary_cards}')
    print(f'  покрытие терминов словаря:   {len(found_term_links)}/{len(glossary_terms)}')
    print(f'  неразмеченных терминов:      {len(missing_in_pages)}')
    print(f'  битых ссылок на термины:     {len(broken_links)}')

    if missing_in_pages:
        print()
        print('  ОШИБКА: следующие термины словаря не имеют интерактивных карточек .term:')
        for t in missing_in_pages[:10]:
            print(f'    -> #{t}')
        if len(missing_in_pages) > 10:
            print(f'    -> ... и ещё {len(missing_in_pages) - 10}')

    if broken_links:
        print()
        print('  ОШИБКА: обнаружены некорректные ссылки в карточках .term:')
        for b_file, b_href, b_why in broken_links[:10]:
            print(f'    -> {b_file}: {b_href} ({b_why})')

    print('  ' + '-' * 46)
    if has_errors:
        print('  КРАСНОЕ')
        print()
        return 1
    else:
        print('  ЗЕЛЁНОЕ')
        print()
        return 0


if __name__ == '__main__':
    sys.exit(main())
