#!/usr/bin/env bash
# Claim check: what the site states about its tool is executed, not re-read.
#
#     tools/check-claims.sh
#
# Every claim lives in tools/claims.tsv, one per line, tab separated:
#
#     what the site states <TAB> expected output <TAB> command
#
# The command runs, its output is compared with what is expected, and the line
# turns ДА or НЕТ. A site with no claims yet is green: nothing is claimed, so
# nothing is unproven. The moment a page states something about the tool, the
# claim belongs here with the command that proves it.
#
# Separate from the page check on purpose: that one turns red when markup
# breaks, this one when knowledge does, and the reason for red must be obvious.
#
# Output is Russian: it speaks to the person who accepts the work.

set -uo pipefail

FILE=${1:-tools/claims.tsv}
FAIL=0
SEEN=0
g() { printf '\033[32m%s\033[0m' "$1"; }
r() { printf '\033[31m%s\033[0m' "$1"; }

printf '\n  Утверждения сайта проверены запуском\n'
echo "  ----------------------------------------------"

if [ -f "$FILE" ]; then
  while IFS=$'\t' read -r claim want cmd; do
    case "${claim:-}" in ''|'#'*) continue ;; esac
    [ -n "${cmd:-}" ] || { printf '  [ %s ] %s\n        -> строка без команды\n' "$(r 'НЕТ')" "$claim"; FAIL=$((FAIL+1)); continue; }
    SEEN=$((SEEN+1))
    got=$(eval "$cmd" 2>&1)
    if [ "$got" = "$want" ]; then
      printf '  [ %s ] %s\n' "$(g 'ДА ')" "$claim"
    else
      printf '  [ %s ] %s\n        -> ждали «%s», получили «%s»\n' "$(r 'НЕТ')" "$claim" "$want" "$got"
      FAIL=$((FAIL+1))
    fi
  done < "$FILE"
fi

if [ "$SEEN" -eq 0 ]; then
  printf '  утверждений объявлено: 0\n'
  printf '  пока сайт ничего не утверждает об инструменте, проверять нечего;\n'
  printf '  первое утверждение на странице - первая строка в %s\n' "$FILE"
fi

echo "  ----------------------------------------------"
if [ "$FAIL" -eq 0 ]; then
  printf '  %s\n\n' "$(g 'ЗЕЛЁНОЕ')"
else
  printf '  %s  - строк со словом НЕТ: %s\n\n' "$(r 'КРАСНОЕ')" "$FAIL"
fi
[ "$FAIL" -eq 0 ]
