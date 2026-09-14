"""Fetch today's arXiv announcements (new + cross-listed) for a set of categories
via the official RSS feeds and write them to data/latest.json and data/YYYY-MM-DD.json.
"""
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import feedparser

CATEGORIES = [
    "physics.ao-ph",
    "physics.geo-ph",
    "nlin.CD",
    "math.DS",
    "stat.ML",
    "cs.LG",
    "cs.AI",
]

entries = {}
for cat in CATEGORIES:
    feed = feedparser.parse(f"https://rss.arxiv.org/rss/{cat}")
    for e in feed.entries:
        announce = e.get("arxiv_announce_type", "")
        if announce.startswith("replace"):
            continue  # skip replacements
        m = re.search(r"abs/(\d{4}\.\d{4,5})", e.link)
        if not m:
            continue
        aid = m.group(1)
        abstract = re.sub(r"^.*?Abstract:\s*", "", e.get("summary", ""), flags=re.S).strip()
        cats = [t["term"] for t in e.get("tags", [])]
        rec = entries.setdefault(aid, {
            "id": aid,
            "title": re.sub(r"\s+", " ", e.title).strip(),
            "abstract": abstract,
            "authors": e.get("author", ""),
            "categories": cats,
            "announce_type": announce,
            "link": f"https://arxiv.org/abs/{aid}",
            "seen_in": [],
        })
        rec["seen_in"].append(cat)
    time.sleep(3)  # be polite to arXiv

today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
out = {
    "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "date": today,
    "categories": CATEGORIES,
    "count": len(entries),
    "entries": sorted(entries.values(), key=lambda r: r["id"]),
}
Path("data").mkdir(exist_ok=True)
Path("data/latest.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
Path(f"data/{today}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(f"{len(entries)} entries written for {today}")
