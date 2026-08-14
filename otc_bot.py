import os
import asyncio
from pocketoptionapi.stable_api import PocketOption

SSID = os.environ.get("POCKET_OPTION_SSID")

if not SSID:
    print("ERROR: POCKET_OPTION_SSID is not set")
    raise SystemExit(1)

api = PocketOption(SSID)

async def main():
    print("Pocket Option OTC Signal Bot")
    print("Connecting...")

    await api.connect()

    print("Connected!")
    print("Market: EURUSD OTC")
    print("Timeframe: M1")
    print("Waiting for OTC candles...")

    while True:
        try:
            candles = await api.get_candles("EURUSD_otc", 60, 20)

            if candles:
                print("Received OTC candle data!")
                print(candles[-1])

            await asyncio.sleep(60)

        except Exception as e:
            print("Error:", e)
            await asyncio.sleep(10)

asyncio.run(main())
