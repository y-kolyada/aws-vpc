#!/usr/bin/env bash
# Быстрая проверка изменений. Проверяет только изменённые HTML-файлы и утверждения.
#
#     ./tools/check-fast.sh
#     ./tools/check-fast.sh ru/01.html ru/02.html
#
# Запускает проверки текста, навигации, клеймов и браузерного рендеринга
# только для целевых файлов, экономя время и контекст во время смены.

set -uo pipefail
cd "$(dirname "$0")/.." || exit 2

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

# Определение списка проверяемых страниц
TARGETS=("$@")
if [ "${#TARGETS[@]}" -eq 0 ]; then
  # Ищем изменённые HTML-файлы в рабочей копии или индексе git
  CHANGED=$(git status --porcelain 2>/dev/null | awk '{print $NF}' | grep '\.html$' || true)
  if [ -z "$CHANGED" ]; then
    # Если рабочая копия чиста, берём файлы последнего коммита
    CHANGED=$(git diff --name-only HEAD~1 2>/dev/null | grep '\.html$' || true)
  fi
  if [ -n "$CHANGED" ]; then
    # Преобразуем строку в массив
    while IFS= read -r line; do
      [ -f "$line" ] && TARGETS+=("$line")
    done <<< "$CHANGED"
  fi
fi

if [ "${#TARGETS[@]}" -eq 0 ]; then
  TARGETS=("ru/index.html" "ru/01.html")
fi

echo "  Быстрая проверка: ${TARGETS[*]}"
echo "  =============================================="

run "оболочка и навигация" python3 tools/build-nav.py --check
run "утверждения сайта"    ./tools/check-claims.sh
run "пунктуация (файлы)"   python3 tools/check-text.py "${TARGETS[@]}"
run "телефон и панель"     node tools/check-pages.mjs "${TARGETS[@]}"

echo
echo "  Итог быстрой проверки"
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
  printf '  %s\n\n' "$(g 'ЗЕЛЁНОЕ (быстрая проверка)')"
else
  printf '  %s  - проверок со словом НЕТ: %s\n\n' "$(r 'КРАСНОЕ')" "$FAIL"
fi

[ "$FAIL" -eq 0 ]
