import os

class Settings:
    # 強制鎖定台股市場
    market_type: str = "TW"
    # 自選台股清單
    stock_list: list = os.getenv("STOCK_LIST", "2330,2317,2454").split(",")
    
    # AI金鑰
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    
    # Gmail發信完整參數
    gmail_sender: str = os.getenv("GMAIL_SENDER", "")
    gmail_app_pwd: str = os.getenv("GMAIL_APP_PASSWORD", "")
    gmail_receiver: str = os.getenv("GMAIL_RECEIVER", "")

settings = Settings()
