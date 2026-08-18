import asyncio
import os

from pocket_option import PocketOptionClient
from pocket_option.constants import Regions
from pocket_option.models import AuthorizationData


MARKETS = [
    "EURUSD_otc",
    "EURCHF_otc",
    "GBPUSD_otc",
    "USDJPY_otc",
    "AUDCAD_otc",
    "AUDNZD_otc",
    "AEDCNY_otc",
]

client = PocketOptionClient(logger=True)


@client.on.connect
async def connected(data=None):
    print("CONNECTED")

    session = os.getenv("PO_SESSION")
    uid = os.getenv("PO_UID")

    if not session or not uid:
        print("PO_SESSION or PO_UID missing")
        return

    try:
        auth = AuthorizationData.model_validate({
            "session": session,
            "isDemo": 1,
            "uid": int(uid),
            "platform": 2,
            "isFastHistory": True,
            "isOptimized": True,
        })

        await client.emit.auth(auth)

        print("AUTH REQUEST SENT")

    except Exception as e:
        print("AUTH ERROR:", type(e).__name__, str(e))


@client.on.success_auth
async def authenticated(data):

    print("================================")
    print("POCKET OPTION AUTHENTICATED")
    print("================================")

    for market in MARKETS:

        try:
            await client.emit.subscribe_to_asset(market)
            print("SUBSCRIBED:", market)

        except Exception as e:
            print(
                "SUBSCRIBE ERROR:",
                market,
                type(e).__name__,
                str(e)
            )


async def main():

    print("================================")
    print("POCKET OPTION OTC TEST")
    print("================================")

    if not os.getenv("PO_SESSION"):
        print("PO_SESSION MISSING")
        return

    if not os.getenv("PO_UID"):
        print("PO_UID MISSING")
        return

    print("PO_SESSION FOUND")
    print("PO_UID FOUND")
    print("CONNECTING...")

    try:

        await client.connect(Regions.DEMO)

        while True:
            await asyncio.sleep(10)

    except Exception as e:

        print(
            "CONNECTION ERROR:",
            type(e).__name__,
            str(e)
        )


if __name__ == "__main__":
    asyncio.run(main())
