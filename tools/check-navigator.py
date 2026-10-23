#!/usr/bin/env python3
"""Navigator contract: nine lenses, and a way out of every one of them.

    python3 tools/check-navigator.py

The engineering navigator is a cross-section, not a table of contents: its
value is in the transitions. A lens a reader cannot leave does not do its
work. So three things are checked here.

1. Nine canonical lenses in the canonical order (AGENTS.md section 5.16).
   The anchors are fixed across the series, because cross-site links and the
   reader's muscle memory both depend on them.

2. Every lens ends with a visible line of related chapters. This standard
   existed on five sites of the series and was written in no rule at all,
   so a sixth site satisfied the letter of "bidirectional cross-links" with
   links inside the prose and shipped without the line; the checks had
   nothing to catch and the Architect caught it by eye (finding 7 of
   devops-kubernetes).

3. How many links the line carries is not checked, and that is deliberate.
   The only number here that is not arbitrary is "not zero": the contract of
   a lens is that a reader can leave it, and one way out is a way out. Any
   floor above one is taste, and taste belongs to the site, not to the
   series - this check first demanded four chapters and four glossary
   articles, which were simply the numbers of the site that wrote it, and
   that floor declared five accepted sites defective. A site that wants a
   richer line states it in its own tools/claims.tsv. Glossary articles in
   the line are counted and printed for the same reason: useful to see,
   wrong to demand.

The contract is applied lens by lens, and only to a lens that is actually
written: a freshly stamped site carries nine headings with one placeholder
sentence under each, and demanding a line of related chapters from a
placeholder would mean a red check on an untouched site. A lens counts as
written once its prose passes WRITTEN_CHARS, which is far above a sentence
and far below a real lens. Output is Russian: it speaks to the person who accepts
the work.
"""

import os
import re
import sys

NAVIGATOR = os.path.join('ru', 'navigator.html')
GLOSSARY = os.path.join('ru', 'glossary.html')
LENSES = ['lens-components', 'lens-code', 'lens-strength', 'lens-weaknesses',
          'lens-ecosystem', 'lens-ai', 'lens-cloud', 'lens-devops', 'lens-sre']
RELATED = 'Связанные главы курса:'
MIN_CHAPTERS = 1  # не вкус, а контракт: из линзы есть выход
# Заготовка линзы - одно предложение, написанная линза - несколько абзацев.
# Порог стоит между ними с большим запасом в обе стороны.
WRITTEN_CHARS = 400

LENS_RE = re.compile(r'<h2 id="(lens-[a-z]+)"')
RELATED_RE = re.compile(r'<strong>' + RELATED + r'</strong>(.*?)</p>', re.S)
CHAPTER_RE = re.compile(r'href="\d\d\.html"')
TERM_RE = re.compile(r'href="glossary\.html#')
MARKUP_RE = re.compile(r'<[^>]+>')


def report(lines, bad):
    print()
    print('  Контракт навигатора: девять линз и выход из каждой')
    print('  ' + '-' * 46)
    for line in lines:
        print('  ' + line)
    for why in bad[:10]:
        print('        -> ' + why)
    if len(bad) > 10:
        print('        -> ... и ещё %d' % (len(bad) - 10))
    print('  ' + '-' * 46)
    print('  ' + ('КРАСНОЕ' if bad else 'ЗЕЛЁНОЕ'))
    print()
    return 1 if bad else 0


def main():
    if not os.path.isfile(NAVIGATOR):
        return report(['навигатора нет, проверять нечего'], [])

    with open(NAVIGATOR, encoding='utf-8') as f:
        text = f.read()

    found = LENS_RE.findall(text)
    if not found:
        return report(['навигатор ещё не написан, линз нет'], [])

    bad = []
    if found != LENSES:
        bad.append('линзы не канонические или не в том порядке: ' + ', '.join(found))

    glossary_ready = False
    if os.path.isfile(GLOSSARY):
        with open(GLOSSARY, encoding='utf-8') as f:
            glossary_ready = 'class="glossary-term" id=' in f.read()

    chunks = text.split('<h2 id="lens-')[1:]
    thin_chapters = terms_total = missing = draft = 0
    for anchor, chunk in zip(found, chunks):
        if len(MARKUP_RE.sub(' ', chunk).strip()) < WRITTEN_CHARS:
            draft += 1
            continue
        line = RELATED_RE.search(chunk)
        if not line:
            missing += 1
            bad.append('%s: нет строки «%s» в конце линзы' % (anchor, RELATED))
            continue
        chapters = len(CHAPTER_RE.findall(line.group(1)))
        if chapters < MIN_CHAPTERS:
            thin_chapters += 1
            bad.append('%s: строка связей не ведёт ни в одну главу' % anchor)
        if glossary_ready:
            terms_total += len(TERM_RE.findall(line.group(1)))

    lines = ['линз: %d из %d, написано: %d' % (len(found), len(LENSES), len(found) - draft),
              'линз без строки связей: %d' % missing,
              'линз с тонкой строкой: %d' % thin_chapters]
    if draft:
        lines.append('линз-заготовок пропущено: %d' % draft)
    if glossary_ready:
        lines.append('ссылок в словарь из строк связей: %d (не требуются, но полезны)' % terms_total)
    return report(lines, bad)


if __name__ == '__main__':
    sys.exit(main())
