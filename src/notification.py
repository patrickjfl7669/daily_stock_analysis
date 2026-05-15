import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.config import settings

def send_gmail_report(report_text:str):
    s_addr = settings.gmail_sender
    s_pwd = settings.gmail_app_pwd
    r_addr = settings.gmail_receiver

    if not all([s_addr,s_pwd,r_addr]):
        print("Gmail參數未填寫，取消發送")
        return

    msg = MIMEMultipart()
    msg["From"] = s_addr
    msg["To"] = r_addr
    msg["Subject"] = "台股每日AI分析結果"

    mail_body = MIMEText(report_text,"plain","utf-8")
    msg.attach(mail_body)

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com",465)
        server.login(s_addr,s_pwd)
        server.sendmail(s_addr,r_addr,msg.as_string())
        server.quit()
        print("✅ Gmail郵件發送成功")
    except Exception as e:
        print(f"❌ 郵件發送失敗：{str(e)}")
