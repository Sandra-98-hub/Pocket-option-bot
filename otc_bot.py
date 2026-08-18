import asyncio
import logging
import os

from pocket_option import PocketOptionClient
from pocket_option.constants import Regions
from pocket_option.models import AuthorizationData, SuccessAuthEvent


MARKETS = [
    "EURUSD_otc",
    "EURCHF_otc",
    "GBPUSD_otc",
    "USDJPY_otc",
    "AUDCAD_otc",
    "AUDNZD_otc",
    "AEDCNY_otc",
]

IS_DEMO = 1


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

client = PocketOptionClient(logger=True)


@client.on.connect
async def on_connect(data=None):

    print("")
    print("================================")
    print("POCKET OPTION CONNECTED")
    print("================================")

    session = os.getenv("PO_SESSION")
    uid = os.getenv("PO_UID")

    if not session:
        print("ERROR: PO_SESSION missing")
        return

    if not uid:
        print("ERROR: PO_UID missing")
        return

    print("PO_SESSION: FOUND")
    print("PO_UID: FOUND")

    try:

        auth_data = AuthorizationData.model_validate(
            {
                "session": session,
                "isDemo": IS_DEMO,
                "uid": int(uid),
                "platform": 2,
                "isFastHistory": True,
                "isOptimized": True,
            }
        )

        await client.emit.auth(auth_data)

        print("AUTH REQUEST SENT")

    except Exception as error:

        print("AUTH ERROR")
        print(type(error).__name__)
        print(str(error))


@client.on.success_auth
async def on_success_auth(data: SuccessAuthEvent):

    print("")
    print("================================")
    print("AUTHENTICATED")
    print("================================")

    print("")

    for market in MARKETS:

        print("Testing:", market)

        try:

            await client.emit.subscribe_to_asset(
                market
            )

            print(
                "Subscription requested:",
                market
            )

        except Exception as error:

            print(
                "Subscription error:",
                market
            )

            print(
                type(error).__name__,
                str(error)
            )

    print("")
    print("OTC CONNECTION TEST RUNNING")


async def main():

    print("")
    print("================================")
    print("POCKET OPTION OTC TEST")
    print("================================")
    print("")

    if not os.getenv("PO_SESSION"):
        print("ERROR: PO_SESSION missing")
        return

    if not os.getenv("PO_UID"):
        print("ERROR: PO_UID missing")
        return

    print("PO_SESSION found")
    print("PO_UID found")
    print("")
    print("Connecting...")

    try:

        await client.connect(
            Regions.DEMO
        )

        while True:

            await asyncio.sleep(10)

    except Exception as error:

        print("")
        print("================================")
        print("CONNECTION ERROR")
        print("================================")

        print(
            type(error).__name__
        )

        print(
            str(error)
        )


if __name__ == "__main__":
    asyncio.run(main())
