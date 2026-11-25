#!/usr/bin/env python3
"""Build the PUBLIC internship list from companies' own job boards (Greenhouse, Lever, Ashby public APIs).

This script is deliberately separate from the private pipeline: it reads no profile, resume, experience bank,
mail, score or result file, and it never touches LinkedIn. Its only inputs are the public job board APIs and the
list of company board names below. Its only outputs are README.md and jobs.json.

  python3 public_list.py <output folder> [--template README.template.md]
"""
import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import geo

# Candidate board names. A name that does not exist is simply skipped, so it is cheap to add more.
BOARDS = {
    "greenhouse": """affirm airbnb airtable alchemy amplitude andurilindustries anthropic applovin arcadia asana attentive
        axon benchling benchsci betterment block brex bytedance carta chime cloudflare cockroachlabs coinbase confluent
        coursera coveo crunchyroll databricks datadog deepmind discord doordashusa dropbox duolingo elastic faire
        fastly figma fivetran flexport gitlab glean gusto hootsuite hubspotjobs instacart intercom janestreet
        jumptrading khanacademy lattice lightspeedhq lyft marqeta mercury mongodb neuralink nuro okta opendoor
        pagerduty peloton pinterest planetlabs postman qualtrics quora reddit relativity remitly robinhood roblox
        rubrik samsara scaleai seatgeek singlestore smartsheet sofi spacex squarespace stripe sumologic tailscale
        thumbtack toast tripadvisor twilio twitch verkada vimeo waymo webflow wise xai zocdoc zscaler
        hudsonrivertrading imc optiver drweng akunacapital towerresearchcapital virtu point72 aquaticcapitalmanagement
        appliedintuition aurorainnovation lucidmotors rocketlab astranis hermeus relationalai magnetforensics
        d2l kinaxis ssense applyboard wattpad ecobee fullscript jobber vena trulioo dapperlabs""".split(),
    "lever": """palantir plaid netflix voleon belvederetrading wealthsimple spotify mistral ro brillio matchgroup zoox
        shieldai attentive kraken ledger nielsen veeva outreach highspot clari saviynt cyngn aledade kinsta
        mosaic ritual wattpad lightspeedhq hopper snapcommerce wave pointclickcare achievers ada league tulip
        geotab""".split(),
    "ashby": """1password ada airwallex anysphere ashby baseten benchling bland-ai browserbase clerk cohere cursor decagon
        deel docker drata elevenlabs harvey hopper kalshi koho lambda langchain linear modal notion openai opensea
        perplexity pinecone plaid posthog ramp reducto replicate replit retool runway sierra snowflake stytch
        supabase suno temporal vanta vercel warp watershed wealthsimple writer zapier neofinancial float
        properly clio tailscale""".split(),
}
URLS = {"greenhouse": "https://boards-api.greenhouse.io/v1/boards/{}/jobs",
        "lever": "https://api.lever.co/v0/postings/{}?mode=json",
        "ashby": "https://api.ashbyhq.com/posting-api/job-board/{}"}

INTERN = re.compile(r"\b(intern|interns|internship|internships|co-?op|coop)\b", re.I)
SOFTWARE = re.compile(r"software|developer|\bswe\b|\bsde\b|back.?end|front.?end|full.?stack|mobile|\bios\b|android|"
                      r"platform|infrastructure|devops|site reliability|machine learning|\bml\b|\bai\b|data engineer|"
                      r"security engineer|firmware|embedded|programmer|web ", re.I)
EXCLUDE = re.compile(r"\b(senior|sr|staff|principal|manager|director|head of|architect|mba|phd|ph\.d|marketing|sales|"
                     r"recruit\w*|designer|mechanical|electrical|civil|legal|finance|accounting)\b", re.I)
WINTER = re.compile(r"winter\s*(20)?27|(20)?27\s*winter|\bjan(uary|\.)?\s*(to|-|–)?\s*(\w+\s*)?(20)?27\b", re.I)
SUMMER = re.compile(r"summer\s*(20)?27|(20)?27\s*summer|\bsummer\b(?!.*20(2[0-6]|2[89]))", re.I)
PAST = re.compile(r"\b(2024|2025|2026)\b")


def term_of(title):
    if WINTER.search(title):
        return "Winter 2027"
    if SUMMER.search(title):
        return "Summer 2027"
    return "Other terms"


def wanted(title, location):
    if not (INTERN.search(title) and SOFTWARE.search(title)) or EXCLUDE.search(title):
        return False
    if PAST.search(title) and "2027" not in title:
        return False                                  # an earlier year's posting left open
    return geo.in_scope(location)


def parse(platform, company, data):
    """Yield {company, title, location, url} from one board's API response."""
    if platform == "greenhouse":
        for job in data.get("jobs", []):
            yield {"company": job.get("company_name") or company, "title": job.get("title", ""),
                   "location": (job.get("location") or {}).get("name", ""), "url": job.get("absolute_url", "")}
    elif platform == "lever":
        for job in data if isinstance(data, list) else []:
            categories = job.get("categories") or {}
            places = categories.get("allLocations") or [categories.get("location", "")]
            yield {"company": company, "title": job.get("text", ""), "location": " / ".join(p for p in places if p),
                   "url": job.get("hostedUrl", "")}
    elif platform == "ashby":
        for job in data.get("jobs", []):
            places = [job.get("location", "")] + [s.get("location", "") for s in job.get("secondaryLocations") or []]
            if job.get("isListed", True):
                yield {"company": company, "title": job.get("title", ""),
                       "location": " / ".join(p for p in places if p), "url": job.get("jobUrl", "")}


def fetch_board(item, opener=urllib.request.urlopen):
    """(jobs, found) for one board; a missing board or any error is simply empty."""
    platform, name = item
    try:
        request = urllib.request.Request(URLS[platform].format(name), headers={"User-Agent": "internship-list"})
        with opener(request, timeout=25) as response:
            data = json.loads(response.read().decode("utf-8", "replace"))
    except Exception:
        return [], False
    pretty = name.replace("-", " ").title()
    return list(parse(platform, pretty, data)), True


def collect(opener=urllib.request.urlopen, boards=BOARDS, workers=12):
    items = [(platform, name) for platform, names in boards.items() for name in dict.fromkeys(names)]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda item: fetch_board(item, opener), items))
    jobs, seen = [], set()
    for found, _ in results:
        for job in found:
            title, location = " ".join(job["title"].split()), " ".join(job["location"].split())
            if not job["url"].startswith("https://") or not wanted(title, location):
                continue
            key = (job["company"].lower(), title.lower(), location.lower())
            if job["url"] in seen or key in seen:
                continue
            seen.update({job["url"], key})
            jobs.append({**job, "title": title, "location": location, "term": term_of(title)})
    return jobs, sum(1 for _, ok in results if ok)


def with_dates(jobs, previous, today):
    """Keep the date a posting was first listed; new ones get today's date. Gone postings drop out."""
    first = {job["url"]: job.get("added", today) for job in previous}
    return [{**job, "added": first.get(job["url"], today)} for job in jobs]


def _cell(text):
    return str(text).replace("|", "/").replace("[", "(").replace("]", ")").strip()


def render(jobs, template, today):
    sections = []
    order = {"Winter 2027": 0, "Summer 2027": 1, "Other terms": 2}
    for term in sorted(order, key=order.get):
        rows = sorted((j for j in jobs if j["term"] == term),
                      key=lambda j: (not geo.in_canada(j["location"]), j["company"].lower(), j["title"].lower()))
        if not rows:
            continue
        sections.append(f"## {term}\n\n| Company | Role | Location | Added | Apply |\n| --- | --- | --- | --- | --- |")
        sections += [f"| {_cell(j['company'])} | {_cell(j['title'])} | {_cell(j['location'])} | {j['added']} | "
                     f"[Apply]({j['url'].replace(')', '%29')}) |" for j in rows]
        sections.append("")
    table = "\n".join(sections) if sections else "_Check back soon for new roles._\n"
    return (template.replace("{{UPDATED}}", today).replace("{{COUNT}}", str(len(jobs))).replace("{{JOBS}}", table))


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    out = Path(argv[1])
    out.mkdir(parents=True, exist_ok=True)
    template_path = (Path(argv[argv.index("--template") + 1]) if "--template" in argv
                     else Path(__file__).with_name("public-kit") / "README.template.md")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    previous_path = out / "jobs.json"
    previous = json.loads(previous_path.read_text(encoding="utf-8")) if previous_path.exists() else []
    jobs, boards_found = collect()
    if boards_found < 20 and previous:
        raise SystemExit("Too few job boards answered; keeping the previous list rather than publishing a broken one.")
    jobs = with_dates(jobs, previous, today)
    previous_path.write_text(json.dumps(jobs, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    (out / "README.md").write_text(render(jobs, template_path.read_text(encoding="utf-8"), today),
                                   encoding="utf-8", newline="\n")
    counts = {t: sum(1 for j in jobs if j["term"] == t) for t in ("Winter 2027", "Summer 2027", "Other terms")}
    print(f"{boards_found} job boards answered; {len(jobs)} open postings: {counts}; "
          f"in Canada: {sum(1 for j in jobs if geo.in_canada(j['location']))}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
