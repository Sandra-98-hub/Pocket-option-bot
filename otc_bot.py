import asyncio
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from pocket_option import PocketOptionClient
from pocket_option.constants import Regions
from pocket_option.models import AuthorizationData


# ============================================================
# SETTINGS
# ============================================================

PORT = int(os.environ.get("PORT", "10000"))

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


# ============================================================
# SIMPLE WEB SERVER FOR RENDER
# ============================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Pocket Option OTC bot is running")

    def log_message(self, format, *args):
        return


def start_web_server():

    server = HTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler
    )

    print(f"Health server listening on port {PORT}")

    server.serve_forever()


# ============================================================
# POCKET OPTION
# ============================================================

client = PocketOptionClient(logger=True)


@client.on.connect
async def on_connect(data=None):

    print("")
    print("========================================")
    print("POCKET OPTION WEBSOCKET CONNECTED")
    print("========================================")

    session = os.getenv("PO_SESSION")
    uid = os.getenv("PO_UID")

    if not session:
        print("ERROR: PO_SESSION is missing")
        return

    if not uid:
        print("ERROR: PO_UID is missing")
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

        print("")
        print("AUTHENTICATION ERROR")
        print(type(error).__name__)
        print(str(error))


@client.on.success_auth
async def on_success_auth(data):

    print("")
    print("========================================")
    print("POCKET OPTION AUTHENTICATED")
    print("========================================")

    print("")
    print("Testing OTC markets:")

    for market in MARKETS:

        try:

            await client.emit.subscribe_to_asset(
                market
            )

            print(
                "SUBSCRIPTION REQUESTED:",
                market
            )

        except Exception as error:

            print(
                "SUBSCRIPTION ERROR:",
                market
            )

            print(
                type(error).__name__,
                str(error)
            )


# ============================================================
# POCKET OPTION LOOP
# ============================================================

async def pocket_option_loop():

    print("")
    print("========================================")
    print("POCKET OPTION OTC BOT")
    print("========================================")

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

        await client.connect(
            Regions.DEMO
        )

        while True:
            await asyncio.sleep(10)

    except Exception as error:

        print("")
        print("POCKET OPTION ERROR")
        print(type(error).__name__)
        print(str(error))


# ============================================================
# START
# ============================================================

def main():

    print("Starting Pocket Option OTC bot...")

    # Start Render health server.
    web_thread = threading.Thread(
        target=start_web_server,
        daemon=True
    )

    web_thread.start()

    # Start Pocket Option event loop.
    asyncio.run(
        pocket_option_loop()
    )


if __name__ == "__main__":
    main()
