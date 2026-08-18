import os
import asyncio
import urllib.request
import urllib.parse

from BinaryOptionsToolsV2.pocketoption import PocketOptionAsync


MARKETS = [
    "AUDCAD_otc",
    "AEDCNY_otc",
    "AUDNZD_otc",
]

SSID = os.getenv("POCKET_OPTION_SSID")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def telegram(message):

    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing")
        return

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}/sendMessage"
    )

    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }).encode()

    try:
        request = urllib.request.Request(
            url,
            data=data,
            method="POST"
        )

        with urllib.request.urlopen(
            request,
            timeout=15
        ) as response:

            print(
                "Telegram status:",
                response.status
            )

    except Exception as error:

        print("Telegram error:", error)


async def main():

    print("====================================")
    print("POCKET OPTION OTC BOT")
    print("====================================")

    if not SSID:
        print("ERROR: POCKET_OPTION_SSID missing")
        return

    print("SSID: FOUND")
    print("Connecting to Pocket Option...")

    try:

        async with PocketOptionAsync(SSID) as api:

            print("CONNECTED TO POCKET OPTION")
            print("")

            telegram(
                "✅ Pocket Option OTC bot connected.\n"
                "Testing OTC markets:\n\n"
                "AUD/CAD OTC\n"
                "AED/CNY OTC\n"
                "AUD/NZD OTC"
            )

            for market in MARKETS:

                print("--------------------------------")
                print("Testing:", market)

                try:

                    candles = await api.get_candles(
                        market,
                        60,
                        30
                    )

                    if candles:

                        print(
                            "✅ OTC candles received:",
                            market
                        )

                        print(
                            "Latest candle:",
                            candles[-1]
                        )

                        telegram(
                            f"✅ OTC DATA RECEIVED\n\n"
                            f"Market: {market}\n"
                            f"Timeframe: M1\n"
                            f"Source: Pocket Option OTC"
                        )

                    else:

                        print(
                            "❌ No candles:",
                            market
                        )

                except Exception as error:

                    print(
                        "❌ Market error:",
                        market
                    )

                    print(
                        type(error).__name__,
                        str(error)
                    )

            print("")
            print("OTC TEST COMPLETE")

            while True:
                await asyncio.sleep(60)

    except Exception as error:

        print("")
        print("====================================")
        print("POCKET OPTION CONNECTION ERROR")
        print("====================================")
        print(type(error).__name__)
        print(str(error))


if __name__ == "__main__":
    asyncio.run(main())
