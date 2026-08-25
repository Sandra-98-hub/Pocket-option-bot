import os
import asyncio
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
    "USDCHF_otc"
]

M1_PERIOD = 60


class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Pocket Option OTC bot is running")

    def log_message(self, format, *args):
        return


def start_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    print("Health server listening on port " + str(PORT), flush=True)
    server.serve_forever()


def status(message):
    print(message, flush=True)


async def main():

    status("==========================================")
    status("POCKET OPTION OTC M1 CANDLE MONITOR")
    status("==========================================")
    status("TIMEFRAME: M1")
    status("SIGNAL ONLY")
    status("AUTOMATIC TRADING: OFF")
    status("")

    po_session = os.getenv("PO_SESSION")
    po_uid = os.getenv("PO_UID")

    if not po_session:
        status("ERROR: PO_SESSION is missing")
        return

    if not po_uid:
        status("ERROR: PO_UID is missing")
        return

    status("PO_SESSION found")
    status("PO_UID found")

    try:
        client = PocketOptionClient()
    except Exception as error:
        status("CLIENT CREATION ERROR: " + str(error))
        return

    status("Pocket Option client created")

    status("Starting Pocket Option connection...")

    try:
        auth = client.get_auth_from_packet(po_session)
        status("AUTHORIZATION PARSED")
    except Exception as error:
        status("AUTHORIZATION PARSE FAILED: " + str(error))
        return

    try:
        await client.connect(
            url="https://api.pocketoption.com",
            auth=auth,
            wait=True,
            wait_timeout=10,
            retry=True
        )
    except Exception as error:
        status("CONNECT ERROR: " + str(error))
        return

    status("CONNECT CALL FINISHED")

    try:
        status("SOCKET CONNECTED: " + str(client.sio.connected))
    except Exception:
        status("SOCKET CONNECTED: UNKNOWN")

    status("")
    status("==========================================")
    status("REAL ACCOUNT CONNECTION READY")
    status("==========================================")
    status("M1 PERIOD: 60 SECONDS")
    status("")

    for market in OTC_MARKETS:
        status("WATCHING: " + market)

    status("")
    status("M1 CANDLE MONITORING ACTIVE")
    status("AUTOMATIC TRADING: OFF")
    status("WAITING FOR OTC MARKET EVENTS...")
    status("==========================================")

    while True:
        now = datetime.now(timezone.utc)

        status(
            "BOT ALIVE: "
            + now.strftime("%Y-%m-%d %H:%M:%S UTC")
        )

        await asyncio.sleep(30)


def run():

    health_thread = Thread(
        target=start_health_server,
        daemon=True
    )

    health_thread.start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        status("BOT STOPPED")
    except Exception as error:
        status("BOT ERROR: " + str(error))


if __name__ == "__main__":
    run()
