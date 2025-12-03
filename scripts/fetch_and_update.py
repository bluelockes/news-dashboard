import feedparser
import json
import os
import requests
from datetime import datetime

OPENAI_KEY = os.getenv("OPENAI_API_KEY")

RSS_FEEDS = [
    ("Reuters", "https://www.reutersagency.com/feed/?best-topics=world&&post_type=best"),
    ("BBC", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("AP", "https://apnews.com/hub/ap-top-news?output=rss")
]

DB_PATH = "data/news.json"


def load_db():
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, "r") as f:
        return json.load(f)


def save_db(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


import requests
import os

def translate_text(text):
    api_key = os.getenv("OPENAI_API_KEY")

    url = "https://api.openai.com/v1/responses"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-4o-mini",
        "input": f"Translate this news headline into Thai:\n{text}",
        "max_output_tokens": 200
    }

    r = requests.post(url, headers=headers, json=data)
    res = r.json()

    # --- ตัวใหม่: responses API ---
    try:
        return res["output"][0]["content"][0]["text"]
    except:
        pass

    # fallback
    return f"[TRANSLATION ERROR] raw_response: {res}"



def main():
    db = load_db()
    existing_links = {item["link"] for item in db}

    new_items = []

    for source, url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            if entry.link in existing_links:
                continue

            translated = translate_text(f"{entry.title}\n{entry.link}")

            item = {
                "source": source,
                "title": entry.title,
                "link": entry.link,
                "translated": translated,
                "timestamp": datetime.utcnow().isoformat()
            }
            new_items.append(item)

    if new_items:
        db = new_items + db
        db = db[:200]  # เก็บเฉพาะ 200 ข่าวล่าสุด
        save_db(db)


if __name__ == "__main__":
    main()
