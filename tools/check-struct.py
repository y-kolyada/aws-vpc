#!/usr/bin/env python3
"""Structure check: a translated page against its Russian original.

A translation must stay a translation: same structure, same anchors, same
commands. Accepting fifty pages in a language you do not read is guesswork
otherwise.

    python3 tools/check-struct.py en            every page of a language
    python3 tools/check-struct.py en/01.html    one page
    python3 tools/check-struct.py uk de         several languages

Compared: the set and order of all ids; the number of sections; the number of
code blocks and the skeleton of each (comments and human strings stripped, so
comments may be translated but grep -q must not become grep -Q); the number of
questions, exactly fifty on a level page; the alphabet (no Cyrillic in English
and German, Ukrainian letters present and Russian-only letters absent in
Ukrainian); and the shell - fifteen navigation items, four languages, no stub
card left behind.

Output is Russian: it speaks to the person who accepts the work.
"""

import os
import re
import sys

SOURCE = 'ru'
LANGS = ('en', 'uk', 'de')
SECTIONS = 15

STRIP = re.compile(r'<script\b.*?</script>|<!--.*?-->', re.S | re.I)
ID = re.compile(r'\bid\s*=\s*"([^"]+)"')
H2 = re.compile(r'<h2\b[^>]*\bid\s*=\s*"[^"]+"', re.I)
CODE = re.compile(r'<pre\b[^>]*>\s*<code\b[^>]*>(.*?)</code>\s*</pre>', re.S | re.I)
QA_ITEM = re.compile(r'<ol class="qa"[^>]*>(.*?)</ol>', re.S | re.I)
NAV_ITEM = re.compile(r'<nav class="contents".*?</nav>', re.S | re.I)
# Переключатель стал областью навигации с подписью - читалка игнорирует
# подпись на div без роли. Принимаем обе формы: старую в детской копии и
# новую здесь.
LANG_LINK = re.compile(r'<(div|nav) class="lang-switcher".*?</\1>', re.S | re.I)
ENTITIES = (('&lt;', '<'), ('&gt;', '>'), ('&quot;', '"'), ('&#39;', "'"), ('&amp;', '&'))

# Characters that mark a word as code rather than prose. A dot is not one of
# them: "subst." and its translation are words, not a command.
CODEISH = set('${}()[]<>*~|&/=+\\`!%^')

CYRILLIC = re.compile(r'[\u0400-\u04FF]')
UK_OWN = re.compile(r'[іїєґІЇЄҐ]')
RU_ONLY = re.compile(r'[ыэъЫЭЪ]')

# A comment starts a word: inside ${v#x} the hash is not a comment.
COMMENT = re.compile(r'(?m)(?:(?<=\s)|^)#.*$')
EXPANSION = re.compile(r'(\$(?:[a-zA-Z0-9_?#*@!$-]+|\{[^}]*\}|\([^)]*\))|`[^`]*`)')


def read(path):
    with open(path, encoding='utf-8') as handle:
        return handle.read()


def unescape(text):
    for what, to in ENTITIES:
        text = text.replace(what, to)
    return text


def skeleton(code):
    text = COMMENT.sub('', unescape(code))
    text = re.sub(r"'[^']*'", "''", text)
    text = re.sub(r'(\$\{[^}:]+\:\?)[^}]*\}', r'\1""}', text)
    out = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == '"':
            j = i + 1
            has_dollar = False
            while j < n:
                if text[j] == '\\':
                    j += 2
                    continue
                if text[j] in ('$', '`'):
                    has_dollar = True
                if text[j] == '"':
                    break
                j += 1
            if j < n and not has_dollar:
                out.append('""')
                i = j + 1
            else:
                content = text[i+1:j] if j < n else text[i+1:]
                parts = []
                last = 0
                for m in EXPANSION.finditer(content):
                    inter = content[last:m.start()]
                    codeish = ''.join(c for c in inter if c in '/=:')
                    if codeish:
                        parts.append(codeish)
                    parts.append(m.group(0))
                    last = m.end()
                tail = content[last:]
                codeish = ''.join(c for c in tail if c in '/=:')
                if codeish:
                    parts.append(codeish)
                out.append('"' + ''.join(parts) + '"')
                i = j + 1 if j < n else n
        else:
            out.append(text[i])
            i += 1
    return ' '.join(''.join(out).split())


def shape(code):
    """Shape of a block: line count and its code-like words. Prose differs
    between languages, but {a,b}, $var and *.txt must match."""
    text = unescape(code)
    text = re.sub(r'(\$\{[^}:]+\:\?)[^}]*\}', r'\1""}', text)
    tokens = [t.strip("\"'") for t in text.split()]
    tokens = [t for t in tokens if any(ch in CODEISH for ch in t)]
    return (len(text.strip().splitlines()), tokens)



def is_scheme(code):
    """A diagram rather than commands: Cyrillic survives in the original once
    comments and human strings are stripped. Such blocks are translated whole,
    so only their shape is compared."""
    return bool(CYRILLIC.search(skeleton(code)))


def facts(path):
    raw = read(path)
    text = STRIP.sub(' ', raw)
    nav = NAV_ITEM.search(text)
    switcher = LANG_LINK.search(text)
    qa = []
    for block in QA_ITEM.findall(text):
        qa.append(block.count('<li>'))
    return {
        'ids': ID.findall(text),
        'sections': len(H2.findall(text)),
        'codes': [skeleton(c) for c in CODE.findall(text)],
        'shapes': [shape(c) for c in CODE.findall(text)],
        'schemes': [is_scheme(c) for c in CODE.findall(text)],
        'questions': sum(qa),
        'nav': nav.group(0).count('<li>') if nav else 0,
        'langs': switcher.group(0).count('<a ') if switcher else 0,
        'stub': 'stub-card' in text,
        'raw': raw,
    }


def compare(target, source, lang):
    bad = []
    a, b = facts(target), facts(source)

    if a['ids'] != b['ids']:
        only_here = [i for i in a['ids'] if i not in b['ids']]
        only_there = [i for i in b['ids'] if i not in a['ids']]
        if only_here or only_there:
            bad.append('якоря разошлись: лишние %s, потерянные %s'
                       % (only_here[:3] or '-', only_there[:3] or '-'))
        else:
            bad.append('якоря те же, но в другом порядке')
    if a['sections'] != b['sections']:
        bad.append('разделов %d, в оригинале %d' % (a['sections'], b['sections']))
    if len(a['codes']) != len(b['codes']):
        bad.append('блоков кода %d, в оригинале %d' % (len(a['codes']), len(b['codes'])))
    else:
        for n in range(len(b['codes'])):
            if b['schemes'][n]:
                if a['shapes'][n] != b['shapes'][n]:
                    bad.append('схема %d: форма разошлась с оригиналом (строк %d против %d)'
                               % (n + 1, a['shapes'][n][0], b['shapes'][n][0]))
                    break
            elif a['codes'][n] != b['codes'][n]:
                bad.append('блок кода %d изменён: %s'
                           % (n + 1, a['codes'][n][:60] or '(пусто)'))
                break
    if a['questions'] != b['questions']:
        bad.append('вопросов %d, в оригинале %d' % (a['questions'], b['questions']))
    elif a['questions'] and a['questions'] != 50:
        bad.append('вопросов %d, а на странице уровня их ровно 50' % a['questions'])
    if a['nav'] != SECTIONS:
        bad.append('пунктов навигации %d вместо %d' % (a['nav'], SECTIONS))
    if a['langs'] != 4:
        bad.append('в переключателе языков %d ссылки вместо четырёх' % a['langs'])
    if a['stub']:
        bad.append('осталась карточка «перевод готовится»')

    # Переключатель языков вырезается из проверки алфавита: имя языка там
    # намеренно написано на самом языке - «Русский», «Українська», - и читалка
    # произносит его правильным голосом благодаря lang. Это требование
    # доступности, а не недопереведённый текст.
    speech = LANG_LINK.sub(' ', a['raw'])

    if lang in ('en', 'de'):
        left = CYRILLIC.findall(speech)
        left = [c for c in left if c not in '\u0410']  # font-size button label, fixed by the shell generator
        if left:
            bad.append('осталась кириллица: %d символов' % len(left))
    elif lang == 'uk':
        if not UK_OWN.search(speech):
            bad.append('нет украинских букв (і, ї, є, ґ) - страница не переведена')
        if RU_ONLY.search(speech):
            bad.append('остались русские буквы ы, э, ъ')
    return bad


def pages(args):
    out = []
    for arg in args:
        if os.path.isfile(arg):
            out.append(arg)
        elif os.path.isdir(arg):
            out += [os.path.join(arg, n) for n in sorted(os.listdir(arg)) if n.endswith('.html')]
    return out


def main(argv):
    args = argv[1:] or list(LANGS)
    targets = pages(args)
    if not targets:
        print('нечего сверять: укажите язык (en) или страницу (en/01.html)')
        return 2

    rows = []
    for target in targets:
        lang, name = os.path.split(target)
        lang = os.path.basename(lang)
        source = os.path.join(SOURCE, name)
        if lang == SOURCE:
            continue
        if not os.path.isfile(source):
            rows.append((target, ['нет русского оригинала ' + source]))
            continue
        rows.append((target, compare(target, source, lang)))

    broken = [r for r in rows if r[1]]
    print()
    print('  Сверка перевода с оригиналом')
    print('  ' + '-' * 46)
    for target, bad in rows:
        mark = 'ДА ' if not bad else 'НЕТ'
        print('  [ %s ] %s' % (mark, target))
        for line in bad:
            print('        -> %s' % line)
    print('  ' + '-' * 46)
    print('  страниц сверено: %d, расходятся: %d' % (len(rows), len(broken)))
    print('  %s' % ('КРАСНОЕ' if broken else 'ЗЕЛЁНОЕ'))
    print()
    return 1 if broken else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
