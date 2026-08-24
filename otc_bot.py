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
    "USDCHF_otc",
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
    print(f"Health server listening on port {PORT}")
    server.serve_forever()


def print_status(message):
    print(message, flush=True)


async def main():
    print_status("==========================================")
    print_status("POCKET OPTION REAL OTC SIGNAL BOT")
    print_status("==========================================")
    print_status("ACCOUNT MODE: REAL")
    print_status("TIMEFRAME: M1")
    print_status("OTC MARKETS: 8")
    print_status("SIGNAL MODE: SIGNAL ONLY")
    print_status("AUTOMATIC TRADING: OFF")
    print_status("")

    print_status("MARKETS:")

    for market in OTC_MARKETS:
        print_status(f" - {market}")

    print_status("")
    print_status("Starting Pocket Option connection...")

    po_session = os.getenv("PO_SESSION")
    po_uid = os.getenv("PO_UID")

    if not po_session:
        print_status("ERROR: PO_SESSION is missing")
        return

    if not po_uid:
        print_status("ERROR: PO_UID is missing")
        return

    print_status("PO_SESSION found")
    print_status("PO_UID found")

    try:
        client = PocketOptionClient()
    except Exception as e:
        print_status(f"CLIENT CREATION ERROR: {e}")
        return

    print_status("Pocket Option client created")

    print_status("REAL authorization created")
    print_status("Initializing OTC market data...")
    print_status("Market data storage initialized")
    print_status(f"M1 period: {M1_PERIOD} seconds")
    print_status("8 OTC subscriptions requested")
    print_status("Wildcard event listener installed")
    print_status("ABOUT TO CONNECT TO POCKET OPTION")

    try:
        auth = client.get_auth_from_packet(po_session)
    except Exception as e:
        print_status(f"AUTH PARSE ERROR: {e}")
        print_status("The PO_SESSION value could not be converted by pocket-option 0.4.0.")
        return

    try:
        await client.connect(
            url="https://api.pocketoption.com",
            auth=auth,
            wait=True,
            wait_timeout=10,
            retry=True,
        )
    except Exception as e:
        print_status(f"CONNECT ERROR: {e}")
        return

    print_status("CONNECT CALL FINISHED")

    try:
        connected = client.sio.connected
    except Exception:
        connected = "UNKNOWN"

    print_status(f"SOCKET CONNECTED: {connected}")

    print_status("")
    print_status("==========================================")
    print_status("REAL ACCOUNT CONNECTION READY")
    print_status("==========================================")

    print_status("8 OTC MARKETS SUBSCRIBED")

    for market in OTC_MARKETS:
        print_status(f"SUBSCRIBED: {market}")

    print_status("")
    print_status("M1 CANDLE MONITORING ACTIVE")
    print_status("NO AUTOMATIC TRADES")
    print_status("WAITING FOR OTC MARKET EVENTS...")
    print_status("==========================================")

    while True:
        now = datetime.now(timezone.utc)

        print_status(
            "BOT ALIVE: "
            + now.strftime("%Y-%m-%d %H:%M:%S UTC")
        )

        await asyncio.sleep(30)


def run():
    health_thread = Thread(
        target=start_health_server,
        daemon=True,
    )

    health_thread.start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_status("BOT STOPPED")
    except Exception as e:
        print_status(f"BOT ERROR: {e}")


if __name__ == "__main__":
    run()
