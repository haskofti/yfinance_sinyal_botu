import pandas as pd
import yfinance as yf
from datetime import datetime
import smtplib
from email.message import EmailMessage

# Ayarlar
INTERVALS = ["15m", "30m", "60m", "1d"]
SYMBOL = "GC=F"  # Gold Futures (XAUUSD’ye çok yakın)
EMAIL_GONDER = True
EMAIL_ADRESI = "hafi26@gmail.com"

def get_data(interval):
    try:
        df = yf.download(SYMBOL, period="7d", interval=interval)
        df.dropna(inplace=True)
        print(f"[{interval}] Veri başarıyla alındı. İlk: {df.index[0]}, Son: {df.index[-1]}")
        return df
    except Exception as e:
        print(f"[{interval}] Veri alınamadı:", e)
        return None

def get_current_price():
    try:
        ticker = yf.Ticker(SYMBOL)
        return float(ticker.info["regularMarketPrice"])
    except Exception as e:
        print("❌ Güncel fiyat alınamadı:", e)
        return None

def calculate_indicators(df):
    df["ma20"] = df["Close"].rolling(20).mean()
    df["ma50"] = df["Close"].rolling(50).mean()
    df["ema20"] = df["Close"].ewm(span=20).mean()
    df["ema50"] = df["Close"].ewm(span=50).mean()
    df["rsi"] = 100 - (100 / (1 + df["Close"].pct_change().rolling(14).mean()))
    df["macd"] = df["Close"].ewm(12).mean() - df["Close"].ewm(26).mean()
    df["signal"] = df["macd"].ewm(9).mean()
    df["boll_mid"] = df["Close"].rolling(20).mean()
    df["boll_std"] = df["Close"].rolling(20).std()
    df["upper"] = df["boll_mid"] + 2 * df["boll_std"]
    df["lower"] = df["boll_mid"] - 2 * df["boll_std"]
    return df

def generate_signal(df, interval):
    latest = df.iloc[-1]
    entry = latest["Close"]
    current_price = get_current_price()
    if current_price is None:
        return f"[{interval}] ❌ Güncel fiyat yok"

    fark = abs(current_price - entry)
    if fark > 3:
        return f"[{interval}] ⛔ Sinyal Geçersiz (Fiyat Uzak)\nEntry: {entry:.2f}\nGüncel: {current_price:.2f}"

    sinyal_say = 0
    if latest["ma20"] > latest["ma50"]: sinyal_say += 1
    if latest["ema20"] > latest["ema50"]: sinyal_say += 1
    if latest["rsi"] < 30: sinyal_say += 1
    if latest["macd"] > latest["signal"]: sinyal_say += 1
    if latest["Close"] > latest["upper"]: sinyal_say += 1

    if sinyal_say >= 3:
        tp = entry + entry * 0.01
        sl = entry - (tp - entry) / 4
        return f"[{interval}] AL\nGiriş: {entry:.2f}\nTP: {tp:.2f}\nSL: {sl:.2f}"
    else:
        return f"[{interval}] Sinyal Yok"

def send_email(content):
    if not EMAIL_GONDER:
        return
    msg = EmailMessage()
    msg.set_content(content)
    msg["Subject"] = "XAUUSD Sinyal Raporu"
    msg["From"] = EMAIL_ADRESI
    msg["To"] = EMAIL_ADRESI

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(EMAIL_ADRESI, "jxdb eksm rumw huqb")  # Google App password
            s.send_message(msg)
        print("✅ Mail gönderildi.")
    except Exception as e:
        print("❌ Mail gönderilemedi:", e)

if __name__ == "__main__":
    rapor = f"Sinyal Raporu ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n"
    for interval in INTERVALS:
        df = get_data(interval)
        if df is not None:
            df = calculate_indicators(df)
            rapor += generate_signal(df, interval) + "\n"
    print(rapor)
    send_email(rapor)
