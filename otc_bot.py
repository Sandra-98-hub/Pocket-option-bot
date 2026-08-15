import asyncio
import os
from BinaryOptionsToolsV2.pocketoption import PocketOptionAsync

SSID = os.environ.get("PO_SSID", "").strip()

if not SSID:
    print("ERROR: PO_SSID is not set")
    raise SystemExit(1)

async def main():
    print("Pocket Option OTC Signal Bot")
    print("Market: EURUSD_otc")
    print("Timeframe: M1")
    print("Connecting...")

    client = PocketOptionAsync(ssid=SSID)

    print("Connected!")
    print("Waiting for real OTC candles...")

    async for candle in client.subscribe_symbol("EURUSD_otc"):
        print("OTC CANDLE:", candle)

if __name__ == "__main__":
    asyncio.run(main())
