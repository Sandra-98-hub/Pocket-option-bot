import asyncio
import os
import requests
import pandas as pd

from BinaryOptionsToolsV2.pocketoption import PocketOptionAsync

SSID = os.getenv("PO_SSID", "").strip()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()


def telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram credentials missing")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:
        r = requests.post(
            url,
            data={"chat_id": CHAT_ID, "text": message},
            timeout=10
        )

        print("Telegram status:", r.status_code)
        print("Telegram response:", r.text)

    except Exception as e:
        print("Telegram error:", e)


def signal_from_prices(prices):
    if len(prices) < 20:
        return "WAIT"

    s = pd.Series(prices)

    ema9 = s.ewm(span=9, adjust=False).mean().iloc[-1]
    ema20 = s.ewm(span=20, adjust=False).mean().iloc[-1]

    change = s.diff()

    gain = change.clip(lower=0).rolling(14).mean().iloc[-1]
    loss = (-change.clip(upper=0)).rolling(14).mean().iloc[-1]

    if loss == 0:
        rsi = 100
    else:
        rsi = 100 - (100 / (1 + gain / loss))

    price = s.iloc[-1]

    if ema9 > ema20 and rsi >= 55 and price > ema9:
        return "BUY"

    if ema9 < ema20 and rsi <= 45 and price < ema9:
        return "SELL"

    return "WAIT"


async def main():

    print("================================")
    print("POCKET OPTION SIGNAL BOT")
    print("EURUSD OTC M1")
    print("================================")

    if not SSID:
        print("ERROR: PO_SSID is missing")
        return

    if not TELEGRAM_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN is missing")
        return

    if not CHAT_ID:
        print("ERROR: TELEGRAM_CHAT_ID is missing")
        return

    print("Connecting to Pocket Option...")

    client = PocketOptionAsync(ssid=SSID)

    print("Connected!")
    print("Sending Telegram startup message...")

    telegram(
        "🤖 POCKET OPTION SIGNAL BOT ONLINE\n\n"
        "EUR/USD OTC\n"
        "M1\n"
        "EMA 9/20 + RSI 14\n\n"
        "Waiting for signal..."
    )

    prices = []

    async for candle in client.subscribe_symbol("EURUSD_otc"):

        try:
            if isinstance(candle, dict):
                close = candle.get("close")
            else:
                close = candle.close

            close = float(close)
            prices.append(close)

            if len(prices) > 100:
                prices.pop(0)

            signal = signal_from_prices(prices)

            print(
                "Close:",
                close,
                "| Candles:",
                len(prices),
                "| Signal:",
                signal
            )

            if signal == "BUY":

                telegram(
                    "🟢 POCKET OPTION SIGNAL\n\n"
                    "EUR/USD OTC\n"
                    "M1\n\n"
                    "➡️ BUY\n\n"
                    "EMA 9 > EMA 20\n"
                    "RSI ≥ 55\n\n"
                    "Signal only — no automatic trade."
                )

            elif signal == "SELL":

                telegram(
                    "🔴 POCKET OPTION SIGNAL\n\n"
                    "EUR/USD OTC\n"
                    "M1\n\n"
                    "➡️ SELL\n\n"
                    "EMA 9 < EMA 20\n"
                    "RSI ≤ 45\n\n"
                    "Signal only — no automatic trade."
                )

        except Exception as e:
            print("Candle error:", e)


if __name__ == "__main__":
    asyncio.run(main())
