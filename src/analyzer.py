import yfinance as yf
from src.config import settings

def get_tw_data(code: str):
    try:
        tick = yf.Ticker(f"{code}.TW")
        df = tick.history(period="60d")
        if df.empty:
            tick = yf.Ticker(f"{code}.TWO")
            df = tick.history(period="60d")
        return df
    except:
        return None

def calc_tech_index(df):
    df["ma5"] = df["Close"].rolling(5).mean()
    df["ma10"] = df["Close"].rolling(10).mean()
    now_price = df["Close"].iloc[-1]
    ma5_price = df["ma5"].iloc[-1]
    bias = round(((now_price - ma5_price)/ma5_price)*100,2)
    return now_price,ma5_price,bias

def tw_stock_analysis(code_list:list) -> str:
    content = "【台股每日AI分析報告】\n"
    content += "====================================\n"
    for code in code_list:
        df = get_tw_data(code)
        if df is None or len(df)<10:
            content += f"{code}：行情資料取得失敗\n"
            continue
        price,ma5,bias = calc_tech_index(df)
        if bias <= 2:
            suggest = "🟢 低檔回踩，適合布局"
        elif bias <=5:
            suggest = "🟡 區間整理，觀望為主"
        else:
            suggest = "🔴 乖離過高，避免追高"
        content += f"標的:{code} 現價:{price} MA5:{ma5} 乖離率:{bias}% 建議:{suggest}\n"
    return content
