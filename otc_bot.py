import os
import asyncio

from BinaryOptionsToolsV2.pocketoption import PocketOptionAsync


async def main():

    ssid = os.environ.get("POCKET_OPTION_SSID")

    print("================================")
    print("POCKET OPTION OTC CONNECTION")
    print("================================")

    if not ssid:
        print("ERROR: POCKET_OPTION_SSID is missing")
        return

    print("SSID found.")
    print("Connecting...")

    try:

        client = PocketOptionAsync(
            ssid=ssid
        )

        print("Connected successfully.")

        print("Getting EURUSD OTC candles...")

        candles = await client.get_candles(
            "EURUSD_otc",
            60,
            0
        )

        print("Candles received:", len(candles))

        if candles:

            print("Latest OTC candle:")
            print(candles[-1])

        print("================================")
        print("POCKET OPTION OTC DATA WORKING")
        print("================================")

    except Exception as e:

        print("OTC CONNECTION ERROR:")
        print(type(e).__name__)
        print(str(e))


if __name__ == "__main__":
    asyncio.run(main())
