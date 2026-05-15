import os
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ===== 台股分析 =====
def get_tw_analysis(codes):
    report = "【台股每日AI分析報告】\n"
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

# ===== Gmail 寄信 =====
def send_email(report):
    sender = os.getenv("GMAIL_SENDER")
    password = os.getenv("GMAIL_APP_PASSWORD")
    receiver = os.getenv("GMAIL_RECEIVER")

    if not all([sender, password, receiver]):
        print("❌ Gmail 參數未設定")
        return

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = "台股每日AI分析結果"
    msg.attach(MIMEText(report, "plain", "utf-8"))

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender, password)
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
    print(analysis_report)
    send_email(analysis_report)
    print("===== 程式結束 =====")
