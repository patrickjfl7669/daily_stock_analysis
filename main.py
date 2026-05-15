from src.config import settings
from src.analyzer import tw_stock_analysis
from src.notification import send_gmail_report

def main():
    print("===== 台股AI自動分析啟動 =====")
    stock_codes = settings.stock_list
    full_report = tw_stock_analysis(stock_codes)
    print(full_report)
    # 執行自動寄送Gmail
    send_gmail_report(full_report)
    print("===== 分析完成、郵件發送完畢 =====")

if __name__ == "__main__":
    main()
