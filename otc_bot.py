import os
import asyncio

from pocket_option import PocketOptionClient
from pocket_option import AuthorizationData
from pocket_option import IsDemo

PO_URL = "wss://api.pocketoption.com/socket.io/"

session = os.getenv("PO_SESSION")

if not session:
    print("ERROR: PO_SESSION is missing")
    raise SystemExit(1)

print("PO_SESSION found")

async def main():

    print("Creating authorization...")

    auth = AuthorizationData(
        session=session,
        isDemo=IsDemo.DEMO,
        uid=0,
        platform=1,
        isFastHistory=True,
        isOptimized=True
    )

    print("Authorization created")
    print("Connecting to Pocket Option...")

    client = PocketOptionClient()

    try:
        await client.connect(
            PO_URL,
            auth=auth,
            wait=True,
            wait_timeout=10,
            retry=True
        )

        print("CONNECTED:", client.is_authorized())

        if client.is_authorized():
            print("POCKET OPTION LIVE CONNECTION SUCCESSFUL")
        else:
            print("CONNECTED BUT NOT AUTHORIZED")

        await client.wait()

    except Exception as e:
        print("CONNECTION ERROR:")
        print(type(e).__name__, str(e))

if __name__ == "__main__":
    asyncio.run(main())
