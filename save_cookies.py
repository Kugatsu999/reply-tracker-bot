from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json

# Chromeリモートデバッグに接続
options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=options)

# クッキーを取得して保存
cookies = driver.get_cookies()
with open("cookies.json", "w", encoding="utf-8") as f:
    json.dump(cookies, f, indent=2, ensure_ascii=False)

print("✅ Cookiesを cookies.json に保存しました！")

driver.quit()
