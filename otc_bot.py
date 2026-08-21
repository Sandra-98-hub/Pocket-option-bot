import os
import asyncio
from pocket_option import PocketOptionClient

print("POCKET OPTION PACKAGE OK")

session = os.getenv("PO_SESSION")

if not session:
    print("ERROR: PO_SESSION is missing")
    raise SystemExit(1)

print("PO_SESSION found")

async def main():
    print("Creating Pocket Option client...")

    client = PocketOptionClient()

    print("Connecting to Pocket Option...")

    try:
        result = await client.connect(session)

        print("CONNECT RESULT:")
        print(result)

        print("AUTHORIZED:", client.is_authorized())

        if client.is_authorized():
            print("POCKET OPTION CONNECTION SUCCESSFUL")
            print("LIVE CONNECTION READY")
        else:
            print("POCKET OPTION CONNECTION NOT AUTHORIZED")

        await client.wait()

    except Exception as e:
        print("CONNECTION ERROR:")
        print(type(e).__name__, str(e))

if __name__ == "__main__":
    asyncio.run(main())
