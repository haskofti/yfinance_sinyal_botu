import pandas as pd
import yfinance as yf
from datetime import datetime
import smtplib
from email.message import EmailMessage

INTERVALS = ["15m", "30m", "60m", "4h", "1d"]
SYMBOL = "GC=F"  # Altın (Gold Futures)
EMAIL_GONDER = True
EMAIL_ADRESI = "hafi26@gmail.com"

def get_data(interval):
    try:
        df = yf.download(SYMBOL, period="7d", interval=interval)
        df = df.dropna()
        print(f"[{interval}] Veri başarıyla alındı. İlk: {df.index[0]}, Son: {df.index[-1]}")
        return df
    except Exception as e:
        print(f"[{interval}] Veri alınamadı:", e)
        return None

def get_current_price():
    try:
        ticker = yf.Ticker(SYMBOL)
        price = ticker.info.get("regularMarketPrice", None)
        return float(price) if price is not None else None
    except Exception as e:
        print("❌ Güncel fiyat alınamadı:", e)
        return None

def calculate_indicators(df):
    df["ma20"] = df["Close"].rolling(window=20).mean()
    df["ma50"] = df["Close"].rolling(window=50).mean()
    df["ma100"] = df["Close"].rolling(window=100).mean()
    df["ema20"] = df["Close"].ewm(span=20).mean()
    df["ema50"] = df["Close"].ewm(span=50).mean()
    df["ema100"] = df["Close"].ewm(span=100).mean()
    df["rsi14"] = 100 - (100 / (1 + df["Close"].pct_change().rolling(window=14).mean()))
    df["momentum"] = df["Close"] - df["Close"].shift(10)
    df["macd"] = df["Close"].ewm(span=12).mean() - df["Close"].ewm(span=26).mean()
    df["signal"] = df["macd"].ewm(span=9).mean()
    df["bollinger_mid"] = df["Close"].rolling(20).mean()
    df["bollinger_std"] = df["Close"].rolling(20).std()
    df["upper_band"] = df["bollinger_mid"] + 2 * df["bollinger_std"]
    df["lower_band"] = df["bollinger_mid"] - 2 * df["bollinger_std"]
    df["adx"] = abs(df["Close"].diff()).rolling(14).mean()
    df["roc"] = df["Close"].pct_change(periods=10)
    df["willr"] = (df["Close"] - df["Low"].rolling(14).min()) / (df["High"].rolling(14).max() - df["Low"].rolling(14).min())
    return df

def generate_signal(df, interval):
    latest = df.iloc[-1]
    sinyal_sayisi = 0

    if latest["ma20"] > latest["ma50"]: sinyal_sayisi += 1
    if latest["ema20"] > latest["ema50"]: sinyal_sayisi += 1
    if latest["ma50"] > latest["ma100"]: sinyal_sayisi += 1
    if latest["ema50"] > latest["ema100"]: sinyal_sayisi += 1
    if latest["rsi14"] < 30: sinyal_sayisi += 1
    if latest["momentum"] > 0: sinyal_sayisi += 1
    if latest["macd"] > latest["signal"]: sinyal_sayisi += 1
    if latest["Close"] > latest["upper_band"]: sinyal_sayisi += 1
    if latest["adx"] > 20: sinyal_sayisi += 1
    if latest["roc"] > 0: sinyal_sayisi += 1
    if latest["willr"] > -0.8: sinyal_sayisi += 1

    if sinyal_sayisi >= 6:
        entry = float(latest["Close"])
        tp = entry + (entry * 0.01)
        sl = entry - ((tp - entry) / 4)

        current_price = get_current_price()
        if current_price is not None:
            try:
                fark = abs(float(current_price) - float(entry))
                print(f"[{interval}] Entry: {entry:.2f} | Güncel: {current_price:.2f} | Fark: {fark:.2f}")
                if fark > 3:
                    return f"[{interval}] ⛔ Sinyal Geçersiz (Fiyat Uzak)\nEntry: {entry:.2f}\nGüncel: {current_price:.2f}"
            except Exception as e:
                print(f"[{interval}] Fiyat karşılaştırma hatası:", e)
                return f"[{interval}] ⛔ Sinyal Geçersiz (Fiyat okunamadı)"

        return f"[{interval}] AL\nGiriş: {entry:.2f}\nTP: {tp:.2f}\nSL: {sl:.2f}"
    return f"[{interval}] Sinyal Yok"

def send_email(content):
    if not EMAIL_GONDER:
        return

    sender = "hafi26@gmail.com"
    password = "jxdb eksm rumw huqb"
    receiver = "hafi26@gmail.com"

    try:
        msg = EmailMessage()
        msg.set_content(content)
        msg["Subject"] = "XAUUSD Çoklu Zaman Sinyal"
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
        df = get_data(interval)
        if df is not None:
            df = calculate_indicators(df)
            rapor += generate_signal(df, interval) + "\n"
    print(rapor)
    send_email(rapor)
