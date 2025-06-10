import time
import json
from pathlib import Path

import praw
from praw.models import Comment, Submission
from telegram import Bot
import os


# ─── 1. CONFIG ────────────────────────────────────────────────────
REDDIT_CLIENT_ID     = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT    = os.getenv("REDDIT_USER_AGENT")

TELEGRAM_TOKEN       = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID     = int(os.getenv("TELEGRAM_CHAT_ID"))

SEEN_FILE = Path("seen_ids.json")

# ─── 2. HELPER: load & save seen IDs ─────────────────────────────────────────

def load_seen_ids():
    if SEEN_FILE.exists():
        return set(json.loads(SEEN_FILE.read_text()))
    return set()

def save_seen_ids(ids_set):
    SEEN_FILE.write_text(json.dumps(list(ids_set), indent=2))

# ─── 3. INIT REDDIT & TELEGRAM ─────────────────────────────────────

reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

bot = Bot(token=TELEGRAM_TOKEN)

# ─── Sanity check: test Telegram connectivity ──────────────────────────────────

try:
    bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text="✅ WatcherIO bot is configured and alive!"
    )
    print("✅ Telegram test message sent.")
except Exception as e:
    print("❌ Telegram test failed:", e)
    exit(1)

# ─── 4. MAIN LOOP ────────────────────────────────────

def main():
    seen = load_seen_ids()
    print(f"Loaded {len(seen)} seen IDs. Starting loop…")

    while True:
        try:
            for item in reddit.redditor("Still_View_7459").new(limit=10):
                if item.id not in seen:
                    seen.add(item.id)

                    link = f"https://reddit.com{item.permalink}"

                    # ─── Detect type & prepare message ──────────────────────────
                    if isinstance(item, Comment):
                        kind = "Comment"
                        excerpt = item.body[:200]
                        full_text = item.body

                        print("\n🗨️  New Comment:\n" + "-"*50)
                        print(full_text)
                        print(f"\n🔗 Link: {link}")
                        print("-"*50)

                        msg = (
                            f"🆕 New {kind}!\n\n"
                            f"{full_text}\n\n"
                            f"{link}"
                        )

                    elif isinstance(item, Submission):
                        kind = "Post"
                        title = item.title
                        description = item.selftext or "[No Description]"

                        print("\n📄 New Post:\n" + "-"*50)
                        print(f"Title      : {title}")
                        print(f"Description: {description}")
                        print(f"\n🔗 Link: {link}")
                        print("-"*50)

                        msg = (
                            f"🆕 New {kind}!\n\n"
                            f"Title: {title}\n"
                            f"Description: {description}\n\n"
                            f"{link}"
                        )

                    else:
                        continue

                    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
                    print(f"✅ Sent to Telegram: {kind} {item.id}")

            save_seen_ids(seen)

        except Exception as e:
            print("⚠️  Error in main loop:", e)

        time.sleep(10)

if __name__ == "__main__":
    main()
