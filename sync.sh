#!/usr/bin/env bash
# Hand the seed's shared parts to a site that already exists.
#
#     ./sync.sh ../../courses/git
#     ./sync.sh ../../courses/*          (several at once)
#
# Copies the engine, the shared checks and the harness documents. Never touches
# the site's own files: pages, site.conf, lessons/, and the three topic files
# (tools/check-examples.sh, tools/check-claims.sh, tools/claims.tsv) which are
# only created when absent, never overwritten.
#
# This is the only sanctioned way an engine fix reaches a site: the fix is made
# once in the seed and handed down, so five sites cannot drift five ways.
set -euo pipefail

seed=$(cd "$(dirname "$0")" && pwd)
own=(tools/check-examples.sh tools/check-claims.sh tools/claims.tsv)

# Разрешаем абсолютные пути целей до смены каталога
targets=()
for t in "$@"; do
  if [ -d "$t" ]; then
    targets+=("$(cd "$t" && pwd)")
  else
    targets+=("$t")
  fi
done

cd "$seed"

for target in "${targets[@]}"; do
  [ -f "$target/site.conf" ] || { printf '  %-22s пропущен: не сайт серии\n' "$(basename "$target")"; continue; }
  changed=0
  for file in assets/* assets/img/* tools/*.py tools/*.mjs tools/check-page.sh tools/check-fast.sh \
              check.sh .gitignore AGENTS.md CLAUDE.md BRIEF.md .claude/skills/*/*.md; do
    [ -f "$seed/$file" ] || continue
    # Леса штампа живут только в ростке: bootstrap.sh удаляет их у себя, и
    # раздача не должна возвращать их обратно. Поймано на сайте git.
    case "$file" in tools/new-site.py) continue ;; esac
    mkdir -p "$target/$(dirname "$file")"
    if [ ! -f "$target/$file" ] || ! cmp -s "$seed/$file" "$target/$file"; then
      cp "$seed/$file" "$target/$file"
      changed=$((changed+1))
    fi
  done
  for file in "${own[@]}"; do
    if [ ! -f "$target/$file" ]; then
      cp "$seed/$file" "$target/$file"
      changed=$((changed+1))
    fi
  done
  printf '  %-22s обновлено файлов: %s\n' "$(basename "$target")" "$changed"
done
