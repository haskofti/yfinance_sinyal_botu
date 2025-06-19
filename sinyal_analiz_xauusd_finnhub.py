import requests
import pandas as pd
from datetime import datetime
import smtplib
from email.message import EmailMessage
import time

API_KEY = "d1a0if9r01qltimuel50d1a0if9r01qltimuel5g"  # Finnhub API Key
SYMBOL = "OANDA:XAUUSD"
EMAIL_ADRESI = "hafi26@gmail.com"
EMAIL_GONDER = True

INTERVALS = ["15", "30", "60", "240", "D"]

def get_finnhub_data(resolution):
    url = f"https://finnhub.io/api/v1/stock/candle"
    params = {
        "symbol": SYMBOL,
        "resolution": resolution,
        "from": int(time.time()) - 7 * 24 * 60 * 60,  # son 7 gün
        "to": int(time.time()),
        "token": API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data.get("s") != "ok":
            print(f"[{resolution}] Veri alınamadı: API boş veri döndü")
            return None
        df = pd.DataFrame({
            "datetime": pd.to_datetime(data["t"], unit="s"),
            "Open": data["o"],
            "High": data["h"],
            "Low": data["l"],
            "Close": data["c"]
        })
        df.set_index("datetime", inplace=True)
        print(f"[{resolution}] İlk veri: {df.index[0]}, Son veri: {df.index[-1]}")
        return df
    else:
        print(f"[{resolution}] HTTP Hatası:", response.status_code)
        return None

def get_current_price():
    url = f"https://finnhub.io/api/v1/quote?symbol={SYMBOL}&token={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get("c", None)
    print("Fiyat verisi alınamadı")
    return None

def calculate_indicators(df):
    df["ma20"] = df["Close"].rolling(window=20).mean()
    df["ma50"] = df["Close"].rolling(window=50).mean()
    df["ema20"] = df["Close"].ewm(span=20).mean()
    df["ema50"] = df["Close"].ewm(span=50).mean()
    df["rsi14"] = 100 - (100 / (1 + df["Close"].pct_change().rolling(window=14).mean()))
    df["macd"] = df["Close"].ewm(span=12).mean() - df["Close"].ewm(span=26).mean()
    df["signal"] = df["macd"].ewm(span=9).mean()
    df["upper_band"] = df["Close"].rolling(20).mean() + 2 * df["Close"].rolling(20).std()
    df["lower_band"] = df["Close"].rolling(20).mean() - 2 * df["Close"].rolling(20).std()
    return df

def generate_signal(df, interval):
    latest = df.iloc[-1]
    sinyal_sayisi = 0

    if latest["ma20"] > latest["ma50"]: sinyal_sayisi += 1
    if latest["ema20"] > latest["ema50"]: sinyal_sayisi += 1
    if latest["rsi14"] < 30: sinyal_sayisi += 1
    if latest["macd"] > latest["signal"]: sinyal_sayisi += 1
    if latest["Close"] > latest["upper_band"]: sinyal_sayisi += 1

    if sinyal_sayisi >= 3:
        entry = latest["Close"]
        tp = entry + (entry * 0.01)
        sl = entry - ((tp - entry) / 4)

        current_price = get_current_price()
        if current_price is not None:
            fark = abs(current_price - entry)
            print(f"[{interval}] Entry: {entry:.2f} | Güncel: {current_price:.2f} | Fark: {fark:.2f}")
            if fark > 3:
                return f"[{interval}] ⛔ Sinyal Geçersiz (Fiyat Uzak)\nEntry: {entry:.2f}\nGüncel: {current_price:.2f}"

        return f"[{interval}] AL\nGiriş: {entry:.2f}\nTP: {tp:.2f}\nSL: {sl:.2f}"
    return f"[{interval}] Sinyal Yok"

def send_email(content):
    if not EMAIL_GONDER:
        return

    sender = "hafi26@gmail.com"
    password = "jxdb eksm rumw huqb"  # Uygulama şifresi
    receiver = "hafi26@gmail.com"

    try:
        msg = EmailMessage()
        msg.set_content(content)
        msg["Subject"] = "XAUUSD Sinyal Raporu"
        msg["From"] = sender
        msg["To"] = receiver

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)

        print("✅ Mail başarıyla gönderildi.")
    except Exception as e:
        print("❌ Mail gönderilemedi:", e)

if __name__ == "__main__":
    rapor = f"Sinyal Raporu ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n"
    for interval in INTERVALS:
        df = get_finnhub_data(interval)
        if df is not None:
            df = calculate_indicators(df)
            rapor += generate_signal(df, interval) + "\n"
    print(rapor)
    send_email(rapor)
    "api key değiştirildi"
