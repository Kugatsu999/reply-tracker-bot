import time
import csv
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
from datetime import datetime, timezone

# --- 設定 ---
TARGET_URL = "https://x.com/rai5s9t/with_replies"
MAX_USERS = 15  # 最大取得件数
COOKIES_FILE = "cookies.json"  # 追加ポイント

# --- Seleniumセットアップ ---
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

print(f"▶️ {TARGET_URL} を取得中…")
driver.get("https://x.com/")  # 最初はトップにアクセス
time.sleep(3)

# --- 🍪 Cookieをセット ---
if Path(COOKIES_FILE).exists():
    with open(COOKIES_FILE, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    for cookie in cookies:
        if "sameSite" in cookie and cookie["sameSite"] == "None":
            cookie["sameSite"] = "Strict"  # GitHub Actions上の問題回避
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            print(f"Cookieセット失敗: {e}")

# --- 本来のターゲットページへアクセス ---
driver.get(TARGET_URL)
time.sleep(5)

reply_targets = []
last_height = driver.execute_script("return document.body.scrollHeight")

def collect_replies():
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    new_targets = 0

    for article in soup.find_all("article"):
        time_tag = article.find("time")
        if not time_tag or not time_tag.has_attr("datetime"):
            continue
        post_time = datetime.fromisoformat(time_tag["datetime"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - post_time
        if delta.total_seconds() > 3600:
            continue  # 1時間以上前ならスキップ

        reply_to_span = article.find("span", string=re.compile(r"^@[a-zA-Z0-9_]+$"))
        if reply_to_span:
            handle = reply_to_span.text.strip().replace("@", "")
            if handle.lower() != "rai5s9t" and handle not in reply_targets:
                reply_targets.append(handle)
                new_targets += 1
                print(f"🆕 追加: {handle}（{int(delta.total_seconds() / 60)}分前）")
                if len(reply_targets) >= MAX_USERS:
                    return new_targets
    return new_targets

# --- 初回収集 ---
collect_replies()

# --- スクロールしながら追加収集 ---
for _ in range(30):
    if len(reply_targets) >= MAX_USERS:
        break

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2.5)
    new_height = driver.execute_script("return document.body.scrollHeight")

    if new_height == last_height:
        print("🔚 スクロール限界に到達")
        break
    last_height = new_height

    new_found = collect_replies()
    if new_found == 0:
        print("🔍 新しいリプライは見つからず")
        break

driver.quit()

# --- 結果をCSVに保存 ---
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"replied_user_ids_{timestamp}.csv"
Path(filename).write_text("replied_user_id\n" + "\n".join(reply_targets), encoding="utf-8")

print(f"✅ {len(reply_targets)} 件のリプライ先ユーザーIDを {filename} に保存しました。")
