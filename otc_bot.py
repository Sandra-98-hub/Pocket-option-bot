import os
import asyncio
import logging

from pocket_option import PocketOptionClient
from pocket_option.constants import Regions
from pocket_option.models import Asset


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

MARKETS = [
    Asset.AUDCAD_otc,
    Asset.AEDCNY_otc,
    Asset.AUDNZD_otc,
]


async def main():

    print("======================================")
    print("POCKET OPTION OTC CONNECTION TEST")
    print("======================================")

    session = os.getenv("POCKET_OPTION_SESSION")
    uid = os.getenv("POCKET_OPTION_UID")

    if not session:
        print("❌ POCKET_OPTION_SESSION is missing")
        return

    if not uid:
        print("❌ POCKET_OPTION_UID is missing")
        return

    print("Session: FOUND")
    print("UID: FOUND")
    print("Connecting to Pocket Option...")

    client = PocketOptionClient(logger=True)

    try:

        await client.connect(
            Regions.DEMO
        )

        print("✅ Connected to Pocket Option")

        print("")
        print("Testing OTC markets:")

        for market in MARKETS:

            print("")
            print(f"Testing {market}...")

            try:

                await client.emit.subscribe_to_asset(
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
        print("======================================")
        print("OTC CONNECTION TEST RUNNING")
        print("======================================")

        while True:
            await asyncio.sleep(10)

    except Exception as error:

        print("")
        print("❌ POCKET OPTION ERROR")
        print(type(error).__name__)
        print(str(error))


if __name__ == "__main__":
    asyncio.run(main())
