"""
Script 01 — Parse & Clean the Twitter Archive
==============================================

INPUT:  visakanv_twitter_archive.json (Community Archive / Twitter data export format)
OUTPUT: data/tweets_cleaned.json

WHAT THIS DOES:
    Loads the raw archive JSON and produces a clean, flat list of tweet objects
    with only the fields we actually need. It filters out:
      - Retweets (RT @...) — we only want Visa's original voice
      - Non-English tweets — embeddings work best within one language
      - Tweets with empty or very short text — not useful for semantic clustering

    It also flags self-replies, which are how threads work on Twitter. When Visa
    replies to himself, that's a thread continuation — a building block for the
    city's "buildings" (individual threads).

OUTPUT FIELDS per tweet:
    id            — tweet ID string (unique identifier)
    text          — full tweet text (unicode, emoji preserved)
    date          — ISO 8601 datetime string (e.g. "2022-03-15T14:30:00+00:00")
    likes         — integer like count at time of archive export
    retweets      — integer retweet count at time of archive export
    reply_to_id   — ID of parent tweet if this is a reply, else null
    is_self_reply — True if replying to own tweet (thread continuation)

WHY THIS MATTERS FOR THE CITY:
    Thread structure (self-replies) is how we'll group tweets into "buildings".
    A thread = a building. A standalone tweet = a small kiosk or street stall.
    The likes count determines building size and whether it becomes a landmark.
"""

import json
from pathlib import Path
from datetime import datetime

# ─── Configuration ────────────────────────────────────────────────────────────

# Path to the raw archive file.
# Place the archive JSON in the project root and rename it, or update this path.
ARCHIVE_PATH = Path(__file__).parent.parent / "visakanv_twitter_archive.json"

# Where cleaned output goes. This path is relative to the project root.
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "tweets_cleaned.json"

# Visa's Twitter account ID — used to detect self-replies (thread continuations)
ACCOUNT_ID = "16884623"

# Filter out tweets shorter than this (likely noise, @mentions with no content, etc.)
MIN_TEXT_LENGTH = 20

# ─── Helpers ──────────────────────────────────────────────────────────────────

def parse_date(date_str):
    """Convert Twitter's date format to ISO 8601.

    Twitter format: "Fri Sep 27 16:20:19 +0000 2024"
    Output format:  "2024-09-27T16:20:19+00:00"
    """
    dt = datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y")
    return dt.isoformat()


def is_retweet(tweet):
    """Retweets always start with 'RT @'. Simple and reliable."""
    return tweet["full_text"].startswith("RT @")


def clean_tweet(raw):
    """Extract and normalize the fields we care about from a raw tweet dict."""
    t = raw["tweet"]
    return {
        "id":            t["id_str"],
        "text":          t["full_text"],
        "date":          parse_date(t["created_at"]),
        "likes":         int(t.get("favorite_count", 0)),
        "retweets":      int(t.get("retweet_count", 0)),
        "reply_to_id":   t.get("in_reply_to_status_id_str") or None,
        "is_self_reply": t.get("in_reply_to_user_id_str") == ACCOUNT_ID,
    }

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Script 01 — Parse & Clean Archive")
    print("=" * 60)

    # Load the raw archive
    print(f"\nLoading archive from:\n  {ARCHIVE_PATH}")
    print("(This may take a moment — the file is large...)")
    with open(ARCHIVE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_tweets = data["tweets"]
    print(f"\nRaw tweet count: {len(raw_tweets):,}")

    # Filter and clean
    cleaned = []
    skipped = {"retweet": 0, "non_english": 0, "too_short": 0}

    for raw in raw_tweets:
        t = raw["tweet"]

        if is_retweet(t):
            skipped["retweet"] += 1
            continue

        if t.get("lang") != "en":
            skipped["non_english"] += 1
            continue

        text = t["full_text"].strip()
        if len(text) < MIN_TEXT_LENGTH:
            skipped["too_short"] += 1
            continue

        cleaned.append(clean_tweet(raw))

    # Summary
    print(f"\nFiltered out:")
    print(f"  {skipped['retweet']:>7,} retweets")
    print(f"  {skipped['non_english']:>7,} non-English tweets")
    print(f"  {skipped['too_short']:>7,} tweets under {MIN_TEXT_LENGTH} characters")
    print(f"\nKept: {len(cleaned):,} original English tweets")

    # Stats on what we kept
    self_replies  = sum(1 for t in cleaned if t["is_self_reply"])
    total_likes   = sum(t["likes"] for t in cleaned)
    landmarks     = sum(1 for t in cleaned if t["likes"] >= 1000)
    hidden_alleys = sum(1 for t in cleaned if t["likes"] == 0)

    # Tweets are newest-first in the archive, so reverse for date range display
    oldest_date = cleaned[-1]["date"][:10]
    newest_date = cleaned[0]["date"][:10]

    print(f"\nArchive stats:")
    print(f"  Date range:              {oldest_date} → {newest_date}")
    print(f"  Self-replies (threads):  {self_replies:,}")
    print(f"  Potential landmarks      {landmarks:,}  (≥1,000 likes)")
    print(f"  Hidden alleys:           {hidden_alleys:,}  (0 likes)")
    print(f"  Total likes across all:  {total_likes:,}")

    # Save
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to: {OUTPUT_PATH}")
    print("\nNext step: run 02_embed_sample.py")


if __name__ == "__main__":
    main()
