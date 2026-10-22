---
name: site-bootstrap
description: Guides the initialization and bootstrapping of a brand-new course site of the AI Factory series from seed/swa, setting up git branches (main, dev, prod), verifying 10/10 green checks out-of-the-box, and preparing Batch 1 under the stop crane.
---

# Skill · Site Bootstrap and Initialization

Use this skill whenever starting a brand-new course site of the AI Factory series (e.g. `docker`, `newrelic`, or any course from `assess-tracks` or `study-tracks`) from absolute scratch.

## 1. Parameters of the Site

Identify the five parameters of the new site with the Conductor:
- `<target-dir>`: destination path, e.g. `../../courses/docker`
- `<site-name>`: header brand, e.g. `devops-docker`
- `<topic-chip>`: amber chip in the header, e.g. `Docker`
- `<storage-key>`: local storage and cookie key prefix, e.g. `docker`
- `[search-word]`: initial smoke search term (defaults to topic word, e.g. `container` or `образ`)

## 2. Execute Bootstrap from the Seed

From the shared seed directory `seed/swa/`:
```bash
cd /home/ik/lab/ai-factory-builder/seed/swa
./bootstrap.sh ../../courses/<repo> <site-name> "<topic-chip>" <storage-key> <search-word>
```

What this does automatically:
- Copies the static SWA engine, assets, checks, and harness.
- Writes `site.conf` with site-specific metadata.
- Stamps all 73 HTML pages (landing page `index.html`, 15 topics, `glossary.html`, `navigator.html` across `ru`, `en`, `uk`, `de`, plus root `index.html` language door).
- Builds initial navigation (`build-nav.py`), metadata (`build-meta.py`), and search index (`build-search.py`).
- Removes seed scaffolding (`pages/`, `tools/new-site.py`).

## 3. Playwright Symlink and Git Setup

Switch to the newly stamped directory:
```bash
cd /home/ik/lab/ai-factory-builder/courses/<repo>
ln -s ../../node_modules node_modules
```

Initialize git repository and branches:
```bash
git init -b main
git add -A && git commit -m "feat(site): stamp initial course scaffold from seed"
git branch prod main
git checkout -b dev main
```

**Branch Architecture Invariants:**
- `main`: root baseline stamped from the seed.
- `prod`: release branch for GitHub Pages publication. Must branch strictly from `main` (`git branch prod main`), NEVER directly from `dev`. Releases are merged into `prod` using `--no-ff` nodes.
- `dev`: active working branch where AI pilots and engineers build content and run checks.

## 4. Immediate Machine Verification

Run the full test suite before touching any file:
```bash
./check.sh
```

The check MUST print `ЗЕЛЁНОЕ` (10/10 checks passing) on the freshly stamped site right out of the box:
- [ ДА ] страница и заголовок
- [ ДА ] оболочка и навигация
- [ ДА ] утверждения сайта
- [ ДА ] примеры запускаются
- [ ДА ] ссылки и якоря
- [ ДА ] термины и словарь
- [ ДА ] пунктуация
- [ ДА ] индекс поиска
- [ ДА ] данные страниц
- [ ДА ] телефон и панель

## 5. Remote and GitHub Pages Connection (Architect/Conductor Action)

If a remote repository on GitHub (`y-kolyada/<repo>`) is created:
```bash
git remote add origin git@github.com:y-kolyada/<repo>.git
git push -u origin main
git push -u origin prod
git push -u origin dev
gh repo edit y-kolyada/<repo> --default-branch main
gh api --method POST repos/y-kolyada/<repo>/pages -f source[branch]=prod -f source[path]=/
```

## 6. Handing Off to Batch 1 and Stop Crane

Once the scaffold is green and branches are established:
1. Activate the `step` skill to formulate `lessons/step-1.md`.
2. Follow Rule §5.15 (Batched shift delivery model) - target **Batch 1 (Setup, Landing index.html, Topics 01-05)**.
3. Formulate the goal, strictly three machine-checkable predicates, and explicit boundaries.
4. Stop and await the Conductor's explicit approval word ("делаем") before authoring any content.
