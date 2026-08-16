
import os
import asyncio

from BinaryOptionsToolsV2.pocketoption import PocketOptionAsync


# ==========================================
# POCKET OPTION OTC MARKETS
# ==========================================

OTC_MARKETS = [
    "AUDCAD_otc",
    "AEDCNY_otc",
    "AUDNZD_otc",
]


async def test_market(client, market):

    print("------------------------------------------")
    print(f"Testing: {market}")
    print("Timeframe: M1")

    try:

        candles = await client.get_candles(
            market,
            60,
            0
        )

        if candles:

            print(f"✅ {market} OTC DATA RECEIVED")
            print(f"Candles received: {len(candles)}")

            latest = candles[-1]

            print("Latest candle:")
            print(latest)

            return True

        else:

            print(f"❌ {market}: No candles received")
            return False

    except Exception as error:

        print(f"❌ {market}: ERROR")
        print(type(error).__name__)
        print(str(error))

        return False


async def main():

    print("")
    print("==========================================")
    print("POCKET OPTION OTC DATA TEST")
    print("==========================================")
    print("")

    ssid = os.getenv("POCKET_OPTION_SSID")

    if not ssid:

        print("❌ ERROR")
        print("POCKET_OPTION_SSID is missing")

        return

    print("SSID: FOUND")
    print("Markets to test:")

    for market in OTC_MARKETS:
        print(f"  - {market}")

    print("")
    print("Connecting to Pocket Option...")
    print("")

    try:

        client = PocketOptionAsync(
            ssid=ssid
        )

        print("Connection initialized.")
        print("")

        working_markets = []

        for market in OTC_MARKETS:

            result = await test_market(
                client,
                market
            )

            if result:
                working_markets.append(market)

            # Small pause between requests
            await asyncio.sleep(1)

        print("")
        print("==========================================")
        print("TEST COMPLETE")
        print("==========================================")

        if working_markets:

            print("")
            print("OTC MARKETS WITH DATA:")

            for market in working_markets:
                print(f"✅ {market}")

            print("")
            print(
                "Next step: connect these candles "
                "to the EMA/RSI signal engine."
            )

        else:

            print("")
            print("❌ NO OTC MARKET DATA RECEIVED")
            print("")
            print(
                "The Pocket Option connection "
                "needs to be fixed before signals "
                "are generated."
            )

    except Exception as error:

        print("")
        print("==========================================")
        print("OTC CONNECTION ERROR")
        print("==========================================")

        print(type(error).__name__)
        print(str(error))


if __name__ == "__main__":

    asyncio.run(main())
