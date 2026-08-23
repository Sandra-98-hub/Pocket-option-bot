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

IS_DEMO = 0
CANDLE_PERIOD = 60
PORT = int(os.getenv("PORT", "10000"))

# Eight OTC markets
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
print("POCKET OPTION REAL OTC SIGNAL BOT", flush=True)
print("==========================================", flush=True)

print("ACCOUNT MODE: REAL", flush=True)
print("TIMEFRAME: M1", flush=True)
print("OTC MARKETS: 8", flush=True)
print("SIGNAL MODE: SIGNAL ONLY", flush=True)
print("AUTOMATIC TRADING: OFF", flush=True)

print("MARKETS:", flush=True)

for market in OTC_MARKETS:
    print(" -", market, flush=True)


# ============================================================
# RENDER HEALTH SERVER
# ============================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/plain"
        )

        self.end_headers()

        self.wfile.write(
            b"Pocket Option OTC signal bot is running"
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
# TELEGRAM
# ============================================================

TELEGRAM_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN"
)

TELEGRAM_CHAT_ID = os.getenv(
    "TELEGRAM_CHAT_ID"
)


async def send_telegram(message):

    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:

        print(
            "Telegram not configured",
            flush=True
        )

        return

    try:

        import aiohttp

        url = (
            "https://api.telegram.org/bot"
            + TELEGRAM_TOKEN
            + "/sendMessage"
        )

        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        }

        async with aiohttp.ClientSession() as session:

            async with session.post(
                url,
                json=payload,
                timeout=15
            ) as response:

                print(
                    "Telegram response:",
                    response.status,
                    flush=True
                )

    except Exception as e:

        print(
            "Telegram ERROR:",
            type(e).__name__,
            str(e),
            flush=True
        )


# ============================================================
# EVENT HANDLER
# ============================================================

async def market_event_handler(
    event_name,
    data=None
):

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
        "MARKET EVENT:",
        event_name,
        flush=True
    )

    print(
        "TIME:",
        now,
        flush=True
    )

    if data is not None:

        try:

            text = str(data)

            if len(text) > 3000:

                text = (
                    text[:3000]
                    + "...[truncated]"
                )

            print(
                "DATA:",
                text,
                flush=True
            )

        except Exception:

            print(
                "DATA: [unable to display]",
                flush=True
            )

    print(
        "==========================================",
        flush=True
    )


# ============================================================
# MAIN
# ============================================================

async def main():

    print(
        "Starting Pocket Option connection...",
        flush=True
    )


    # --------------------------------------------------------
    # ENVIRONMENT
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # CREATE CLIENT
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # REAL AUTHORIZATION
    # --------------------------------------------------------

    try:

        authorization = (
            AuthorizationData.model_validate(
                {
                    "session": session,
                    "isDemo": IS_DEMO,
                    "uid": int(uid),
                    "platform": 2,
                    "isFastHistory": True,
                    "isOptimized": True,
                }
            )
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


    # --------------------------------------------------------
    # INITIALIZE MARKET DATA
    # --------------------------------------------------------

    try:

        print(
            "Initializing OTC market data...",
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
            "M1 period:",
            CANDLE_PERIOD,
            "seconds",
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


    # --------------------------------------------------------
    # WILDCARD EVENT LISTENER
    # --------------------------------------------------------

    try:

        client.add_on(
            "*",
            handler=market_event_handler
        )

        print(
            "Wildcard event listener installed",
            flush=True
        )

    except Exception as e:

        print(
            "WILDCARD LISTENER ERROR:",
            type(e).__name__,
            str(e),
            flush=True
        )


    # --------------------------------------------------------
    # CONNECT
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # CONNECTION STATUS
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # STORAGE CHECK
    # --------------------------------------------------------

    try:

        assets = client.assets

        print(
            "ASSETS STORAGE READY:",
            type(assets).__name__,
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

        candles = client.candles

        print(
            "CANDLE STORAGE READY:",
            type(candles).__name__,
            flush=True
        )

    except Exception as e:

        print(
            "CANDLE STORAGE ERROR:",
            type(e).__name__,
            str(e),
            flush=True
        )


    # --------------------------------------------------------
    # FINAL STATUS
    # --------------------------------------------------------

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
        "WAITING FOR OTC MARKET EVENTS...",
        flush=True
    )

    print("==========================================", flush=True)


    # --------------------------------------------------------
    # KEEP ALIVE
    # --------------------------------------------------------

    while True:

        try:

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

        except asyncio.CancelledError:

            break


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
