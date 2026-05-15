import os
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

# ===== 靜態新聞模板（避免網路抓取）=====
def get_news_template():
    news_report = "\n\n【今日台股新聞快訊】\n"
    news_report += "============================\n"
    news_report += "1. 台股整體盤勢穩健，電子權值股支撐大盤\n"
    news_report += "2. 半導體產業鏈受惠 AI 需求，相關個股表現強勁\n"
    news_report += "3. 外資連續買超，市場資金動能充足\n\n"
    news_report += "💡 若需最新即時新聞，建議直接查看鉅亨網或證交所官網\n"
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
    msg["Subject"] = "台股每日AI分析結果"
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
    news_report = get_news_template()
    full_report = analysis_report + news_report
    print(full_report)
    send_email(full_report)
    print("===== 程式結束 =====")
