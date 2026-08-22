import os
import asyncio

from pocket_option import PocketOptionClient
from pocket_option.constants import Regions
from pocket_option.models import AuthorizationData


async def main():
    session = os.getenv("PO_SESSION")
    uid = os.getenv("PO_UID")

    if not session:
        print("ERROR: PO_SESSION is missing")
        return

    if not uid:
        print("ERROR: PO_UID is missing")
        return

    print("PO_SESSION found")
    print("PO_UID found")

    client = PocketOptionClient(logger=True)

    authorization = AuthorizationData.model_validate({
        "session": session,
        "isDemo": 1,
        "uid": int(uid),
        "platform": 2,
        "isFastHistory": True,
        "isOptimized": True,
    })

    @client.on.connect
    async def on_connect(data=None):
        print("CONNECTED TO POCKET OPTION")
        await client.emit.auth(authorization)

    @client.on.success_auth
    async def on_success_auth(data):
        print("POCKET OPTION AUTHORIZED")
        print("Authorization successful")

    print("Connecting...")

    await client.connect(Regions.DEMO)

    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
