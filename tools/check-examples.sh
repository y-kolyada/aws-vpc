#!/usr/bin/env bash
# Example check: code shown on a page has been run, and it did what the page says.
#
#     tools/check-examples.sh
#
# A page marks a runnable block with data-run: `run` for a block that produces
# output, `setup` for one that prepares state, `syntax` for one that is only
# parsed. A fixture next to it says what to feed in and what to expect.
#
# THIS FILE IS A SKELETON. The mechanism is shared across the series, the
# interpreter is not: Bash runs with bash, Terraform with terraform validate,
# Actions with actionlint, a query language with a parser of its own. While the
# site declares no runnable blocks, the check is green - nothing is shown, so
# nothing is unproven. The first data-run block on a page turns it red, and
# that is the moment to write the runner here, with the reference site's
# tools/check-examples.sh as the pattern.
#
# Output is Russian: it speaks to the person who accepts the work.

set -uo pipefail

g() { printf '\033[32m%s\033[0m' "$1"; }
r() { printf '\033[31m%s\033[0m' "$1"; }

BLOCKS=$(grep -ho 'data-run="[a-z]*"' */*.html 2>/dev/null | wc -l)

printf '\n  Примеры со страниц запускаются\n'
echo "  ----------------------------------------------"

if [ "$BLOCKS" -eq 0 ]; then
  printf '  блоков с data-run: 0\n'
  printf '  страницы пока не показывают кода, который надо запускать\n'
  echo "  ----------------------------------------------"
  printf '  %s\n\n' "$(g 'ЗЕЛЁНОЕ')"
  exit 0
fi

printf '  блоков с data-run: %s, а запускателя под них нет\n' "$BLOCKS"
printf '  допишите этот файл: механика общая, интерпретатор свой\n'
printf '  образец - tools/check-examples.sh эталонного сайта\n'
echo "  ----------------------------------------------"
printf '  %s\n\n' "$(r 'КРАСНОЕ')"
exit 1
