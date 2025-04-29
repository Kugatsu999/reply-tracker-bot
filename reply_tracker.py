import time
import csv
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

TARGET_URL = "https://x.com/rai5s9t/with_replies"
MAX_USERS = 15

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--remote-debugging-port=9222")
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
        if (now - post_time).total_seconds() > 3600:
            continue
        handles = article.find_all("span")
        for span in handles:
            handle = span.text.strip().replace("@", "")
            if handle.lower() != "rai5s9t" and handle not in reply_targets:
                reply_targets.append(handle)
                print(f"🆕 追加: {handle}")
                if len(reply_targets) >= MAX_USERS:
                    return

# 最初の読み込み分
collect_from_page()

# スクロールしながら追加収集
for _ in range(30):
    if len(reply_targets) >= MAX_USERS:
        break
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2.5)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height
    collect_from_page()

# 書き出し
filename = f"replies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
with open(filename, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["replied_user_id"])
    for uid in reply_targets:
        writer.writerow([uid])
print(f"✅ {len(reply_targets)} 件を {filename} に保存しました。")
