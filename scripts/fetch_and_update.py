import feedparser
import json
import os
import requests
from datetime import datetime

# -----------------------------
# CONFIG
# -----------------------------
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

RSS_FEEDS = [
    ("Reuters", "https://www.reutersagency.com/feed/?best-topics=world&&post_type=best"),
    ("BBC", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("AP", "https://apnews.com/hub/ap-top-news?output=rss")
]

DB_PATH = "data/news.json"
MAX_NEWS = 200


# -----------------------------
# Database Helpers
# -----------------------------
def load_db():
    if not os.path.exists(DB_PATH):
        return []
    try:
        with open(DB_PATH, "r") as f:
            return json.load(f)
    except:
        return []


def save_db(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# -----------------------------
# Translation
# NEW OPENAI API (2025+)
# -----------------------------
def translate_text(text):
    api_key = OPENAI_KEY
    if not api_key:
        return "[TRANSLATION ERROR] Missing OPENAI_API_KEY"

    url = "https://api.openai.com/v1/responses"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "gpt-4o-mini",
        "input": f"Translate this news into Thai:\n{text}",
        "max_output_tokens": 200
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        res = r.json()

        # -------------------------
        # 1) ถ้ามี output_text (ง่ายสุด)
        # -------------------------
        if "output_text" in res:
            return res["output_text"]

        # -------------------------
        # 2) Responses API แบบใหม่
        # -------------------------
        try:
            return res["output"][0]["content"][0]["text"]
        except:
            pass

        # -------------------------
        # 3) Chat-style fallback (บางโมเดลส่งแบบเก่า)
        # -------------------------
        try:
            return res["choices"][0]["message"]["content"]
        except:
            pass

        # -------------------------
        # 4) ถ้าเป็น error จาก API
        # -------------------------
        if "error" in res:
            return f"[TRANSLATION ERROR] {res['error']['message']}"

        # -------------------------
        # 5) ถ้าจับไม่ได้จริง ๆ
        # -------------------------
        return f"[TRANSLATION ERROR] raw_response: {res}"

    except Exception as e:
        return f"[TRANSLATION ERROR] {str(e)}"



# -----------------------------
# Main Logic
# -----------------------------
def main():
    db = load_db()
    existing_links = {item["link"] for item in db}
    new_items = []

    for source, url in RSS_FEEDS:
        feed = feedparser.parse(url)

        for entry in feed.entries[:5]:  # เอา 5 ข่าวล่าสุดจากแต่ละสำนัก
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

    # update DB
    if new_items:
        final_data = new_items + db
        final_data = final_data[:MAX_NEWS]
        save_db(final_data)


if __name__ == "__main__":
    main()
