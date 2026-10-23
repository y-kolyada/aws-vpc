#!/usr/bin/env bash
# Проверка сайта. Одна команда - один ответ.
#
#     ./check.sh
#
# ПОЧЕМУ ОДНА КОМАНДА, А НЕ ЧЕТЫРЕ. Проверка, которую нужно вспоминать по
# частям, не запускается перед публикацией - запускается та, что одна и
# отвечает ЗЕЛЁНОЕ или КРАСНОЕ. Сами проверки лежат в tools/ и запускаются
# по отдельности, когда нужно понять причину:
#
#     tools/check-page.sh ru/01.html      страница существует и у неё свой заголовок
#     tools/check-claims.sh               утверждения сайта выполняются в терминале
#     tools/check-examples.sh             примеры со страниц 10-12 запускаются
#     python3 tools/check-links.py        внутренние ссылки и якоря
#     python3 tools/check-text.py         длинное тире на страницах
#     python3 tools/build-search.py       пересобрать индекс поиска
#     python3 tools/build-meta.py         голова страницы, объём в словах, соседние темы, карта сайта
#     node tools/check-pages.mjs          телефон 390px и липкая панель, все страницы
#     python3 tools/check-navigator.py    девять линз и выход из каждой
#     node tools/shot.mjs ru/01.html       снимок одной страницы, чтобы посмотреть глазами
#
# Браузерная проверка требует playwright (npm i playwright). Если его нет,
# она честно говорит об этом и считается КРАСНОЙ: зелёный ответ без браузера
# означал бы, что страницы никто не смотрел.

set -uo pipefail
cd "$(dirname "$0")" || exit 2

if [ "${1:-}" = "--fast" ]; then
  shift
  exec ./tools/check-fast.sh "$@"
fi

FAIL=0
NAMES=()
CODES=()

g() { printf '\033[32m%s\033[0m' "$1"; }
r() { printf '\033[31m%s\033[0m' "$1"; }

run() {
  local name=$1
  shift
  "$@"
  local code=$?
  NAMES+=("$name")
  CODES+=("$code")
  [ "$code" -eq 0 ] || FAIL=$((FAIL + 1))
}

run "страница и заголовок" ./tools/check-page.sh ru/index.html
run "оболочка и навигация" python3 tools/build-nav.py --check
run "утверждения сайта"    ./tools/check-claims.sh
run "примеры запускаются"  ./tools/check-examples.sh
run "ссылки и якоря"       python3 tools/check-links.py
run "термины и словарь"    python3 tools/check-terms.py
run "пунктуация"          python3 tools/check-text.py
run "индекс поиска"        python3 tools/build-search.py --check
run "данные страниц"       python3 tools/build-meta.py --check
run "телефон и панель"     node tools/check-pages.mjs
run "линзы навигатора"     python3 tools/check-navigator.py

echo
echo "  Итог проверки сайта"
echo "  ----------------------------------------------"
for i in "${!NAMES[@]}"; do
  if [ "${CODES[$i]}" -eq 0 ]; then
    printf '  [ %s ] %s\n' "$(g 'ДА ')" "${NAMES[$i]}"
  else
    printf '  [ %s ] %s\n' "$(r 'НЕТ')" "${NAMES[$i]}"
  fi
done
echo "  ----------------------------------------------"
if [ "$FAIL" -eq 0 ]; then
  printf '  %s\n\n' "$(g 'ЗЕЛЁНОЕ')"
else
  printf '  %s  - проверок со словом НЕТ: %s\n\n' "$(r 'КРАСНОЕ')" "$FAIL"
fi

[ "$FAIL" -eq 0 ]
