#!/usr/bin/env bash
# Example check: code shown on a page has been run, and it did what the page says.
#
#     tools/check-examples.sh [страница ...]
#
# A page marks a runnable block with data-run: `run` for a block that produces
# output, `setup` for one that prepares state, `syntax` for one that is only
# parsed. This file is the site's own (AGENTS.md section 1): the mechanism is
# shared across the series, the interpreter is not.
#
# WHAT THIS SITE'S INTERPRETER IS. There is no AWS account here, so nothing on
# a page may claim to be a live answer from the service. Two kinds of block are
# therefore allowed, and both are proved without credentials and without a
# network call:
#
#   data-run="syntax"  a printed object. It must parse as JSON, and every key
#                      in it is matched, at its own place in the nesting,
#                      against the service model that the installed AWS CLI
#                      carries: `aws <command> --generate-cli-skeleton input`
#                      for what you send, `... output` for what comes back.
#                      An invented or misplaced field name turns this red.
#   data-run="run"     a computation over addresses. It is executed with
#                      `python3 -I` in a temporary directory, and the numbers
#                      the page quotes must appear in its output.
#   data-run="setup"   not supported here: there is no state to prepare.
#
# WHAT IT DOES NOT PROVE. The model says which fields exist and how they nest,
# not which values the service would return, and not that a call would succeed.
# A page therefore never prints an object as a real answer; it prints the shape
# of one. The line about a test account stands in lessons/backlog.md.
#
# THE TABLE BELOW IS THE CONTRACT. Four tab-separated fields: the block id,
# the kind, the way it is checked, and the detail.
#
#   модель   <команда> <input|output> [путь.в.форме]   сверить с моделью AWS
#   нет-модели  <причина>                              своей формы нет, и вот почему
#   ждём     <кусок>|<кусок>|...                       что обязано быть в выводе
#
# A block that parses as JSON and carries no data-run turns the check red: the
# mark cannot be forgotten. A marked block with no row in the table turns it
# red too: a block is never waved through in silence. The table lives here and
# not in tools/fixtures/, because section 1 of AGENTS.md names exactly three
# files as the site's own, and a new directory under tools/ is not one of them.
#
# Output is Russian: it speaks to the person who accepts the work.

set -uo pipefail
cd "$(dirname "$0")/.." || exit 2

PAGES=("$@")
if [ ${#PAGES[@]} -eq 0 ]; then
  mapfile -t PAGES < <(ls */*.html 2>/dev/null)
fi

tmp=$(mktemp -d "${TMPDIR:-/tmp}/examples.XXXXXX") || exit 2
trap 'rm -rf "$tmp"' EXIT

cat > "$tmp/table.tsv" <<'TABLE'
# id	вид	способ	подробность
02-2	syntax	модель	ec2 describe-subnets output Subnets.0
04-2	syntax	модель	ec2 describe-nat-gateways output NatGateways.0
05-2	syntax	модель	ec2 authorize-security-group-ingress input
06-1	syntax	модель	ec2 create-vpc-endpoint input
06-3	syntax	нет-модели	документ политики: служба принимает его строкой, и своей формы у него в модели нет
07-1	syntax	модель	ec2 create-vpc-peering-connection input
08-2	syntax	модель	ec2 modify-vpc-attribute input
08-4	syntax	модель	route53resolver create-resolver-endpoint input
09-4	syntax	модель	ec2 create-network-insights-path input
10-1	run	ждём	a pub 10.0.0.0/20|c data 10.0.128.0/20
10-2	run	ждём	28 16 11|24 256 251|20 4096 4091
10-3	run	ждём	10.0.5.0/24 pcx-07c3
10-4	syntax	модель	ec2 modify-subnet-attribute input
10-5	syntax	модель	ec2 revoke-security-group-egress input
10-6	syntax	модель	ec2 create-route input
11-1	syntax	модель	ec2 create-nat-gateway input
11-2	run	ждём	NAT    41.50|шлюз   0.00|разница 41.50
11-3	syntax	модель	ec2 modify-vpc-endpoint input
11-4	syntax	модель	ec2 authorize-security-group-ingress input
11-5	syntax	модель	ec2 create-flow-logs input
11-6	syntax	модель	route53 associate-vpc-with-hosted-zone input
11-7	run	ждём	можно: 100.64.0.0/16
12-1	run	ждём	pay 10.0.0.0/12|risk 10.16.0.0/12|web 10.32.0.0/12
12-2	syntax	модель	ec2 enable-transit-gateway-route-table-propagation input
12-3	syntax	модель	ram create-resource-share input
12-4	syntax	модель	route53resolver create-resolver-rule input
12-5	syntax	нет-модели	документ политики точки доступа: служба принимает его строкой, своей формы в модели нет
12-6	syntax	модель	ec2 start-network-insights-analysis input
TABLE

python3 -I - "$tmp" "$tmp/table.tsv" "${PAGES[@]}" <<'PY'
import html, json, os, pathlib, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

CODE = re.compile(r'<pre\b([^>]*)>\s*<code\b[^>]*>(.*?)</code>\s*</pre>', re.S | re.I)
KIND = re.compile(r'data-run="([a-z]+)"')
LIMIT = 20

GREEN, RED, OFF = '\033[32m', '\033[31m', '\033[0m'
fail = []
checked = schemes = ran = 0

tmp = pathlib.Path(sys.argv[1])
table = {}
for line in pathlib.Path(sys.argv[2]).read_text(encoding='utf-8').splitlines():
    if not line.strip() or line.lstrip().startswith('#'):
        continue
    bid, kind, how, detail = (line.split('\t') + ['', '', ''])[:4]
    table[bid.strip()] = (kind.strip(), how.strip(), detail.strip())

print()
print('  Примеры со страниц проверяются')
print('  ----------------------------------------------')


def ok(text):
    print('  [ %sДА %s ] %s' % (GREEN, OFF, text))


def bad(text):
    fail.append(text)
    print('  [ %sНЕТ%s ] %s' % (RED, OFF, text))


SHAPES = {}


def fetch(key):
    command, mode = key
    return subprocess.run(['aws'] + command.split() + ['--generate-cli-skeleton', mode],
                          capture_output=True, text=True)


def model(command, mode, path):
    """Форма объекта из модели службы, установленной вместе с AWS CLI."""
    run = SHAPES.get((command, mode)) or fetch((command, mode))
    if run.returncode != 0:
        tail = [l for l in run.stderr.strip().split('\n') if l.strip()]
        return None, 'модель не взялась: %s' % (tail[0] if tail else 'пустая ошибка')
    shape = json.loads(run.stdout)
    for step in filter(None, path.split('.')):
        try:
            shape = shape[int(step)] if step.isdigit() else shape[step]
        except (KeyError, IndexError, TypeError):
            return None, 'в модели нет пути %s' % path
    return shape, None


def compare(block, shape, where=''):
    """Каждый ключ страницы ищется на своём месте в форме службы."""
    wrong = []
    if isinstance(block, dict):
        if not isinstance(shape, dict):
            return ['%s: на странице объект, в модели его нет' % (where or 'корень')]
        for key, value in block.items():
            full = (where + '.' if where else '') + key
            if key not in shape:
                wrong.append('%s - такого поля в модели нет' % full)
            else:
                wrong += compare(value, shape[key], full)
    elif isinstance(block, list):
        if not isinstance(shape, list) or not shape:
            return ['%s: на странице список, в модели его нет' % (where or 'корень')]
        for i, value in enumerate(block):
            wrong += compare(value, shape[0], '%s[%d]' % (where, i))
    return wrong


blocks = []
wanted = set()
for key, (kind, how, detail) in table.items():
    if kind == 'syntax' and how == 'модель':
        parts = detail.split()
        if parts[-1] in ('input', 'output'):
            wanted.add((' '.join(parts[:-1]), parts[-1]))
        else:
            wanted.add((' '.join(parts[:-2]), parts[-2]))
if wanted:
    with ThreadPoolExecutor(max_workers=8) as pool:
        SHAPES.update(zip(wanted, pool.map(fetch, wanted)))

for page in sys.argv[3:]:
    text = pathlib.Path(page).read_text(encoding='utf-8')
    for number, match in enumerate(CODE.finditer(text), 1):
        found = KIND.search(match.group(1))
        blocks.append((page,
                       '%s-%d' % (pathlib.Path(page).stem, number),
                       found.group(1) if found else '',
                       html.unescape(match.group(2)).strip('\n')))

for page, bid, kind, body in blocks:
    looks_json = body.lstrip().startswith('{')
    row = table.get(bid)

    if not kind:
        if looks_json:
            bad('%s · похож на объект, а пометки data-run нет (%s)' % (bid, page))
        else:
            schemes += 1
        continue

    if kind == 'setup':
        bad('%s · пометка setup здесь не поддержана: состояние готовить нечем (%s)' % (bid, page))
        continue

    if row is None:
        bad('%s · помечен data-run="%s", а строки в таблице сверки нет (%s)' % (bid, kind, page))
        continue

    row_kind, how, detail = row
    if row_kind != kind:
        bad('%s · на странице data-run="%s", в таблице "%s" (%s)' % (bid, kind, row_kind, page))
        continue

    if kind == 'syntax':
        try:
            document = json.loads(body)
        except ValueError as error:
            bad('%s · не разбирается: %s (%s)' % (bid, error, page))
            continue
        if how == 'нет-модели':
            checked += 1
            ok('%s · разобран, своей формы в модели нет: %s' % (bid, detail))
            continue
        if how != 'модель':
            bad('%s · непонятный способ сверки "%s" (%s)' % (bid, how, page))
            continue
        parts = detail.split()
        command, mode = ' '.join(parts[:-1]), parts[-1]
        path = ''
        if mode not in ('input', 'output'):
            command, mode, path = ' '.join(parts[:-2]), parts[-2], parts[-1]
        shape, error = model(command, mode, path)
        if error:
            bad('%s · %s (%s)' % (bid, error, page))
            continue
        wrong = compare(document, shape)
        if wrong:
            bad('%s · %s (%s)' % (bid, '; '.join(wrong), page))
        else:
            checked += 1
            ok('%s · поля сверены с моделью: aws %s %s' % (bid, command, mode))
        continue

    if kind == 'run':
        if how != 'ждём':
            bad('%s · помечен run, а в таблице не сказано, чего ждать (%s)' % (bid, page))
            continue
        work = tmp / bid
        work.mkdir(parents=True, exist_ok=True)
        script = work / 'block.py'
        script.write_text(body + '\n', encoding='utf-8')
        env = dict(os.environ, TMPDIR=str(work))
        try:
            run = subprocess.run([sys.executable, '-I', 'block.py'], cwd=work, env=env,
                                 capture_output=True, text=True, timeout=LIMIT)
        except subprocess.TimeoutExpired:
            bad('%s · не уложился в %s секунд (%s)' % (bid, LIMIT, page))
            continue
        if run.returncode != 0:
            line = (run.stderr.strip().split('\n') or [''])[-1]
            bad('%s · код возврата %s: %s (%s)' % (bid, run.returncode, line, page))
            continue
        missing = [w for w in detail.split('|') if w not in run.stdout]
        if missing:
            bad('%s · в выводе нет: %s (%s)' % (bid, ', '.join(missing), page))
            for line in run.stdout.strip().split('\n')[:8]:
                print('        | %s' % line)
            continue
        ran += 1
        ok('%s · исполнен, числа страницы совпали' % bid)
        continue

    bad('%s · неизвестная пометка data-run="%s" (%s)' % (bid, kind, page))

print('  ----------------------------------------------')
print('  блоков всего: %d · сверено с моделью: %d · исполнено: %d · схем: %d'
      % (len(blocks), checked, ran, schemes))
print('  ----------------------------------------------')
if fail:
    print('  %sКРАСНОЕ%s  - блоков со словом НЕТ: %d\n' % (RED, OFF, len(fail)))
    sys.exit(1)
print('  %sЗЕЛЁНОЕ%s\n' % (GREEN, OFF))
PY
