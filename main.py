import os
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from bs4 import BeautifulSoup
import time

# ===== 台股技術分析 =====
def get_tw_analysis(codes):
    report = "【台股每日技術分析】\n"
    report += "============================\n"
    for code in codes:
        try:
            ticker = yf.Ticker(f"{code}.TW")
            df = ticker.history(period="60d")
            if df.empty:
                ticker = yf.Ticker(f"{code}.TWO")
                df = ticker.history(period="60d")
            price = round(df["Close"].iloc[-1], 2)
            ma5 = round(df["Close"].rolling(5).mean().iloc[-1], 2)
            bias = round(((price - ma5)/ma5)*100, 2)
            if bias <= 2:
                suggest = "🟢 低檔回踩，適合布局"
            elif bias <= 5:
                suggest = "🟡 區間整理，觀望為主"
            else:
                suggest = "🔴 乖離過高，避免追高"
            report += f"標的:{code} 現價:{price} MA5:{ma5} 乖離率:{bias}% 建議:{suggest}\n"
        except Exception as e:
            report += f"{code} 資料取得失敗: {e}\n"
    return report

# ===== 通用新聞請求函數（避免重複程式碼）=====
def fetch_news(url, description):
    news = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        news_items = soup.select("div._1E4L a")[:3]
        for item in news_items:
            title = item.get("title", "無標題")
            link = "https://news.cnyes.com" + item.get("href", "")
            news.append((title, link))
    except Exception as e:
        print(f"DEBUG: {description} 新聞抓取失敗: {e}")
    return news

# ===== 台股大盤新聞 =====
def get_market_news():
    print("DEBUG: 正在抓取台股大盤新聞...")
    news_report = "\n\n【今日台股大盤新聞快訊】\n"
    news_report += "============================\n"
    news_list = fetch_news("https://news.cnyes.com/news/cat/tw_stock", "大盤")
    for idx, (title, link) in enumerate(news_list, 1):
        news_report += f"{idx}. {title}\n  連結: {link}\n\n"
    return news_report

# ===== 個股專屬新聞 =====
def get_stock_news(codes):
    print("DEBUG: 正在抓取個股專屬新聞...")
    news_report = "\n【你持有的個股相關新聞】\n"
    news_report += "============================\n"
    for code in codes:
        news_list = fetch_news(f"https://news.cnyes.com/news/search?q={code}", f"{code}")
        if news_list:
            news_report += f"📌 {code} 相關新聞:\n"
            for idx, (title, link) in enumerate(news_list, 1):
                news_report += f"  {idx}. {title}\n     連結: {link}\n"
            news_report += "\n"
        else:
            news_report += f"📌 {code} 今日無相關新聞\n\n"
        time.sleep(1)  # 加入延遲避免被擋
    return news_report

# ===== Gmail 寄信 =====
def send_email(report):
    sender = os.getenv("GMAIL_SENDER")
    password = os.getenv("GMAIL_APP_PASSWORD")
    receiver = os.getenv("GMAIL_RECEIVER")

    print(f"DEBUG: 寄件者信箱: {sender}")
    print(f"DEBUG: 收件者信箱: {receiver}")
    print(f"DEBUG: 密碼長度: {len(password) if password else '未設定'}")

    if not all([sender, password, receiver]):
        print("❌ Gmail 參數未設定，取消發送")
        return

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = "台股每日AI分析結果（含大盤+個股新聞）"
    msg.attach(MIMEText(report, "plain", "utf-8"))

    try:
        print("DEBUG: 正在連接 Gmail SMTP 伺服器")
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        print("DEBUG: 正在登入")
        server.login(sender, password)
        print("DEBUG: 正在發送郵件")
        server.sendmail(sender, receiver, msg.as_string())
        server.quit()
        print("✅ Gmail 郵件發送成功")
    except Exception as e:
        print(f"❌ 郵件發送失敗: {e}")

# ===== 主程式 =====
if __name__ == "__main__":
    print("===== 台股分析啟動 =====")
    stock_list = os.getenv("STOCK_LIST", "2330,2317,2454").split(",")
    analysis_report = get_tw_analysis(stock_list)
    market_news = get_market_news()
    stock_news = get_stock_news(stock_list)
    full_report = analysis_report + market_news + stock_news
    print(full_report)
    send_email(full_report)
    print("===== 程式結束 =====")
