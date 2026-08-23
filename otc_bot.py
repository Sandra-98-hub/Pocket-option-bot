```python
import os
import asyncio
import threading
import inspect
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

from pocket_option import PocketOptionClient
from pocket_option.constants import Regions
from pocket_option.contrib.default_init import default_init
from pocket_option.models import Asset, AuthorizationData


# ============================================================
# SETTINGS
# ============================================================

IS_DEMO = 0
CANDLE_PERIOD = 60
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


# ============================================================
# STARTUP
# ============================================================

print("==========================================", flush=True)
print("POCKET OPTION REAL OTC CANDLE MONITOR", flush=True)
print("==========================================", flush=True)

print("ACCOUNT MODE: REAL", flush=True)
print("TIMEFRAME: M1", flush=True)
print("OTC MARKETS: 8", flush=True)
print("AUTOMATIC TRADING: OFF", flush=True)

for market in OTC_MARKETS:
    print("SUBSCRIBE:", market, flush=True)


# ============================================================
# RENDER HEALTH SERVER
# ============================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(
            b"Pocket Option OTC candle monitor is running"
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
# SAFE OBJECT READER
# ============================================================

def safe_get(obj, name, default=None):

    try:

        if isinstance(obj, dict):
            return obj.get(name, default)

        return getattr(obj, name, default)

    except Exception:

        return default


# ============================================================
# CANDLE DISPLAY
# ============================================================

def print_candle(market, candle):

    now = datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )

    print(
        "==========================================",
        flush=True
    )

    print(
        "NEW M1 CANDLE",
        flush=True
    )

    print(
        "MARKET:",
        market,
        flush=True
    )

    print(
        "RECEIVED:",
        now,
        flush=True
    )

    print(
        "TIME:",
        safe_get(candle, "time"),
        flush=True
    )

    print(
        "OPEN:",
        safe_get(candle, "open"),
        flush=True
    )

    print(
        "HIGH:",
        safe_get(candle, "high"),
        flush=True
    )

    print(
        "LOW:",
        safe_get(candle, "low"),
        flush=True
    )

    print(
        "CLOSE:",
        safe_get(candle, "close"),
        flush=True
    )

    print(
        "==========================================",
        flush=True
    )


# ============================================================
# CANDLE STORAGE MONITOR
# ============================================================

async def monitor_candle_storage(client):

    print(
        "Starting candle storage monitor...",
        flush=True
    )

    candles = getattr(
        client,
        "candles",
        None
    )

    if candles is None:

        print(
            "ERROR: client.candles is unavailable",
            flush=True
        )

        return


    print(
        "CANDLE STORAGE:",
        type(candles).__name__,
        flush=True
    )


    # --------------------------------------------------------
    # Show the actual method signature in the logs.
    # This avoids guessing the API of the installed version.
    # --------------------------------------------------------

    try:

        method = getattr(
            candles,
            "get_candles",
            None
        )

        if method:

            print(
                "get_candles signature:",
                inspect.signature(method),
                flush=True
            )

    except Exception as e:

        print(
            "Could not inspect get_candles:",
            type(e).__name__,
            str(e),
            flush=True
        )


    last_seen = {}

    while True:

        try:

            for market in OTC_MARKETS:

                # ------------------------------------------------
                # Storage normally uses the Asset enum as the key.
                # ------------------------------------------------

                try:

                    result = candles.get_candles(
                        market
                    )

                except TypeError:

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


                # ------------------------------------------------
                # Normalize the result into a list.
                # ------------------------------------------------

                if isinstance(result, (list, tuple)):

                    items = list(result)

                else:

                    items = [result]


                if not items:
                    continue


                latest = items[-1]

                candle_time = safe_get(
                    latest,
                    "time"
                )

                close = safe_get(
                    latest,
                    "close"
                )


                # ------------------------------------------------
                # Only print a candle when it is new.
                # ------------------------------------------------

                key = (
                    str(candle_time),
                    str(close)
                )

                market_key = str(market)

                if last_seen.get(market_key) != key:

                    last_seen[market_key] = key

                    print_candle(
                        market_key,
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
# MAIN
# ============================================================

async def main():

    print(
        "Starting Pocket Option connection...",
        flush=True
    )


    # ========================================================
    # ENVIRONMENT
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
    # MARKET DATA INITIALIZATION
    # ========================================================

    try:

        print(
            "Initializing 8 OTC M1 subscriptions...",
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

        print(
            "8 OTC subscriptions requested",
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
    # CONNECTION STATUS
    # ========================================================

    connected = getattr(
        client.sio,
        "connected",
        False
    )

    print(
        "SOCKET CONNECTED:",
        connected,
        flush=True
    )

    print(
        "REAL MODE FLAG:",
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
    # START CANDLE MONITOR
    # ========================================================

    asyncio.create_task(
        monitor_candle_storage(client)
    )


    # ========================================================
    # READY
    # ========================================================

    print("==========================================", flush=True)

    print(
        "REAL ACCOUNT CONNECTION READY",
        flush=True
    )

    print(
        "8 OTC MARKETS SUBSCRIBED",
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
        "WAITING FOR CANDLES...",
        flush=True
    )

    print("==========================================", flush=True)


    # ========================================================
    # KEEP ALIVE
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
            "Bot stopped",
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
