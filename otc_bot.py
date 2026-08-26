import os
import asyncio
import logging
from collections import defaultdict, deque
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from pocket_option import PocketOptionClient
from pocket_option.constants import Regions
from pocket_option.contrib.default_init import default_init
from pocket_option.models import (
    Asset,
    AuthorizationData,
    UpdateCloseValueItem,
)


# ============================================================
# POCKET OPTION 0.4.0 OTC M1 SIGNAL BOT
# ============================================================

print("=" * 60)
print("POCKET OPTION 0.4.0 OTC M1 SIGNAL BOT")
print("=" * 60)

ACCOUNT_MODE = "REAL"
TIMEFRAME = "M1"
CANDLE_PERIOD = 60

SIGNAL_ONLY = True
AUTOMATIC_TRADING = False

PORT = int(os.getenv("PORT", "10000"))

REGION_NAME = os.getenv(
    "PO_REGION",
    "EUROPA"
)


# ============================================================
# OTC MARKETS
# ============================================================

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
# STRATEGY SETTINGS
# ============================================================

EMA_FAST = 9
EMA_SLOW = 21
RSI_PERIOD = 14

MIN_PRICES = 30
MIN_SCORE = 80


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(
    "POCKET_OPTION_OTC"
)


# ============================================================
# CLIENT
# ============================================================

client = PocketOptionClient(
    logger=True
)


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
            b"Pocket Option OTC M1 Signal Bot is running"
        )

    def log_message(
        self,
        format,
        *args
    ):
        return


def start_health_server():

    server = HTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler
    )

    print(
        f"Health server listening on port {PORT}"
    )

    server.serve_forever()


# ============================================================
# DATA STORAGE
# ============================================================

price_history = defaultdict(
    lambda: deque(
        maxlen=500
    )
)

last_price = {}

last_minute = {}

last_signal_minute = {}


# ============================================================
# ASSET NAMES
# ============================================================

ASSET_NAMES = {
    Asset.EURUSD_otc: "EURUSD_otc",
    Asset.GBPUSD_otc: "GBPUSD_otc",
    Asset.USDJPY_otc: "USDJPY_otc",
    Asset.AUDUSD_otc: "AUDUSD_otc",
    Asset.AUDCAD_otc: "AUDCAD_otc",
    Asset.AUDNZD_otc: "AUDNZD_otc",
    Asset.EURGBP_otc: "EURGBP_otc",
    Asset.USDCHF_otc: "USDCHF_otc",
}

ALLOWED_ASSETS = set(
    ASSET_NAMES.values()
)


# ============================================================
# EMA
# ============================================================

def calculate_ema(values, period):

    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)

    result = (
        sum(values[:period])
        / period
    )

    for value in values[period:]:

        result = (
            (value - result)
            * multiplier
        ) + result

    return result


# ============================================================
# RSI
# ============================================================

def calculate_rsi(
    values,
    period=14
):

    if len(values) < period + 1:
        return None

    gains = []
    losses = []

    for index in range(
        1,
        len(values)
    ):

        change = (
            values[index]
            - values[index - 1]
        )

        if change > 0:

            gains.append(change)
            losses.append(0)

        else:

            gains.append(0)
            losses.append(abs(change))

    if len(gains) < period:
        return None

    average_gain = (
        sum(gains[:period])
        / period
    )

    average_loss = (
        sum(losses[:period])
        / period
    )

    for index in range(
        period,
        len(gains)
    ):

        average_gain = (
            (
                average_gain
                * (period - 1)
            )
            + gains[index]
        ) / period

        average_loss = (
            (
                average_loss
                * (period - 1)
            )
            + losses[index]
        ) / period

    if average_loss == 0:

        return 100.0

    rs = (
        average_gain
        / average_loss
    )

    return 100 - (
        100 / (1 + rs)
    )


# ============================================================
# SIGNAL ENGINE
# ============================================================

def calculate_signal(
    asset_name
):

    values = list(
        price_history[asset_name]
    )

    if len(values) < MIN_PRICES:
        return None

    price = values[-1]

    ema9 = calculate_ema(
        values,
        EMA_FAST
    )

    ema21 = calculate_ema(
        values,
        EMA_SLOW
    )

    rsi = calculate_rsi(
        values,
        RSI_PERIOD
    )

    if (
        ema9 is None
        or ema21 is None
        or rsi is None
    ):
        return None


    # ========================================================
    # BUY
    # ========================================================

    buy_score = 0

    if ema9 > ema21:
        buy_score += 40

    if price > ema9:
        buy_score += 20

    if rsi > 50:
        buy_score += 20

    if rsi < 70:
        buy_score += 20

    if (
        buy_score >= MIN_SCORE
        and ema9 > ema21
        and rsi > 50
    ):

        return {
            "direction": "BUY",
            "score": buy_score,
            "price": price,
            "ema9": ema9,
            "ema21": ema21,
            "rsi": rsi,
        }


    # ========================================================
    # SELL
    # ========================================================

    sell_score = 0

    if ema9 < ema21:
        sell_score += 40

    if price < ema9:
        sell_score += 20

    if rsi < 50:
        sell_score += 20

    if rsi > 30:
        sell_score += 20

    if (
        sell_score >= MIN_SCORE
        and ema9 < ema21
        and rsi < 50
    ):

        return {
            "direction": "SELL",
            "score": sell_score,
            "price": price,
            "ema9": ema9,
            "ema21": ema21,
            "rsi": rsi,
        }

    return None


# ============================================================
# PRINT SIGNAL
# ============================================================

def print_signal(
    asset_name,
    signal
):

    now = datetime.now(
        timezone.utc
    )

    minute_key = now.strftime(
        "%Y-%m-%d %H:%M"
    )

    if (
        last_signal_minute.get(
            asset_name
        )
        == minute_key
    ):
        return

    last_signal_minute[
        asset_name
    ] = minute_key

    print("")
    print("=" * 60)
    print(
        "🚨 LIVE POCKET OPTION OTC M1 SIGNAL 🚨"
    )
    print("=" * 60)

    print(
        f"MARKET:     {asset_name}"
    )

    print(
        f"SIGNAL:     {signal['direction']}"
    )

    print(
        "TIME UTC:   "
        f"{now.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print(
        f"PRICE:      "
        f"{signal['price']:.6f}"
    )

    print(
        f"EMA(9):     "
        f"{signal['ema9']:.6f}"
    )

    print(
        f"EMA(21):    "
        f"{signal['ema21']:.6f}"
    )

    print(
        f"RSI(14):    "
        f"{signal['rsi']:.2f}"
    )

    print(
        f"SCORE:      "
        f"{signal['score']}%"
    )

    print(
        "SOURCE:     Pocket Option OTC"
    )

    print(
        "TIMEFRAME:  M1"
    )

    print(
        "AUTOMATIC:  OFF"
    )

    print("=" * 60)
    print("")


# ============================================================
# PROCESS PRICE
# ============================================================

def process_price(
    asset_name,
    price
):

    try:

        price = float(price)

    except (
        TypeError,
        ValueError
    ):

        return

    if price <= 0:
        return

    last_price[
        asset_name
    ] = price

    price_history[
        asset_name
    ].append(price)

    now = datetime.now(
        timezone.utc
    )

    current_minute = now.replace(
        second=0,
        microsecond=0
    )

    previous_minute = last_minute.get(
        asset_name
    )

    if previous_minute == current_minute:
        return

    last_minute[
        asset_name
    ] = current_minute

    count = len(
        price_history[
            asset_name
        ]
    )

    print(
        f"[M1 DATA] "
        f"{asset_name} | "
        f"price={price:.6f} | "
        f"data={count} | "
        f"time="
        f"{current_minute.strftime('%H:%M:%S')} UTC"
    )

    if count < MIN_PRICES:

        print(
            f"[DATA] "
            f"{asset_name}: "
            f"collecting "
            f"{count}/{MIN_PRICES}"
        )

        return

    signal = calculate_signal(
        asset_name
    )

    if signal:

        print_signal(
            asset_name,
            signal
        )

    else:

        print(
            f"[NO SIGNAL] "
            f"{asset_name} | "
            f"EMA/RSI not aligned"
        )


# ============================================================
# POCKET OPTION REAL-TIME PRICE EVENT
# ============================================================

@client.on.update_close_value
async def on_update_close_value(
    assets: list[UpdateCloseValueItem],
):

    try:

        for item in assets:

            asset_name = ASSET_NAMES.get(
                item.asset
            )

            if not asset_name:
                continue

            if asset_name not in ALLOWED_ASSETS:
                continue

            try:

                price = float(
                    item.value
                )

            except (
                TypeError,
                ValueError
            ):

                continue

            process_price(
                asset_name,
                price
            )

    except Exception:

        logger.exception(
            "ERROR PROCESSING OTC PRICE UPDATE"
        )


# ============================================================
# CONNECTION EVENT
# ============================================================

@client.on.connect
async def on_connect(
    _data=None
):

    print(
        "POCKET OPTION SOCKET CONNECTED"
    )


# ============================================================
# DISCONNECT EVENT
# ============================================================

@client.on.disconnect
async def on_disconnect(
    _data=None
):

    print(
        "POCKET OPTION SOCKET DISCONNECTED"
    )


# ============================================================
# AUTH EVENT
# ============================================================

@client.on.success_auth
async def on_success_auth(
    data=None
):

    print(
        "POCKET OPTION AUTHORIZATION SUCCESSFUL"
    )


# ============================================================
# REGION
# ============================================================

def get_region():

    region_map = {

        "EUROPA":
            Regions.EUROPA,

        "ASIA":
            Regions.ASIA,

        "UNITED_STATES_NORTH":
            Regions.UNITED_STATES_NORTH,

        "UNITED_STATES_SOUTH":
            Regions.UNITED_STATES_SOUTH,

        "UNITED_STATES_2":
            Regions.UNITED_STATES_2,

        "UNITED_STATES_3":
            Regions.UNITED_STATES_3,

        "UNITED_STATES_4":
            Regions.UNITED_STATES_4,

        "FRANCE_1":
            Regions.FRANCE_1,

        "FRANCE_2":
            Regions.FRANCE_2,

        "RUSSIA":
            Regions.RUSSIA,

        "INDIA":
            Regions.INDIA,

        "FINLAND":
            Regions.FINLAND,

        "SEYCHELLES":
            Regions.SEYCHELLES,

        "HONGKONG":
            Regions.HONGKONG,

        "SERVER_1":
            Regions.SERVER_1,

        "SERVER_2":
            Regions.SERVER_2,

        "SERVER_3":
            Regions.SERVER_3,
    }

    region = region_map.get(
        REGION_NAME.upper()
    )

    if region is None:

        print(
            f"Unknown PO_REGION: {REGION_NAME}"
        )

        print(
            "Using EUROPA"
        )

        region = Regions.EUROPA

    return region


# ============================================================
# MAIN
# ============================================================

async def main():

    session = os.getenv(
        "PO_SESSION"
    )

    uid = os.getenv(
        "PO_UID"
    )

    if not session:

        print(
            "FATAL: PO_SESSION is missing"
        )

        return

    if not uid:

        print(
            "FATAL: PO_UID is missing"
        )

        return

    try:

        uid_number = int(uid)

    except ValueError:

        print(
            "FATAL: PO_UID must be a number"
        )

        return


    print(
        "ACCOUNT MODE:",
        ACCOUNT_MODE
    )

    print(
        "TIMEFRAME:",
        TIMEFRAME
    )

    print(
        "SIGNAL ONLY"
    )

    print(
        "AUTOMATIC TRADING: OFF"
    )

    print(
        "PO_SESSION found"
    )

    print(
        "PO_UID found"
    )


    # ========================================================
    # AUTHORIZATION
    # ========================================================

    try:

        authorization = (
            AuthorizationData.model_validate(
                {
                    "session": session,
                    "isDemo": 0,
                    "uid": uid_number,
                    "platform": 2,
                    "isFastHistory": True,
                    "isOptimized": True,
                }
            )
        )

    except Exception as exc:

        print(
            "AUTHORIZATION DATA ERROR:"
        )

        print(
            repr(exc)
        )

        return

    print(
        "AUTHORIZATION DATA CREATED"
    )


    # ========================================================
    # INITIALIZE CLIENT
    # ========================================================

    try:

        default_init(
            client,
            authorization=authorization,
            sub_assets=OTC_MARKETS,
            sub_period=CANDLE_PERIOD,
        )

    except Exception as exc:

        print(
            "DEFAULT INIT ERROR:"
        )

        print(
            repr(exc)
        )

        return

    print(
        "M1 CANDLE STORAGE INITIALIZED"
    )

    print(
        f"{len(OTC_MARKETS)} OTC MARKETS REGISTERED"
    )

    for asset in OTC_MARKETS:

        print(
            "WATCHING:",
            ASSET_NAMES[asset]
        )


    # ========================================================
    # REGION
    # ========================================================

    region = get_region()

    print(
        "POCKET OPTION REGION:",
        REGION_NAME.upper()
    )

    print(
        "CONNECTING TO POCKET OPTION..."
    )


    # ========================================================
    # CONNECT
    #
    # IMPORTANT:
    # pocket-option 0.4.0 uses a Regions value here.
    # ========================================================

    try:

        await client.connect(
            region
        )

    except Exception as exc:

        print("")
        print(
            "POCKET OPTION CONNECTION ERROR"
        )

        print(
            repr(exc)
        )

        print("")

        raise


    # ========================================================
    # READY
    # ========================================================

    print("")
    print("=" * 60)

    print(
        "POCKET OPTION CONNECTION ACTIVE"
    )

    print(
        "REAL ACCOUNT AUTHENTICATION INITIALIZED"
    )

    print(
        "8 OTC MARKETS REGISTERED"
    )

    print(
        "M1 MARKET DATA MONITORING ACTIVE"
    )

    print(
        "SIGNAL ONLY"
    )

    print(
        "AUTOMATIC TRADING: OFF"
    )

    print(
        "WAITING FOR OTC MARKET EVENTS..."
    )

    print("=" * 60)


    # ========================================================
    # KEEP ALIVE
    # ========================================================

    while True:

        await asyncio.sleep(30)

        now = datetime.now(
            timezone.utc
        )

        print(
            "BOT ALIVE: "
            f"{now.strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    health_thread = Thread(
        target=start_health_server,
        daemon=True
    )

    health_thread.start()

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        print(
            "BOT STOPPED"
        )

    except Exception as exc:

        print("")
        print(
            "FATAL BOT ERROR"
        )

        print(
            repr(exc)
        )

        print("")

        raise
