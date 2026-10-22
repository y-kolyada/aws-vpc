# Brief for a new site of the series

Paste this into a fresh session, with the row of your site filled in.

| Repo (dir) | Site name | Topic chip | Storage key | Search word |
| :-- | :-- | :-- | :-- | :-- |
| `git` | `devops-git` | `Git` | `git` | `rebase` |
| `github-actions` | `devops-github-actions` | `GitHub Actions` | `gha` | `workflow` |
| `terraform` | `devops-terraform` | `Terraform` | `terraform` | `state` |
| `aws-iam` | `devops-aws-iam` | `AWS IAM` | `aws-iam` | `policy` |
| `newrelic` | `sre-newrelic` | `New Relic` | `newrelic` | `NRQL` |

## 1. Stamp the site (one command, from the seed)

```
cd /home/ik/lab/ai-factory-builder/seed/swa
./bootstrap.sh ../../courses/<repo> <site name> "<topic chip>" <storage key> <search word>
```

It copies the seed, writes `site.conf`, stamps 68 pages (Russian skeletons, three languages as stubs), runs the three generators and removes its own scaffolding. Then:

```
cd /home/ik/lab/ai-factory-builder/courses/<repo>
ln -s ../../node_modules node_modules   # the browser check needs playwright
./check.sh
```

The check must be green before any content is written. It is green on a freshly stamped site: measured, all eight lines, on a throwaway stamp.

## 1a. The first commit, and the branches

The repository starts empty on `main`. The stamp is its first commit, work happens on `dev`, and `prod` appears at the first release:

```
git add -A && git commit -m "feat(site): stamp the site from the seed"
git checkout -b dev
```

`.gitignore` comes from the seed and already keeps the `node_modules` symlink and `__pycache__` out of that commit.

## 2. Read the rules

`AGENTS.md` in the site, all of it. Section 1 is the one that matters most: **this repository does not edit `assets/` or `tools/`.** A defect there is one line in `lessons/notes-1.md` and a fix in the seed, once, for every site.

## 3. Write the task before any page

`lessons/step-1.md`: the goal, **exactly three predicates**, the boundaries. Show the predicates to the Conductor and stop. The work starts on the word "делаем".

## 4. The first delivery, when it is approved

Russian only, two pages of real text:

- `ru/index.html` - the landing page: what the site is, who it is for, what the reader leaves with. It holds the reader, so it is not a table of contents in prose.
- `ru/01.html` - the first topic: the mechanisms the rest of the site builds on.
- The fifteen navigation titles and the glossary stay as they are until the Architect approves the plan of sections. Do not invent fifteen names in passing.
- Every claim about the tool is executed before it is published. If the examples cannot be run in this session, the claim does not go on the page.
- Run `python3 tools/build-meta.py`, `python3 tools/build-search.py`, then `./check.sh`.

## 5. Report back

Commit locally, never push. In the report: what the predicates say, the output of `./check.sh`, the word count of the two pages, and anything that belongs in the seed rather than in this site.

