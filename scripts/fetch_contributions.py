#!/usr/bin/env python3
"""
fetch_contributions.py — scrape the public contribution calendar.

No token needed: GitHub serves the calendar as public HTML at
https://github.com/users/<username>/contributions — the same fragment
the profile page itself uses. We parse the day cells and write
data/contributions.json with raw days plus derived stats.
"""
import datetime as dt
import json
import os
import sys

import requests
from bs4 import BeautifulSoup

USERNAME = "rakshitaryan0-wq"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = os.path.join("data", "contributions.json")


def fetch_days() -> list[dict]:
    resp = requests.get(URL, timeout=30, headers={
        "User-Agent": "profile-art-heatmap (github.com/" + USERNAME + ")"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    cells = soup.select("td.ContributionCalendar-day[data-date]")
    if not cells:  # older markup fallback
        cells = soup.select("[data-date][data-level]")
    if not cells:
        sys.exit("no day cells found — GitHub markup may have changed")

    # Counts can live in tool-tip elements keyed by cell id.
    tips = {}
    for tip in soup.select("tool-tip[for]"):
        tips[tip.get("for")] = tip.get_text(" ", strip=True)

    days = []
    for c in cells:
        date = c["data-date"]
        level = int(c.get("data-level", 0))
        count = 0
        txt = tips.get(c.get("id"), "") or c.get_text(" ", strip=True)
        for tok in txt.replace(",", "").split():
            if tok.isdigit():
                count = int(tok)
                break
        days.append({"date": date, "count": count, "level": level})

    days.sort(key=lambda d: d["date"])
    return days


def derive_stats(days: list[dict]) -> dict:
    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"], default=None)

    # Streaks (current streak counts backwards from the last day with
    # data; today having 0 doesn't break it, the day is just ongoing).
    longest = cur = 0
    for d in days:
        cur = cur + 1 if d["count"] > 0 else 0
        longest = max(longest, cur)

    current = 0
    for d in reversed(days):
        if d["count"] > 0:
            current += 1
        elif current == 0 and d is days[-1]:
            continue  # today may still be empty
        else:
            break

    monthly: dict[str, int] = {}
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]

    return {
        "total": total,
        "best_day": best,
        "current_streak": current,
        "longest_streak": longest,
        "monthly": monthly,
    }


def main() -> None:
    days = fetch_days()
    data = {
        "username": USERNAME,
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sample": False,
        "days": days,
        "stats": derive_stats(days),
    }
    os.makedirs("data", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    print(f"wrote {OUT}: {len(days)} days, "
          f"{data['stats']['total']} contributions")


if __name__ == "__main__":
    main()
