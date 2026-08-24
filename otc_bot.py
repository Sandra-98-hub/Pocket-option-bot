import os
import asyncio
import inspect

from pocket_option import PocketOptionClient


async def main():
    print("==========================================")
    print("POCKET OPTION 0.4.0 PROPERTY INSPECTION")
    print("==========================================")

    ssid = os.getenv("PO_SESSION")
    uid = os.getenv("PO_UID")

    if not ssid:
        print("PO_SESSION missing")
        return

    if not uid:
        print("PO_UID missing")
        return

    print("PO_SESSION found")
    print("PO_UID found")

    try:
        client = PocketOptionClient(
            ssid=ssid,
            uid=uid,
            is_demo=False
        )
    except TypeError:
        client = PocketOptionClient(
            ssid=ssid,
            uid=uid
        )

    print("CLIENT CREATED")

    print("CONNECTING...")

    try:
        await client.connect()
    except Exception as e:
        print("CONNECT ERROR:", repr(e))
        return

    print("CONNECTED")

    try:
        candles = client.candles

        print("")
        print("==========================================")
        print("CANDLES OBJECT")
        print("==========================================")
        print(type(candles))
        print(candles)

        print("")
        print("CANDLES MEMBERS")

        for name in dir(candles):
            if not name.startswith("_"):
                try:
                    obj = getattr(candles, name)

                    if callable(obj):
                        try:
                            print(
                                name,
                                inspect.signature(obj)
                            )
                        except Exception:
                            print(name)
                    else:
                        print(name)

                except Exception:
                    pass

    except Exception as e:
        print("CANDLES ERROR:", repr(e))

    try:
        assets = client.assets

        print("")
        print("==========================================")
        print("ASSETS OBJECT")
        print("==========================================")
        print(type(assets))
        print(assets)

        print("")
        print("ASSETS MEMBERS")

        for name in dir(assets):
            if not name.startswith("_"):
                try:
                    obj = getattr(assets, name)

                    if callable(obj):
                        try:
                            print(
                                name,
                                inspect.signature(obj)
                            )
                        except Exception:
                            print(name)
                    else:
                        print(name)

                except Exception:
                    pass

    except Exception as e:
        print("ASSETS ERROR:", repr(e))

    print("")
    print("==========================================")
    print("INSPECTION COMPLETE")
    print("==========================================")

    while True:
        await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(main())
