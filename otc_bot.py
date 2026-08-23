```python
import os
import asyncio
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

from pocket_option import PocketOptionClient
from pocket_option.constants import Regions
from pocket_option.contrib.default_init import default_init
from pocket_option.models import Asset, AuthorizationData


# ============================================================
# SETTINGS
# ============================================================

PORT = int(os.getenv("PORT", "10000"))

# REAL ACCOUNT
IS_DEMO = 0

# M1 = 60 seconds
CANDLE_PERIOD = 60

# 8 OTC MARKETS
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


# ============================================================
# HEALTH SERVER FOR RENDER
# ============================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(
            b"Pocket Option OTC Signal Bot is running"
        )

    def log_message(self, format, *args):
        pass


def start_health_server():

    server = HTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler
    )

    print(
        f"Health server listening on port {PORT}",
        flush=True
    )

    server.serve_forever()


# ============================================================
# SAFE VALUE READER
# ============================================================

def get_value(obj, name, default=None):

    try:

        if isinstance(obj, dict):
            return obj.get(name, default)

        return getattr(obj, name, default)

    except Exception:

        return default


# ============================================================
# PRINT CANDLE
# ============================================================

def print_candle(market, candle):

    received = datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )

    candle_time = get_value(
        candle,
        "time"
    )

    open_price = get_value(
        candle,
        "open"
    )

    high_price = get_value(
        candle,
        "high"
    )

    low_price = get_value(
        candle,
        "low"
    )

    close_price = get_value(
        candle,
        "close"
    )

    print(
        "==========================================",
        flush=True
    )

    print(
        "NEW M1 OTC CANDLE",
        flush=True
    )

    print(
        "MARKET:",
        market,
        flush=True
    )

    print(
        "CANDLE TIME:",
        candle_time,
        flush=True
    )

    print(
        "OPEN:",
        open_price,
        flush=True
    )

    print(
        "HIGH:",
        high_price,
        flush=True
    )

    print(
        "LOW:",
        low_price,
        flush=True
    )

    print(
        "CLOSE:",
        close_price,
        flush=True
    )

    print(
        "RECEIVED:",
        received,
        flush=True
    )

    print(
        "==========================================",
        flush=True
    )


# ============================================================
# CANDLE MONITOR
# ============================================================

async def monitor_candles(client):

    print(
        "CANDLE MONITOR STARTED",
        flush=True
    )

    candles = getattr(
        client,
        "candles",
        None
    )

    if candles is None:

        print(
            "ERROR: Candle storage unavailable",
            flush=True
        )

        return

    print(
        "CANDLE STORAGE:",
        type(candles).__name__,
        flush=True
    )

    last_seen = {}

    while True:

        try:

            for market in OTC_MARKETS:

                result = None

                # Try positional argument first.
                try:

                    result = candles.get_candles(
                        market
                    )

                except TypeError:

                    # Try keyword form.
                    try:

                        result = candles.get_candles(
                            asset=market
                        )

                    except Exception:
                        result = None

                except Exception:

                    result = None

                if result is None:
                    continue

                # Normalize result.
                if isinstance(
                    result,
                    (list, tuple)
                ):

                    candle_list = list(result)

                else:

                    candle_list = [result]

                if not candle_list:
                    continue

                latest = candle_list[-1]

                candle_time = get_value(
                    latest,
                    "time"
                )

                close_price = get_value(
                    latest,
                    "close"
                )

                key = (
                    str(candle_time),
                    str(close_price)
                )

                market_name = str(market)

                if last_seen.get(
                    market_name
                ) != key:

                    last_seen[
                        market_name
                    ] = key

                    print_candle(
                        market_name,
                        latest
                    )

            await asyncio.sleep(1)

        except asyncio.CancelledError:

            return

        except Exception as e:

            print(
                "CANDLE MONITOR ERROR:",
                type(e).__name__,
                str(e),
                flush=True
            )

            await asyncio.sleep(5)


# ============================================================
# MAIN BOT
# ============================================================

async def main():

    print(
        "==========================================",
        flush=True
    )

    print(
        "POCKET OPTION REAL OTC SIGNAL BOT",
        flush=True
    )

    print(
        "==========================================",
        flush=True
    )

    print(
        "ACCOUNT MODE: REAL",
        flush=True
    )

    print(
        "TIMEFRAME: M1",
        flush=True
    )

    print(
        "OTC MARKETS: 8",
        flush=True
    )

    print(
        "SIGNAL MODE: SIGNAL ONLY",
        flush=True
    )

    print(
        "AUTOMATIC TRADES: OFF",
        flush=True
    )

    # ========================================================
    # ENVIRONMENT VARIABLES
    # ========================================================

    session = os.getenv(
        "PO_SESSION"
    )

    uid = os.getenv(
        "PO_UID"
    )

    if not session:

        print(
            "ERROR: PO_SESSION is missing",
            flush=True
        )

        return

    if not uid:

        print(
            "ERROR: PO_UID is missing",
            flush=True
        )

        return

    print(
        "PO_SESSION found",
        flush=True
    )

    print(
        "PO_UID found",
        flush=True
    )

    # ========================================================
    # CLIENT
    # ========================================================

    try:

        client = PocketOptionClient(
            logger=False
        )

        print(
            "Pocket Option client created",
            flush=True
        )

    except Exception as e:

        print(
            "CLIENT CREATION ERROR:",
            type(e).__name__,
            str(e),
            flush=True
        )

        return

    # ========================================================
    # REAL AUTHORIZATION
    # ========================================================

    try:

        authorization = AuthorizationData.model_validate(
            {
                "session": session,
                "isDemo": IS_DEMO,
                "uid": int(uid),
                "platform": 2,
                "isFastHistory": True,
                "isOptimized": True,
            }
        )

        print(
            "REAL authorization created",
            flush=True
        )

    except Exception as e:

        print(
            "AUTHORIZATION ERROR:",
            type(e).__name__,
            str(e),
            flush=True
        )

        return

    # ========================================================
    # INITIALIZE MARKET DATA
    # ========================================================

    try:

        print(
            "Initializing Pocket Option market data...",
            flush=True
        )

        default_init(
            client,
            authorization=authorization,
            sub_assets=OTC_MARKETS,
            sub_period=CANDLE_PERIOD,
        )

        print(
            "Market data storage initialized",
            flush=True
        )

    except Exception as e:

        print(
            "MARKET DATA INITIALIZATION ERROR:",
            type(e).__name__,
            str(e),
            flush=True
        )

        return

    # ========================================================
    # CONNECT
    # ========================================================

    print(
        "ABOUT TO CONNECT TO POCKET OPTION",
        flush=True
    )

    try:

        await client.connect(
            Regions.DEMO
        )

        print(
            "CONNECT CALL FINISHED",
            flush=True
        )

    except Exception as e:

        print(
            "CONNECTION ERROR:",
            type(e).__name__,
            str(e),
            flush=True
        )

        return

    # ========================================================
    # SOCKET STATUS
    # ========================================================

    try:

        connected = client.sio.connected

    except Exception:

        connected = False

    print(
        "SOCKET CONNECTED:",
        connected,
        flush=True
    )

    print(
        "REAL MODE:",
        IS_DEMO == 0,
        flush=True
    )

    # ========================================================
    # STORAGE STATUS
    # ========================================================

    try:

        print(
            "ASSETS STORAGE READY:",
            type(client.assets).__name__,
            flush=True
        )

    except Exception as e:

        print(
            "ASSETS STORAGE ERROR:",
            type(e).__name__,
            str(e),
            flush=True
        )

    try:

        print(
            "CANDLE STORAGE READY:",
            type(client.candles).__name__,
            flush=True
        )

    except Exception as e:

        print(
            "CANDLE STORAGE ERROR:",
            type(e).__name__,
            str(e),
            flush=True
        )

    # ========================================================
    # SUBSCRIPTIONS
    # ========================================================

    print(
        "==========================================",
        flush=True
    )

    print(
        "8 OTC MARKETS SUBSCRIBED",
        flush=True
    )

    for market in OTC_MARKETS:

        print(
            "OTC SUBSCRIPTION:",
            market,
            flush=True
        )

    print(
        "M1 CANDLE MONITORING ACTIVE",
        flush=True
    )

    print(
        "NO AUTOMATIC TRADES",
        flush=True
    )

    print(
        "==========================================",
        flush=True
    )

    # ========================================================
    # START CANDLE MONITOR
    # ========================================================

    asyncio.create_task(
        monitor_candles(client)
    )

    # ========================================================
    # KEEP BOT ALIVE
    # ========================================================

    while True:

        now = datetime.now(
            timezone.utc
        ).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )

        print(
            "BOT ALIVE:",
            now,
            flush=True
        )

        await asyncio.sleep(30)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    threading.Thread(
        target=start_health_server,
        daemon=True
    ).start()

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        print(
            "BOT STOPPED",
            flush=True
        )

    except Exception as e:

        print(
            "FATAL ERROR:",
            type(e).__name__,
            str(e),
            flush=True
        )
```
