#!/usr/bin/env python3
"""Голос страницы: говорит ли она с человеком или о предмете.

    python3 tools/check-voice.py ru/04.html                сравнить с HEAD
    python3 tools/check-voice.py ru/04.html ru/05.html d54ca70

Сайт обращается к читателю: «ваш скрипт», «помните», «не оставляйте». Это
заявлено принципом дизайн-книги - личное уважительное обращение к человеку по
ту сторону экрана. Правка, которая делает текст понятнее на слух, легко уносит
обращение вместе с указаниями пальцем: предмет назван, а человек из абзаца
исчез. Поймано ровно так: после задания 30 в тринадцати правленых абзацах
обращений стало 0 вместо 8, а безличных форм 14 вместо 4.

Считается проза: всё внутри <main> без блоков кода и служебной разметки.
Обращение - второе лицо и притяжательные (вы, ваш, ви, you, your).
Безличное - глаголы третьего лица множественного числа (помечают, організовують):
по-русски и по-украински это главный признак канцелярита.

Красным становится одно: обращений стало меньше, чем было. Остальное печатается
как сведение, потому что норму голоса числом не задать.
"""

import html
import re
import subprocess
import sys

MAIN = re.compile(r'<main.*?</main>', re.S | re.I)
BLOCK = re.compile(r'<pre\b.*?</pre>', re.S | re.I)
SERVICE = re.compile(r'<nav\b.*?</nav>|<p class="page-size".*?</p>', re.S | re.I)
TAG = re.compile(r'<[^>]+>')

YOU = {
    'ru': re.compile(r'\b(?:вы|вам|вас|вами|ваш|ваша|ваше|ваши|вашего|вашей|ваших|вашим|вашу)\b', re.I),
    'uk': re.compile(r'\b(?:ви|вам|вас|вами|ваш|ваша|ваше|ваші|вашого|вашої|ваших|вашим|вашу)\b', re.I),
    'en': re.compile(r'\b(?:you|your|yours)\b', re.I),
    'de': re.compile(r'\b(?:sie|ihr|ihre|ihren|ihrem|ihrer)\b', re.I),
}
# Обращение несут не только местоимения, но и формы второго лица: «помните»,
# «попросите», «проверяете». Совпадений на девяти страницах 38, из них ложных
# два - существительные в предложном падеже, они и стоят в стоп-списке.
SECOND = {
    'ru': re.compile(r'\b[а-яё]+(?:йте|ьте|ите|ете)\b', re.I),
    'uk': re.compile(r'\b[а-яіїєґ]+(?:йте|ьте|ите|ете|єте|ите)\b', re.I),
}
NOT_A_VERB = {'интернете', 'ответе', 'сайте', 'байте', 'документе', 'клиенте',
              'компоненте', 'проекте', 'процессе', 'результате', 'варианте',
              'контексте', 'інтернеті', 'відповіді', 'сайті'}

IMPERSONAL = {
    'ru': re.compile(r'\b\w+(?:ают|уют|яют|ются|аются|уются)\b', re.I),
    'uk': re.compile(r'\b\w+(?:ають|ують|яють|ються|уються)\b', re.I),
}


# Пояснение после кода живёт в двух формах: абзацем на тематических страницах
# и блоком «Почему так» на страницах разборов. Правка по §5.8 ложится именно
# сюда, поэтому ключ --after-code сужает подсчёт до них.
AFTER_CODE = re.compile(r'</pre>\s*(<p>.*?</p>|<div class="prints">.*?</div>)', re.S | re.I)


def prose(raw, after_code=False):
    body = MAIN.search(raw)
    if not body:
        return ''
    if after_code:
        text = ' '.join(AFTER_CODE.findall(body.group(0)))
    else:
        text = SERVICE.sub(' ', BLOCK.sub(' ', body.group(0)))
    return ' '.join(html.unescape(TAG.sub(' ', text)).split())


def before(ref, page):
    out = subprocess.run(['git', 'show', '%s:%s' % (ref, page)],
                         capture_output=True, text=True)
    return None if out.returncode else out.stdout


def count(text, lang):
    you = len(YOU[lang].findall(text)) if lang in YOU else 0
    if lang in SECOND:
        you += sum(1 for w in SECOND[lang].findall(text) if w.lower() not in NOT_A_VERB)
    cold = len(IMPERSONAL[lang].findall(text)) if lang in IMPERSONAL else 0
    return you, cold, len(text.split())


def report(page, ref, after_code=False):
    lang = page.split('/')[0]
    was = before(ref, page)
    if was is None:
        print('  [ НЕТ ] %s: в версии %s такой страницы нет' % (page, ref))
        return ['нет страницы в ' + ref]
    with open(page, encoding='utf-8') as handle:
        now = handle.read()
    old_you, old_cold, old_words = count(prose(was, after_code), lang)
    new_you, new_cold, new_words = count(prose(now, after_code), lang)
    bad = []
    if new_you < old_you:
        bad.append('обращений стало меньше')
    print('  [ %s ] %s' % ('ДА ' if not bad else 'НЕТ', page))
    print('        обращений к читателю: %d было, %d стало' % (old_you, new_you))
    if lang in IMPERSONAL:
        print('        безличных форм:       %d было, %d стало' % (old_cold, new_cold))
    print('        слов в прозе:         %d было, %d стало' % (old_words, new_words))
    return bad


def main(argv):
    after_code = '--after-code' in argv[1:]
    pages = [a for a in argv[1:] if a.endswith('.html')]
    refs = [a for a in argv[1:] if not a.endswith('.html') and not a.startswith('--')]
    if not pages:
        print('укажите страницу: python3 tools/check-voice.py ru/04.html [ref]')
        return 2
    ref = refs[0] if refs else 'HEAD'

    print()
    print('  Голос %s против версии %s'
          % ('пояснений после кода' if after_code else 'страницы', ref))
    print('  ' + '-' * 46)
    broken = 0
    for page in pages:
        if report(page, ref, after_code):
            broken += 1
    print('  ' + '-' * 46)
    print('  страниц сверено: %d, потеряли обращение: %d' % (len(pages), broken))
    print('  %s' % ('\033[31mКРАСНОЕ\033[0m' if broken else '\033[32mЗЕЛЁНОЕ\033[0m'))
    print()
    return 1 if broken else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
