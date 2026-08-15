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
    response = requests.post(
        url,
        data={"chat_id": CHAT_ID, "text": message},
        timeout=10
    )
    print("Telegram:", response.status_code)


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
    print("Pocket Option Telegram Signal Bot")
    print("Market: EURUSD OTC")
    print("Timeframe: M1")
    print("Connecting...")

    client = PocketOptionAsync(ssid=SSID)

    print("Connected!")

    send_telegram(
        "🤖 Pocket Option OTC Signal Bot is ONLINE\n"
        "EUR/USD OTC • M1\n"
        "EMA 9/20 + RSI 14\n"
        "Waiting for confirmation..."
    )

    closes = []
    last_signal = None

    async for candle in client.subscribe_symbol("EURUSD_otc"):

        try:
            close = float(candle["close"])
        except (KeyError, TypeError, ValueError):
            print("Could not read candle:", candle)
            continue

        closes.append(close)

        if len(closes) > 100:
            closes.pop(0)

        signal = calculate_signal(closes)

        print("Close:", close, "Signal:", signal)

        if signal in ("BUY", "SELL") and signal != last_signal:
            message = (
                f"🚨 POCKET OPTION SIGNAL\n\n"
                f"EUR/USD OTC\n"
                f"TIMEFRAME: M1\n\n"
                f"➡️ {signal}\n\n"
                f"EMA 9/20 + RSI 14 confirmation\n"
                f"Signal only — no automatic trade."
            )

            send_telegram(message)
            last_signal = signal


if __name__ == "__main__":
    asyncio.run(main())
