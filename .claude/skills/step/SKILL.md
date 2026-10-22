---
name: step
description: Writes a step document (the full work order) with exactly three checkable predicates before any code is typed. Holds the stop crane: without approved predicates, no product file is touched.
---

# Skill · Writing the step document

Use this whenever the Architect asks for a new page, a new section, a change or "just do this".

## 1. The stop crane

No product file is touched. Not a page, not `style.css`, not `site.conf`. The only file you may write first is the step document itself, `lessons/step-N.md`.

## 2. The goal, in one sentence

State what must **exist** when the work is done. Not "improve the site", but "page `01.html` holds the six mechanisms the rest of the site builds on, in Russian".

## 3. Exactly three predicates

A predicate is a statement you can answer yes or no by looking at the result.

- **Forbidden:** evaluative words. Beautiful, convenient, modern, clear, high-quality.
- **Allowed:** facts. This heading exists; there are no fewer than six sections; `./check.sh` prints ЗЕЛЁНОЕ; the menu item became a link.
- **At least one predicate must be checked by a machine.** If all three are checked by eye, the step closes on an opinion instead of a fact.
- **A vague request is not grounds for interrogation.** Offer two concrete options with their costs and leave room for a third.

## 4. Boundaries

Write down separately what the step does **not** include, and move each item to `lessons/backlog.md` as one line: what · why it is needed · **why not now**. The third field is what separates a decision from forgetfulness. A boundary is as much part of the step as a predicate.

## 5. The draft goes into the file

Write the goal, the three predicates and the boundaries into `lessons/step-N.md`, where N is the current step number.

## 6. Stop

Show the predicates and stop:

> "The predicates are in `lessons/step-N.md`. Read them and correct them: they are yours, not mine. Say the word and I start typing."

Work begins only after that word. Until then, the answer to "just do it quickly" is a polite refusal and a pointer to this stop crane.

## 7. When the work is done

The record goes into `lessons/record-N.md`: what was typed, what the predicates say, what each check printed. When the Conductor explicitly approves the delivery in chat (e.g. "Раздел N принят", "принято"), the AI records the acceptance verdict in the table, indicating a working review authorizing progression to the next step without precluding future refinements. Always conclude the delivery report with an explicit, low-cost choice of next steps for the Conductor (or explicitly state that no forks remain). Before executing any command blocks during the work, always output a single-sentence micro-goal (`**Микро-цель:** ...`) explaining what is being done and why tokens are spent.

## 8. Structural numbering invariants

Every page typed under a step must follow the series numbering contract:
- **Level 1 (Topic navigation):** Sidebar `<nav class="contents">` holds 15 topics, each explicitly carrying `<span class="num">N</span>` before the topic title.
- **Level 2 (In-page topic sections):** Substantive sections on pages 01-12 are numbered sequentially: `<h2 id="...">N · Title <a class="anchor-link" href="#...">#</a></h2>`. Only "Главная мысль страницы" and "Артефакты" remain unnumbered.

## 9. The Noob / Pro / IGL scale and gaming philosophy

The series views technical growth as an engaging game:
- **Noob:** learning core mechanics and eliminating magic.
- **Pro:** reliable execution, avoiding silent failures, clean teamwork.
- **IGL (In-Game Leader):** architectural vision, setting the rules of engagement, and leading under pressure. Learning, work, business, and complexity are demanding yet captivating games. IGL is strictly "In-Game Leader", never "Internal Guild Lead".

## 10. No hard line breaks in Markdown files

Paragraphs, list items, and blockquotes must be written as single continuous lines of text without manual line wrapping at arbitrary columns (such as 80 or 100 characters). Hard newlines are used only between structural blocks (headings, paragraphs, list items, code blocks, tables). Editors handle visual soft-wrapping; single-line prose ensures clean, minimal git diffs and prevents formatting degradation over time.

## 11. Practical example chapters (10-12)

Practical chapters cover 6-7 battle-tested scenarios per chapter (18-21 per course). Each scenario follows the strict triad: `<p><strong>Задача:</strong> ...</p>`, `<pre><code>...</code></pre>`, `<div class="prints"><strong>Почему так:</strong> ...</div>`. Multi-column `<table>` elements are forbidden due to 390px mobile viewport overflow. Each practical chapter declares at least 3 machine-checkable claims in `tools/claims.tsv`.

## 12. Question banks (13-15)

Question banks contain strictly 50 questions per chapter (150 per course). Subsections group questions by tens: `1 · Вопросы (1-10)` .. `5 · Вопросы (41-50)`. Each question provides a clear title, complete answer, and cross-links to glossary terms.

## 13. Batched course delivery (4-5 steps per track)

Instead of 19 single-page micro-shifts, a track is delivered in 4-5 coherent batches: Batch 1 (Setup, Landing, Topics 01-05); Batch 2 (Topics 06-09); Batch 3 (Examples 10-12); Batch 4 (Questions 13-15, Glossary, Navigator); Batch 5 (Polish & Release). Fast checks during drafting use `./tools/check-fast.sh` (or `./check.sh --fast`), reserving full `./check.sh` runs for batch deliveries.

## 14. Prompting /compact on clean git trees

At the end of every delivery record or when a batch is committed and the working tree is clean, the pilot must explicitly remind the Conductor in the next-step fork that the tree is clean and recommend executing `/compact` to reset context and prevent token budget exhaustion.
