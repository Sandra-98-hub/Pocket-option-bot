
import asyncio
import os

from BinaryOptionsToolsV2.pocketoption import PocketOptionAsync

SSID = os.environ.get("PO_SSID")

if not SSID:
    print("ERROR: PO_SESSION is not set")
    raise SystemExit(1)


async def main():
    print("Pocket Option OTC Signal Bot")
    print("============================")
    print("Market: EURUSD OTC")
    print("Timeframe: M1")
    print("Connecting to Pocket Option...")

    client = PocketOptionAsync(ssid=SSID)

    print("Connected!")
    print("Waiting for real OTC candles...")

    async for candle in client.subscribe_symbol("EURUSD_otc"):
        print("REAL OTC CANDLE:")
        print(f"Time:   {candle.get('time')}")
        print(f"Open:   {candle.get('open')}")
        print(f"High:   {candle.get('high')}")
        print(f"Low:    {candle.get('low')}")
        print(f"Close:  {candle.get('close')}")
        print("----------------------------")


if __name__ == "__main__":
    asyncio.run(main())
