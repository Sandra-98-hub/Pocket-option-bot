import asyncio
import os
import requests

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
    requests.post(
        url,
        data={"chat_id": CHAT_ID, "text": message},
        timeout=10
    )


async def main():
    print("Pocket Option Telegram Signal Bot")
    print("Market: EURUSD OTC")
    print("Timeframe: M1")
    print("Connecting...")

    client = PocketOptionAsync(ssid=SSID)

    send_telegram("🤖 Pocket Option OTC bot is online.")

    print("Connected!")
    print("Waiting for OTC candles...")

    async for candle in client.subscribe_symbol("EURUSD_otc"):
        print("OTC candle received:", candle)

        # Temporary connection test.
        # Signal logic will be added after the candle feed is confirmed.
        send_telegram("📊 EUR/USD OTC candle received.")

if __name__ == "__main__":
    asyncio.run(main())
