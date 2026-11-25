# Setup (about 15 minutes)

You need: a GitHub account, a Muse account, your resume as a PDF. Muse's features and free limits change, so check
them in the app.

**Fastest:** clone this repo, open it in Claude Code or Codex, and type `set me up`. The steps below are the same
thing by hand.

## How it fits together
- **This repo (public):** the job list. You only read it.
- **Your repo (private):** your resume, your facts, and Muse's log. Only you and Muse can see it.
- **Muse:** reads both, fills in applications, writes results to your private repo.

## 1. Make your private repo
1. Go to github.com/new. Name it `my-job-pack`.
2. Choose **Private**. Tick **Add a README file**. Create it.
3. Check that the page says **Private** next to the name. If it does not, stop and fix it.

**Do not fork this public repo to hold your files.** A fork of a public repo is public.

## 2. Add your files to the private repo
Use **Add file → Upload files**:
- `resume.pdf`: your resume.
- `experience-bank.md`: copy [templates/experience-bank.md](templates/experience-bank.md) and fill it in. It is the
  only source of facts Muse may use about you, so more detail is better, and only true things.
- `eeo-answers.md` (optional): copy [templates/eeo-answers.md](templates/eeo-answers.md). If you skip it, Muse
  chooses "prefer not to say".
- `results.txt`: an empty file. Muse logs each application here.

Never add: passwords, government ID or social insurance/security numbers, banking details.

## 3. Connect GitHub in Muse
1. In Muse: **Settings → Connectors → GitHub → Connect**.
2. When GitHub asks which repositories, choose **Only select repositories** and pick **only `my-job-pack`**.
3. It needs to read and write file contents (so it can update `results.txt`). If it asks for much more, stop.

## 4. Give Muse its instructions
1. Open [MUSE-PROMPT.md](MUSE-PROMPT.md), copy all of it, and fill in every `[BLANK]`.
2. Paste it into a new Muse chat (or save it in a Muse space, if you have that).
3. Then send: *"Confirm you can read my private repo and the public job list, then start the first job in review
   mode."*

## 5. Review the first applications
Muse fills a form and lists every answer. Check each one, then reply **go**, correct it, or **skip**. Do at least the
first three this way. Look hardest at: work authorization, sponsorship, dates, and anything written in your voice.

## 6. Each day
Send: *"Re-read the job list, skip anything already in results.txt, and continue."*

## Safety notes
- Do not give Muse more access than it needs. It does not need your email to start; if a site emails a code, you can
  paste it yourself.
- If you let it sign in to a site with your password, understand that the site's terms may forbid automation and your
  account could be restricted. Use a unique password and change it if in doubt.
- Do not ask it to get around CAPTCHAs or blocks. Finish those applications yourself.
- Delete your private repo and disconnect the connector when you are done job hunting.
