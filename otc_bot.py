import os
import asyncio

from BinaryOptionsToolsV2.pocketoption import PocketOptionAsync


SSID = os.environ.get("POCKET_OPTION_SSID")

SYMBOL = "EURUSD_otc"


async def main():

    print("================================")
    print("POCKET OPTION OTC TEST")
    print("================================")

    if not SSID:
        print("ERROR: POCKET_OPTION_SSID is missing")
        return

    print("SSID: FOUND")
    print("Market:", SYMBOL)
    print("Timeframe: M1")
    print("Connecting to Pocket Option...")

    try:

        client = PocketOptionAsync(
            ssid=SSID
        )

        print("Connected.")
        print("Waiting for OTC candles...")

        async for candle in client.subscribe_symbol(
            SYMBOL
        ):

            print("--------------------------------")

            print(
                "Candle time:",
                candle.get("time")
            )

            print(
                "Open:",
                candle.get("open")
            )

            print(
                "High:",
                candle.get("high")
            )

            print(
                "Low:",
                candle.get("low")
            )

            print(
                "Close:",
                candle.get("close")
            )

            print("REAL-TIME OTC DATA RECEIVED")

    except Exception as error:

        print(
            "OTC connection error:",
            str(error)
        )


if __name__ == "__main__":

    asyncio.run(main())
