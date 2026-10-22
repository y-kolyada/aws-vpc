#!/usr/bin/env bash
# Page check: the file exists, is not empty, and carries its own title.
#
#     tools/check-page.sh ru/index.html
#
# Answers one of two things: ЗЕЛЁНОЕ or КРАСНОЕ. The wording of the output is
# Russian on purpose: it speaks to the person who accepts the work.
#
# Deliberately small. It does not look at what is on the page, only that a page
# is there - a green check that proves almost nothing, and says so.

set -uo pipefail

PAGE=${1:-ru/index.html}
FAIL=0

g() { printf '\033[32m%s\033[0m' "$1"; }
r() { printf '\033[31m%s\033[0m' "$1"; }

ok()  { printf '  [ %s ] %s\n' "$(g 'ДА ')" "$1"; }
bad() { printf '  [ %s ] %s\n' "$(r 'НЕТ')" "$1"; FAIL=$((FAIL+1))
        printf '        -> %s\n' "$2"; }

echo
echo "  Проверка продукта"
echo "  ----------------------------------------------"

# 1. The page exists
if [ -f "$PAGE" ]; then
  ok "страница $PAGE на месте"
else
  bad "страницы $PAGE нет" "проверьте путь: страницы лежат в ru/ en/ uk/ de/"
fi

# 2. It is not empty
if [ -s "$PAGE" ]; then
  ok "страница не пустая"
else
  bad "страница пустая" "в ней должно быть хоть что-то"
fi

# 3. It has a title. Two ways of reading it, because a grep without -P would
#    return nothing and the check would then lie about the reason.
TITLE=$(grep -oiP '(?<=<title>).*(?=</title>)' "$PAGE" 2>/dev/null | head -1 || true)
if [ -z "$TITLE" ]; then
  TITLE=$(sed -n 's/.*<title>\(.*\)<\/title>.*/\1/Ip' "$PAGE" 2>/dev/null | head -1 || true)
fi
if [ -n "$TITLE" ]; then
  ok "заголовок есть: $TITLE"
else
  bad "у страницы нет заголовка" "нужен тег <title> внутри <head>"
fi

# 4. The title is the product's own, not the template's.
#    A check that has never been red proves nothing. This one was.
if [ "$TITLE" = "Замени этот заголовок" ]; then
  bad "заголовок всё ещё из шаблона" "поменяй <title> на свой - это твой продукт, не наш"
else
  [ -n "$TITLE" ] && ok "заголовок свой, не из шаблона"
fi

# 5. The navigator holds 15 numbered topics
NUMS=$(grep -o '<span class="num">' "$PAGE" 2>/dev/null | wc -l || true)
if [ "$NUMS" -eq 15 ]; then
  ok "в навигаторе 15 пронумерованных тем"
else
  bad "в навигаторе нет нумерации тем: $NUMS из 15" "запустите python3 tools/build-nav.py для восстановления"
fi

echo "  ----------------------------------------------"
if [ "$FAIL" -eq 0 ]; then
  printf '  %s\n\n' "$(g 'ЗЕЛЁНОЕ')"
else
  printf '  %s  - строк со словом НЕТ: %s\n\n' "$(r 'КРАСНОЕ')" "$FAIL"
fi

[ "$FAIL" -eq 0 ]
