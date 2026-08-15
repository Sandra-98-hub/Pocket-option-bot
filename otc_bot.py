
import asyncio
import os
import requests
import pandas as pd

from BinaryOptionsToolsV2.pocketoption import PocketOptionAsync

SSID = os.environ.get("PO_SSID", "").strip()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

if not SSID:
    raise SystemExit("ERROR: PO_SSID is not set")

if not TELEGRAM_TOKEN:
    raise SystemExit("ERROR: TELEGRAM_BOT_TOKEN is not set")

if not CHAT_ID:
    raise SystemExit("ERROR: TELEGRAM_CHAT_ID is not set")


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:
        response = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": message
            },
            timeout=10
        )

        print("Telegram status:", response.status_code)
        print("Telegram response:", response.text)

    except Exception as e:
        print("Telegram error:", e)


def calculate_signal(closes):
    if len(closes) < 20:
        return "WAIT"

    series = pd.Series(closes)

    ema9 = series.ewm(span=9, adjust=False).mean().iloc[-1]
    ema20 = series.ewm(span=20, adjust=False).mean().iloc[-1]

    delta = series.diff()

    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    avg_gain = gains.rolling(14).mean().iloc[-1]
    avg_loss = losses.rolling(14).mean().iloc[-1]

    if avg_loss == 0:
        rsi = 100
    else:
        rsi = 100 - (100 / (1 + avg_gain / avg_loss))

    price = series.iloc[-1]

    if ema9 > ema20 and rsi >= 55 and price > ema9:
        return "BUY"

    if ema9 < ema20 and rsi <= 45 and price < ema9:
        return "SELL"

    return "WAIT"


async def main():

    print("================================")
    print("POCKET OPTION TELEGRAM BOT")
    print("EURUSD OTC - M1")
    print("================================")

    client = PocketOptionAsync(ssid=SSID)

    print("Connected to Pocket Option")

    send_telegram(
        "🤖 POCKET OPTION BOT ONLINE\n\n"
        "EUR/USD OTC\n"
        "M1\n"
        "EMA 9/20 + RSI 14\n\n"
        "Waiting for signal..."
    )

    closes = []

    async for candle in client.subscribe_symbol("EURUSD_otc"):

        try:

            if isinstance(candle, dict):
                close = candle.get("close")
            else:
                close = candle.close

            close = float(close)

            closes.append(close)

            if len(closes) > 100:
                closes.pop(0)

            signal = calculate_signal(closes)

            print(
                "Candle:",
                close,
                "| Candles:",
                len(closes),
                "| Signal:",
                signal
            )

            if signal == "BUY":

                message = (
                    "🟢 POCKET OPTION SIGNAL\n\n"
                    "EUR/USD OTC\n"
                    "TIMEFRAME: M1\n\n"
                    "➡️ BUY\n\n"
                    "EMA 9 > EMA 20\n"
                    "RSI ≥ 55\n\n"
                    "⚠️ Signal only — no automatic trade."
                )

                send_telegram(message)

            elif signal == "SELL":

                message = (
                    "🔴 POCKET OPTION SIGNAL\n\n"
                    "EUR/USD OTC\n"
                    "TIMEFRAME: M1\n\n"
                    "➡️ SELL\n\n"
                    "EMA 9 < EMA 20\n"
                    "RSI ≤ 45\n\n"
                    "⚠️ Signal only — no automatic trade."
                )

                send_telegram(message)

        except Exception as e:
            print("Candle processing error:", e)


if __name__ == "__main__":
    asyncio.run(main())
