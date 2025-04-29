import time
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
from datetime import datetime, timezone

TARGET_URL = "https://x.com/rai5s9t/with_replies"
MAX_USERS = 15

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

print(f"▶️ {TARGET_URL} を取得中…")
driver.get(TARGET_URL)
time.sleep(5)

reply_targets = []
last_height = 0

def collect_from_page():
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    for article in soup.find_all("article"):
        time_tag = article.find("time")
        if not time_tag or not time_tag.has_attr("datetime"):
            continue
        post_time = datetime.fromisoformat(time_tag["datetime"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - post_time
        if delta.total_seconds() > 3600:
            continue

        reply_to_span = article.find("span", string=re.compile(r"^@[a-zA-Z0-9_]+$"))
        if reply_to_span:
            handle = reply_to_span.text.strip().replace("@", "")
            if handle.lower() != "rai5s9t" and handle not in reply_targets:
                reply_targets.append(handle)
                print(f"🆕 追加: {handle}（{int(delta.total_seconds() / 60)}分前）")
                if len(reply_targets) >= MAX_USERS:
                    return

collect_from_page()

for _ in range(30):
    if len(reply_targets) >= MAX_USERS:
        break
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        print("🔚 スクロール限界")
        break
    last_height = new_height
    collect_from_page()

driver.quit()

# 書き出し
filename = f"replied_user_ids_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
with open(filename, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["replied_user_id"])
    for uid in reply_targets:
        writer.writerow([uid])
print(f"✅ {len(reply_targets)} 件のIDを {filename} に保存")
