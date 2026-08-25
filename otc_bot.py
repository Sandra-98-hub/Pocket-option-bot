import os
import asyncio
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from pocket_option import PocketOptionClient
from pocket_option.constants import Regions
from pocket_option.contrib.default_init import default_init
from pocket_option.models import Asset, AuthorizationData

PORT = int(os.getenv("PORT", "10000"))

OTC_MARKETS = [
    Asset.EURUSD_otc,
    Asset.GBPUSD_otc,
    Asset.USDJPY_otc,
    Asset.AUDUSD_otc,
    Asset.AUDCAD_otc,
    Asset.AUDNZD_otc,
    Asset.EURGBP_otc,
    Asset.USDCHF_otc,
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
    status("POCKET OPTION 0.4.0 OTC M1 BOT")
    status("==========================================")
    status("ACCOUNT MODE: REAL")
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

    try:
        uid = int(po_uid)
    except ValueError:
        status("ERROR: PO_UID must contain numbers only")
        return

    status("PO_SESSION found")
    status("PO_UID found")

    try:
        authorization = AuthorizationData.model_validate({
            "session": po_session,
            "isDemo": 0,
            "uid": uid,
            "platform": 2,
            "isFastHistory": True,
            "isOptimized": True,
        })
    except Exception as error:
        status("AUTHORIZATION DATA ERROR: " + str(error))
        return

    status("AUTHORIZATION DATA CREATED")

    try:
        client = PocketOptionClient(logger=True)
    except Exception as error:
        status("CLIENT CREATION ERROR: " + str(error))
        return

    status("Pocket Option client created")

    try:
        default_init(
            client,
            authorization=authorization,
            sub_assets=OTC_MARKETS,
            sub_period=M1_PERIOD,
        )
    except Exception as error:
        status("DEFAULT INIT ERROR: " + str(error))
        return

    status("M1 CANDLE STORAGE INITIALIZED")
    status("8 OTC MARKETS REGISTERED")

    for market in OTC_MARKETS:
        status("WATCHING: " + str(market))

    status("CONNECTING TO POCKET OPTION...")

    try:
        await client.connect(Regions.EUROPA)
    except Exception as error:
        status("CONNECT ERROR: " + str(error))
        return

    status("POCKET OPTION CONNECTION ACTIVE")

    try:
        await client.authorized_event.wait()
        status("ACCOUNT AUTHORIZATION SUCCESSFUL")
    except Exception as error:
        status("AUTHORIZATION WAIT ERROR: " + str(error))
        return

    status("OTC MARKET STREAMS ACTIVE")
    status("WAITING FOR M1 PRICE EVENTS...")

    last_report = {}

    while True:
        for market in OTC_MARKETS:
            try:
                candles = await client.candles.get_candles(
                    market,
                    timeframe=M1_PERIOD,
                    count=2,
                )

                if candles:
                    candle = list(candles)[-1]

                    key = (
                        str(market),
                        candle.timestamp,
                        candle.open,
                        candle.high,
                        candle.low,
                        candle.close,
                    )

                    if last_report.get(str(market)) != key:
                        last_report[str(market)] = key
                        status(
                            "M1 CANDLE | "
                            + str(market)
                            + " | "
                            + candle.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
                            + " | O=" + str(candle.open)
                            + " H=" + str(candle.high)
                            + " L=" + str(candle.low)
                            + " C=" + str(candle.close)
                        )

            except Exception as error:
                status(
                    "CANDLE CHECK ERROR | "
                    + str(market)
                    + " | "
                    + str(error)
                )

        now = datetime.now(timezone.utc)
        status("BOT ALIVE: " + now.strftime("%Y-%m-%d %H:%M:%S UTC"))
        await asyncio.sleep(5)


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
