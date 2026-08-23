import os
import asyncio
import inspect
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from pocket_option import PocketOptionClient

PORT = int(os.getenv("PORT", "10000"))

OTC_MARKETS = [
    "EURUSD_otc",
    "GBPUSD_otc",
    "USDJPY_otc",
    "AUDUSD_otc",
    "AUDCAD_otc",
    "AUDNZD_otc",
    "EURGBP_otc",
    "USDCHF_otc",
]


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot running")

    def log_message(self, format, *args):
        return


def start_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    print(f"Health server listening on port {PORT}")
    server.serve_forever()


def inspect_object(name, obj):
    print("")
    print("==========================================")
    print(name)
    print("==========================================")

    try:
        members = [x for x in dir(obj) if not x.startswith("_")]

        print("PUBLIC MEMBERS:")
        print(members)

        for member_name in members:
            if any(
                word in member_name.lower()
                for word in ["candle", "asset", "market", "subscribe"]
            ):
                try:
                    member = getattr(obj, member_name)
                    print("")
                    print(f"{member_name} = {member}")

                    if callable(member):
                        try:
                            print(
                                "SIGNATURE:",
                                inspect.signature(member)
                            )
                        except Exception:
                            pass

                except Exception as e:
                    print(f"{member_name}: {e}")

    except Exception as e:
        print(f"INSPECTION ERROR: {e}")


async def main():
    print("==========================================")
    print("POCKET OPTION OTC CANDLE DIAGNOSTIC")
    print("==========================================")
    print("REAL ACCOUNT")
    print("M1")
    print("SIGNAL ONLY")
    print("AUTOMATIC TRADING: OFF")
    print("8 OTC MARKETS")
    print("")

    po_session = os.getenv("PO_SESSION")
    po_uid = os.getenv("PO_UID")

    if not po_session:
        print("ERROR: PO_SESSION missing")
        return

    if not po_uid:
        print("ERROR: PO_UID missing")
        return

    print("PO_SESSION found")
    print("PO_UID found")

    try:
        client = PocketOptionClient(
            ssid=po_session,
            uid=po_uid,
            is_demo=False
        )
    except TypeError:
        client = PocketOptionClient(
            ssid=po_session,
            uid=po_uid
        )

    print("Pocket Option client created")

    inspect_object("POCKET OPTION CLIENT", client)

    if hasattr(client, "sio"):
        inspect_object("SOCKET.IO OBJECT", client.sio)

    if hasattr(client, "candles"):
        print("")
        print("==========================================")
        print("CANDLES METHOD")
        print("==========================================")
        print("CANDLES:", client.candles)

        try:
            print(
                "CANDLES SIGNATURE:",
                inspect.signature(client.candles)
            )
        except Exception as e:
            print("SIGNATURE ERROR:", e)

    print("")
    print("Connecting to Pocket Option...")

    try:
        await client.connect()
    except Exception as e:
        print("CONNECT ERROR:", e)
        return

    print("CONNECT CALL FINISHED")

    try:
        print("SOCKET CONNECTED:", client.sio.connected)
    except Exception:
        print("SOCKET CONNECTED: UNKNOWN")

    print("")
    print("==========================================")
    print("CONNECTION READY")
    print("==========================================")

    for market in OTC_MARKETS:
        print(f"OTC MARKET: {market}")

    print("")
    print("DIAGNOSTIC COMPLETE")
    print("")

    while True:
        now = datetime.now(timezone.utc)

        print(
            "BOT ALIVE:",
            now.strftime("%Y-%m-%d %H:%M:%S UTC")
        )

        await asyncio.sleep(30)


def run():
    thread = Thread(
        target=start_health_server,
        daemon=True
    )
    thread.start()

    asyncio.run(main())


if __name__ == "__main__":
    run()
