#!/usr/bin/env python3
"""Setup helper for the internship autopilot. Python 3.9+, standard library only.

  python scripts/autopilot.py init   <private-folder>              create your private files
  python scripts/autopilot.py jobs   <private-folder> [--list F]   build your job list (job boards, and/or your own links)
  python scripts/autopilot.py prompt <private-folder>              write your filled-in Muse prompt
  python scripts/autopilot.py check  <private-folder>              what is still missing, and privacy checks

<private-folder> holds YOUR personal files. It must be outside this public repository.
"""
import json
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))

import geo           # noqa: E402
import public_list   # noqa: E402

DEFAULT_PROFILE = {
    "github_username": "",
    "terms": ["Winter 2027", "Summer 2027"],
    "countries": ["Canada", "US"],
    "locations": "",
    "graduation": "",
    "school": "",
    "program": "",
    "cannot": "",
    "authorization": [{"country": "", "authorized": "", "needs_sponsorship": ""}],
    "daily_limit": 10,
    "only_words": [],
    "skip_words": [],
    "extra_boards": {"greenhouse": [], "lever": [], "ashby": []},
    "job_source": "shared",
}
REQUIRED = ("github_username", "locations", "graduation", "school", "program")
SHARED_LIST = "https://github.com/Arhum2/armcodes-internship-autopilot"
URL = re.compile(r"https?://[^\s,|<>()\"']+")


def private_dir(path):
    """The user's private folder, refused if it is the public repository or inside it."""
    folder = Path(path).expanduser().resolve()
    if folder == REPO or REPO in folder.parents:
        raise SystemExit(f"Refusing: {folder} is inside the PUBLIC repository. Choose a folder outside it, "
                         f"for example {Path.home() / 'my-job-pack'}")
    return folder


def load_profile(folder):
    path = folder / "profile.json"
    if not path.exists():
        raise SystemExit("No profile.json yet. Run: python scripts/autopilot.py init <private-folder>")
    return {**DEFAULT_PROFILE, **json.loads(path.read_text(encoding="utf-8"))}


def init(folder):
    folder.mkdir(parents=True, exist_ok=True)
    made = []
    files = {"profile.json": json.dumps(DEFAULT_PROFILE, indent=2) + "\n",
             "experience-bank.md": (REPO / "templates/experience-bank.md").read_text(encoding="utf-8"),
             "results.txt": "# One line per job: date | company | role | status | link | reason\n",
             ".gitignore": "*.log\n.DS_Store\n"}
    for name, content in files.items():
        if not (folder / name).exists():                       # never overwrite what the user already wrote
            (folder / name).write_text(content, encoding="utf-8")
            made.append(name)
    print(f"Private folder: {folder}\nCreated: {', '.join(made) or 'nothing (everything already there)'}\n"
          "Now put your resume there as resume.pdf.")


def read_own_list(path):
    """[{company, title, location, url}] from any text/CSV/Markdown file: every line with a link counts."""
    jobs = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        match = URL.search(line)
        if not match:
            continue
        label = [p.strip(" -*[]#") for p in re.split(r"[,|\t]", line.replace(match.group(0), "")) if p.strip(" -*[]()#")]
        jobs.append({"company": label[0] if label else "", "title": label[1] if len(label) > 1 else "",
                     "location": label[2] if len(label) > 2 else "", "url": match.group(0).rstrip(".")})
    return jobs


def matches(job, profile):
    title = job["title"].lower()
    countries = {c.strip().lower() for c in profile["countries"]}
    in_country = (("canada" in countries and geo.in_canada(job["location"]))
                  or (countries & {"us", "usa", "united states"} and geo.in_us(job["location"])))
    term_ok = job.get("term") == "Other terms" or not profile["terms"] or job.get("term") in profile["terms"]
    only = [w.lower() for w in profile["only_words"]]
    return bool(in_country and term_ok and (not only or any(w in title for w in only))
                and not any(w.lower() in title for w in profile["skip_words"]))


def done_links(folder):
    path = folder / "results.txt"
    return {u.rstrip("/") for u in URL.findall(path.read_text(encoding="utf-8"))} if path.exists() else set()


def jobs(folder, own_list=None, collect=public_list.collect):
    profile = load_profile(folder)
    found = []
    if own_list:
        found += read_own_list(own_list)                       # the user's own links are never filtered out
    if profile["job_source"] != "own" or not own_list:
        boards = {k: list(v) + list(profile["extra_boards"].get(k, [])) for k, v in public_list.BOARDS.items()}
        scraped, answered = collect(boards=boards)
        found += [j for j in scraped if matches(j, profile)]
        print(f"{answered} company job boards answered.")
    skip, seen, rows = done_links(folder), set(), []
    for job in found:
        key = job["url"].rstrip("/")
        if key not in skip and key not in seen:
            seen.add(key)
            rows.append(job)
    order = {"Winter 2027": 0, "Summer 2027": 1}
    rows.sort(key=lambda j: (order.get(j.get("term"), 2), not geo.in_canada(j.get("location", ""))))
    lines = ["# My job list", "", f"{len(rows)} jobs. Apply in order. Skip any link already in results.txt.", ""]
    for i, j in enumerate(rows, 1):
        head = " - ".join(x for x in (j.get("company"), j.get("title"), j.get("location")) if x) or "(see link)"
        lines += [f"{i}. {head}", f"   Link: {j['url']}", ""]
    (folder / "my-jobs.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} jobs to {folder / 'my-jobs.md'}")


def build_prompt(profile, template):
    auth = []
    for a in profile["authorization"]:
        if a.get("country") and a.get("authorized") and a.get("needs_sponsorship"):
            auth += [f"- Legally authorized to work in {a['country']}: {a['authorized']}",
                     f"- Need visa sponsorship now or in the future in {a['country']}: {a['needs_sponsorship']}"]
    missing = [k for k in REQUIRED if not str(profile.get(k, "")).strip()] + ([] if auth else ["authorization"])
    if missing:
        raise SystemExit("profile.json is missing: " + ", ".join(missing))
    if profile["job_source"] == "shared":
        source = f"- Job list (public, read only):\n  {SHARED_LIST}"
    else:
        source = "- Job list: `my-jobs.md` in my private repo."
    values = {"[TERMS]": ", ".join(profile["terms"]) or "any", "[LOCATIONS]": profile["locations"],
              "[GRADUATION]": f"{profile['graduation']}, {profile['school']}, {profile['program']}",
              "[CANNOT]": profile["cannot"] or "nothing in particular", "[USERNAME]": profile["github_username"],
              "[AUTHORIZATION]": "\n".join(auth), "[DAILY]": str(profile["daily_limit"]), "[JOB_SOURCE]": source}
    body = template.split("\n---\n", 1)[-1].strip()
    for token, value in values.items():
        body = body.replace(token, value)
    return body + "\n"


def prompt(folder):
    text = build_prompt(load_profile(folder), (REPO / "MUSE-PROMPT.md").read_text(encoding="utf-8"))
    (folder / "muse-prompt.md").write_text(text, encoding="utf-8")
    print(f"Wrote {folder / 'muse-prompt.md'}. Read it, then paste all of it into Muse.")


def repo_visibility(folder, opener=urllib.request.urlopen):
    """'public', 'not public' or 'unknown' for the folder's GitHub remote, as an anonymous visitor sees it."""
    git = shutil.which("git")
    if not git or not (folder / ".git").exists():
        return "unknown"
    remote = subprocess.run([git, "-C", str(folder), "remote", "get-url", "origin"], capture_output=True, text=True).stdout
    match = re.search(r"github\.com[:/]([^/]+/[^/\s]+?)(?:\.git)?\s*$", remote)
    if not match:
        return "unknown"
    try:
        with opener(f"https://github.com/{match.group(1)}", timeout=15):
            return "public"
    except urllib.error.HTTPError as exc:
        return "not public" if exc.code == 404 else "unknown"
    except Exception:
        return "unknown"


def problems(folder, visibility=repo_visibility):
    found = []
    if visibility(folder) == "public":
        found.append("STOP: your private repo is PUBLIC. Make it private (or delete it) before doing anything else.")
    if not (folder / "resume.pdf").exists():
        found.append("resume.pdf is missing")
    bank = folder / "experience-bank.md"
    template = (REPO / "templates/experience-bank.md").read_text(encoding="utf-8")
    if not bank.exists() or len(bank.read_text(encoding="utf-8")) < len(template) + 200:
        found.append("experience-bank.md is not filled in yet")
    try:
        build_prompt(load_profile(folder), (REPO / "MUSE-PROMPT.md").read_text(encoding="utf-8"))
    except SystemExit as exc:
        found.append(str(exc))
    if not (folder / "muse-prompt.md").exists():
        found.append("muse-prompt.md not written yet (run: prompt)")
    return found


def check(folder):
    found = problems(folder)
    for item in found:
        print(" -", item)
    if not found:
        print("Ready. Make sure the repo is private, connect only that repo in Muse, and paste muse-prompt.md.")
    return 1 if found else 0


def main(argv):
    if len(argv) < 3 or argv[1] not in ("init", "jobs", "prompt", "check"):
        raise SystemExit(__doc__)
    folder = private_dir(argv[2])
    if argv[1] == "init":
        return init(folder)
    if argv[1] == "jobs":
        return jobs(folder, argv[argv.index("--list") + 1] if "--list" in argv else None)
    if argv[1] == "prompt":
        return prompt(folder)
    return check(folder)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
