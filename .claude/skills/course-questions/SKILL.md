---
name: course-questions
description: Guides the design, implementation, and verification of qualification question bank chapters (topics 13-15 · Noob, Pro, IGL) across the AI Factory course series.
---

# Skill · Qualification Question Banks (13-15)

Use this skill whenever working on question bank chapters: topic 13 (Noob), topic 14 (Pro), or topic 15 (IGL).

## 1. Scope and Volume

- **Exact count:** strictly 50 questions per chapter (total 150 questions across topics 13-15).
- **Word floor:** strictly at least 1100 words per chapter (typical target: 1500-2200 words for 50 substantive questions).
- **Audience tiering:**
  - **Topic 13 (Noob):** 50 foundational questions covering fundamental syntax, CLI commands, basic lifecycle, and common pitfalls.
  - **Topic 14 (Pro):** 50 professional questions on team collaboration, error handling, performance tuning, and CI/CD best practices.
  - **Topic 15 (IGL):** 50 systems architecture and leadership questions on security boundaries, compliance, enterprise scale, and infrastructure governance.

## 2. Top-Down Planning (The 5x3 Architecture Matrix)

- **Phase 1 · Architectural Framing:** Before writing any question text, agree with the Conductor on the high-level 5x3 thematic matrix (5 logical blocks of 10 questions for Noob, 5 for Pro, 5 for IGL, total 15 blocks). Never dump 150 individual question texts into the chat upfront; formulate only the concise 1-sentence scope for each 10-question block. This guarantees course-wide balance, eliminates topical overlap, and conserves token budget.
- **Phase 2 · Autonomous Sequential Delivery:** Deliver question banks in strictly 3 independent steps (one chapter per step: Step N -> Topic 13, Step N+1 -> Topic 14, Step N+2 -> Topic 15). Detailed question formulations, comprehensive technical answers, and explicit interview rationale are drafted directly into the target page `ru/<N>.html` under approved step tasks.

## 3. In-Page Grouping and Navigation

- **Headings contract:** Substantive `<h2>` headings group questions into blocks of 10:
  - `<h2 id="q01-10">1 · Вопросы (1-10) <a class="anchor-link" href="#q01-10">#</a></h2>`
  - `<h2 id="q11-20">2 · Вопросы (11-20) <a class="anchor-link" href="#q11-20">#</a></h2>`
  - `<h2 id="q21-30">3 · Вопросы (21-30) <a class="anchor-link" href="#q21-30">#</a></h2>`
  - `<h2 id="q31-40">4 · Вопросы (31-40) <a class="anchor-link" href="#q31-40">#</a></h2>`
  - `<h2 id="q41-50">5 · Вопросы (41-50) <a class="anchor-link" href="#q41-50">#</a></h2>`
- This preserves the two-level numbering invariant and integrates cleanly with the sidebar TOC (`page-toc`).
- Introductory "Главная мысль страницы" and closing "Артефакты" headings remain unnumbered.

## 3. Question Structure

Each question within a group follows a clear, readable structure:
1. **Numbered title:** `<p><strong>N. Clear, direct question formulation?</strong></p>`
2. **Answer and explanation:** Substantive technical explanation covering the mechanism, edge cases, and best practices.
3. **Glossary cross-links:** Connect technical terminology to `glossary.html` via `<a href="glossary.html#term">term</a>`.
4. **Code snippets where helpful:** Compact inline `<code>` or short `<pre><code>` blocks demonstrating exact behavior.

## 4. Mobile Viewport (390px) and Typography Rules

- No wide `<table>` elements that cause horizontal overflow.
- Zero em dashes (`—`, U+2014) anywhere; use spaced hyphen ` - ` or plain hyphen in ranges `(1-10)`.
- No hard line breaks in Markdown documentation.

## 5. Landing Page Harmonization (index.html)

- The landing page (`ru/index.html`) is the showroom of the course and must be harmonized bottom-up with the 150-question qualification matrix under `<h3>Практические сценарии и банки вопросов (главы 10-15)</h3>` and `<h2 id="levels">`.
- Update the corresponding chapter summary bullet on `ru/index.html` so it accurately reflects the real 50 questions delivered in topics 13, 14, and 15 (Вопросы) according to the 5x3 architecture matrix.
- Update the illustrative cross-tier comparison box on the landing page (`<div class="box"><h3>Практический пример: как меняется ответ с ростом уровня</h3>`) to showcase how a single technical question is approached differently by a Noob (mechanics), Pro (reliability and cleanliness), and IGL (systems architecture and security).
- Updating `ru/index.html` is an inescapable step of the delivery: delivering a chapter 13-15 (Вопросы) without synchronizing its bullet on `ru/index.html` is an unaccepted defect (недоделка).

## 6. Delivery Workflow

1. Agree on the 5x3 thematic matrix in chat before drafting questions.
2. Write `lessons/step-N.md` with strictly 3 predicates before editing product files (Predicate 3 must explicitly require `ru/index.html` bottom-up synchronization).
3. Draft all 50 questions in `ru/<N>.html` across the 5 thematic blocks of 10 questions each with answers and interview rationales.
4. Update `ru/index.html` bottom-up: synchronize the chapter overview bullet under `<h3>Практические сценарии и банки вопросов (главы 10-15)</h3>` with the actual questions and blocks delivered.
5. Add at least 3 machine-checkable claims to `tools/claims.tsv` and verify with `./tools/check-claims.sh`.
6. Run build scripts (`python3 tools/build-nav.py && python3 tools/build-meta.py && python3 tools/build-search.py`).
7. Run `./check.sh` (ensure `ЗЕЛЁНОЕ`, 9/9, 0 mobile defects on 390px, 0 em dashes).
8. Commit with scope `feat(content):` or `refactor(page):` and an informative commit body.
9. Record delivery in `lessons/record-N.md` and present to Conductor with an explicit next-step fork.
