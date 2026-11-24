#!/usr/bin/env python3
"""
Pull daily contribution counts from GitHub's public contributions fragment
(the same HTML the profile page loads) and write data/contributions.json with
the raw days plus the stats the cards show.

Also counts public repos (own vs forked) through the REST API, using
GITHUB_TOKEN when the workflow provides it.

Run daily by .github/workflows/update-profile-cards.yml.
"""
import datetime
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

USER = os.environ.get("GH_PROFILE_USER", "atharv1205")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "data", "contributions.json")
UA = {"User-Agent": f"{USER}-profile-cards/1.0"}


def fetch_days():
    r = requests.get(f"https://github.com/users/{USER}/contributions", headers=UA, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tips = {t.get("for"): t.get_text(strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        date = td.get("data-date")
        if not date:
            continue
        text = tips.get(td.get("id"), "")
        m = re.match(r"(\d[\d,]*)", text)
        count = int(m.group(1).replace(",", "")) if m and not re.search(r"no contributions", text, re.I) else 0
        days.append({"date": date, "count": count, "level": int(td.get("data-level") or 0)})
    if not days:
        sys.exit("no calendar cells found; GitHub markup may have changed")
    return sorted(days, key=lambda d: d["date"])


def fetch_repo_counts():
    headers = dict(UA)
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    own = forks = 0
    page = 1
    while True:
        r = requests.get(f"https://api.github.com/users/{USER}/repos",
                         params={"per_page": 100, "page": page, "type": "owner"},
                         headers=headers, timeout=30)
        if r.status_code != 200:
            return None
        batch = r.json()
        if not batch:
            break
        for repo in batch:
            if repo.get("fork"):
                forks += 1
            else:
                own += 1
        page += 1
    return {"own": own, "forks": forks}


def streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)
    i = len(days) - 1
    if days[i]["count"] == 0:
        i -= 1  # today isn't over yet
    current = 0
    while i >= 0 and days[i]["count"]:
        current += 1
        i -= 1
    return current, longest


def build(days, repos):
    monthly = {}
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]
    best = max(days, key=lambda d: d["count"])
    current, longest = streaks(days)
    return {
        "username": USER,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": sum(d["count"] for d in days),
        "active_days": sum(1 for d in days if d["count"]),
        "day_count": len(days),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": [{"month": k, "total": v} for k, v in sorted(monthly.items())],
        "repos": repos,
        "days": days,
    }


if __name__ == "__main__":
    previous = {}
    if os.path.exists(OUT):
        with open(OUT) as f:
            previous = json.load(f)
    data = build(fetch_days(), fetch_repo_counts() or previous.get("repos"))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(data, f, indent=1)
    print(f"{data['total']} contributions, streak {data['current_streak']} (longest {data['longest_streak']})")
