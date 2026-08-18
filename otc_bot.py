import os
import asyncio
from pocket_option import PocketOptionClient


SESSION = os.getenv("PO_SESSION")
UID = os.getenv("PO_UID")

MARKETS = [
    "AUDCAD_otc",
    "AEDCNY_otc",
    "AUDNZD_otc",
]


async def main():

    print("===================================")
    print("POCKET OPTION OTC CONNECTION TEST")
    print("===================================")

    if not SESSION:
        print("❌ PO_SESSION is missing")
        return

    if not UID:
        print("❌ PO_UID is missing")
        return

    print("PO_SESSION: FOUND")
    print("PO_UID: FOUND")
    print("Connecting...")

    try:

        client = PocketOptionClient(
            session=SESSION,
            uid=UID
        )

        await client.connect()

        print("✅ CONNECTED TO POCKET OPTION")
        print("")

        for market in MARKETS:

            print(
                f"Testing OTC market: {market}"
            )

            try:

                await client.subscribe(
                    market
                )

                print(
                    f"✅ Subscription requested: {market}"
                )

            except Exception as error:

                print(
                    f"❌ {market}: {error}"
                )

        print("")
        print("OTC connection test running.")

        while True:
            await asyncio.sleep(60)

    except Exception as error:

        print("")
        print("❌ CONNECTION ERROR")
        print(type(error).__name__)
        print(str(error))


if __name__ == "__main__":
    asyncio.run(main())
