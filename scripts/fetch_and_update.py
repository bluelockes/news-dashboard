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


def translate_text(text):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Translate the text into Thai. Keep meaning accurate."},
            {"role": "user", "content": text}
        ],
        "max_tokens": 500
    }

    r = requests.post(url, headers=headers, json=payload)

    try:
        data = r.json()
        return data["choices"][0]["message"]["content"]
    except:
        # debug log (เพื่อดูว่ามี error อะไร)
        print("OpenAI API Error:", r.status_code, r.text)
        return "TRANSLATION ERROR"



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
