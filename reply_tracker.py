import time
import csv
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
from datetime import datetime, timezone

# --- 設定 ---
TARGET_URL = "https://x.com/rai5s9t/with_replies"
MAX_USERS = 15  # 最大取得件数

# --- Seleniumセットアップ（GitHub Actions対応）---
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)

print(f"▶️ {TARGET_URL} を取得中…")
driver.get(TARGET_URL)
time.sleep(5)

reply_targets = []
last_height = 0

# --- 初回チェック（スクロール前） ---
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
                break

# --- スクロールしながらチェック ---
for _ in range(30):  # 最大30回スクロール
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
                    break

    if len(reply_targets) >= MAX_USERS:
        break

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2.5)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        print("🔚 スクロール限界に到達")
        break
    last_height = new_height

# --- 結果をCSV保存（GitHub Actions対応） ---
filename = "replies.csv"
with open(filename, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["replied_user_id"])
    for uid in reply_targets:
        writer.writerow([uid])

print(f"✅ {len(reply_targets)} 件のリプライ先ユーザーIDを {filename} に保存しました。")
