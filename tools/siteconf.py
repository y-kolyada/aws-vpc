#!/usr/bin/env python3
"""The site's own facts, read from site.conf.

Every tool in tools/ is identical on every site of the series. What differs -
the name, the live address, the topic word on the amber chip, the storage key
and the release number - lives in one file, site.conf, next to the pages.
"""

import pathlib


def conf(path='site.conf'):
    out = {}
    text = pathlib.Path(path).read_text(encoding='utf-8')
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        name, _, value = line.partition('=')
        out[name.strip()] = value.strip()
    missing = [k for k in ('name', 'url', 'topic', 'key', 'version') if k not in out]
    if missing:
        raise SystemExit('site.conf: не хватает полей %s' % ', '.join(missing))
    return out
