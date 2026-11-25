---
name: internship-autopilot
description: Set a person up to apply to internships with Meta's Muse agent using this repo. Use when they say "set me up", "get started", ask how to use this repo, want a job list, or want to add their own job links or companies.
---

# Internship autopilot setup

You are setting this person up so Muse can fill in internship applications for them, with them approving. Do the work
for them wherever you can; ask only what you cannot find out. Keep it friendly and short.

## Rules you must not break
- This repository is PUBLIC. **Never write anything personal into it**: no resume, name, contact details, answers or
  results. Personal files live only in their private folder (default `~/my-job-pack`).
- Never `git commit`, `git push`, create a repo or change repo settings without saying exactly what will happen and
  getting a clear yes. Their private repo must be **private**; verify it before pushing.
- Never ask for passwords, tokens, government ID or banking details. Account logins are done by them, in their browser.
- Write only facts they told you or that are in their resume. Never improve a number or invent experience. Show them
  what you wrote and let them correct it.
- Do not help get around CAPTCHAs, blocks or a site's login rules. Those applications they finish themselves.
- Say plainly that they approve Muse's answers before it submits, and that a submitted answer cannot be taken back.

## Steps
Ask **one question at a time**. Skip anything you already know.

1. **Explain in three lines** what they will end up with: a private repo with their files, a job list, and a prompt to
   paste into Muse. Check Python works (`python --version`; try `python3`). If it is missing, help them install it.
2. **Private folder.** Ask where (default `~/my-job-pack`), then run
   `python scripts/autopilot.py init <folder>`.
3. **Resume.** Ask for the path to their resume PDF and, with their OK, copy it to `<folder>/resume.pdf`.
4. **Experience bank.** If you can read the PDF, draft `<folder>/experience-bank.md` from it using the template's
   headings, then ask them to confirm it and to add anything missing. If you cannot, ask them section by section.
5. **Profile.** Fill `<folder>/profile.json` by asking: GitHub username; terms; countries; acceptable locations;
   graduation month and year, school, program; anything they cannot do; for each country, whether they are legally
   authorized and whether they need sponsorship (use their exact answers; if unsure, tell them to check and do not
   guess); daily limit (suggest 10). Leave demographic questions out unless they ask; if they do, copy
   `templates/eeo-answers.md` to their private folder and say it is sensitive and optional.
6. **Jobs.** Offer three choices and set `job_source` in the profile:
   - `shared`: Muse reads this repo's public list (simplest).
   - `scrape`: their own filtered list from company job boards: `python scripts/autopilot.py jobs <folder>`. They can
     narrow with `only_words` / `skip_words`, and add companies in `extra_boards` (the board name from a
     greenhouse.io, lever.co or ashbyhq.com address). Verify a new board by running the command and checking results.
   - `own`: their own links in any text, CSV or Markdown file:
     `python scripts/autopilot.py jobs <folder> --list <file>`.
   Run the command for `scrape` or `own` and show them the first few lines of `my-jobs.md`.
7. **Prompt.** `python scripts/autopilot.py prompt <folder>`; show it and confirm the work authorization lines.
8. **Private GitHub repo** named `my-job-pack`. If `gh` is installed and logged in, offer:
   `gh repo create my-job-pack --private --source <folder> --push` (after `git init` and a commit there, with their
   yes). Otherwise give web steps: new repo, **Private**, upload the files. Confirm it says Private.
9. **Check:** `python scripts/autopilot.py check <folder>` and fix what it reports.
10. **Muse.** Tell them: Settings, Connectors, GitHub; choose **only** `my-job-pack`; paste the whole of
    `muse-prompt.md`; ask Muse to confirm it can read the files; review the first applications before saying "go".

## Later requests
- "Find new jobs": run `jobs` again (links already in `results.txt` are left out; pull their repo first so the log is
  current), show the changes, and push only with their yes.
- "Add these links / this company": update their list file or `extra_boards`, then run `jobs`.

Finish by telling them exactly what is done, what is left for them, and how to run it tomorrow.
