import os
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from pocket_option import PocketOptionClient
from pocket_option.constants import Regions
from pocket_option.contrib.default_init import default_init
from pocket_option.models import AuthorizationData, Asset


# ==========================================
# RENDER HEALTH SERVER
# ==========================================

PORT = int(os.getenv("PORT", "10000"))


class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Pocket Option bot is running")

    def log_message(self, format, *args):
        pass


def start_web_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    print(f"Health server listening on port {PORT}", flush=True)
    server.serve_forever()


# ==========================================
# POCKET OPTION
# ==========================================

async def main():

    print("==================================", flush=True)
    print("POCKET OPTION LIVE CANDLE TEST", flush=True)
    print("==================================", flush=True)

    session = os.getenv("PO_SESSION")
    uid = os.getenv("PO_UID")

    if not session:
        print("ERROR: PO_SESSION is missing", flush=True)
        return

    if not uid:
        print("ERROR: PO_UID is missing", flush=True)
        return

    print("PO_SESSION found", flush=True)
    print("PO_UID found", flush=True)

    client = PocketOptionClient(logger=True)

    authorization = AuthorizationData.model_validate({
        "session": session,
        "isDemo": 1,
        "uid": int(uid),
        "platform": 2,
        "isFastHistory": True,
        "isOptimized": True,
    })

    print("Authorization created", flush=True)

    # EUR/USD OTC ONLY for this test
    asset = Asset.EURUSD_otc

    print("Asset selected: EURUSD_otc", flush=True)

    # Subscribe to the EUR/USD OTC stream
    default_init(
        client,
        authorization=authorization,
        sub_assets=[asset],
        sub_period=60,
    )

    print("Market subscription configured", flush=True)

    try:

        print("Connecting to Pocket Option...", flush=True)

        await client.connect(Regions.DEMO)

        print("CONNECT CALL FINISHED", flush=True)

        await client.authorized_event.wait()

        print("==================================", flush=True)
        print("POCKET OPTION AUTHORIZED", flush=True)
        print("EUR/USD OTC SUBSCRIPTION ACTIVE", flush=True)
        print("WAITING FOR LIVE CANDLES...", flush=True)
        print("==================================", flush=True)

        while True:
            await asyncio.sleep(60)

    except Exception as e:

        print("==================================", flush=True)
        print("ERROR", flush=True)
        print(type(e).__name__, str(e), flush=True)
        print("==================================", flush=True)


# ==========================================
# START
# ==========================================

if __name__ == "__main__":

    print("Starting Render health server...", flush=True)

    threading.Thread(
        target=start_web_server,
        daemon=True
    ).start()

    print("Starting Pocket Option connection...", flush=True)

    asyncio.run(main())
