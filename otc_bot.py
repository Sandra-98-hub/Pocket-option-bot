import os
import asyncio
import logging
import math
from collections import defaultdict, deque
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from pocket_option import PocketOptionClient
from pocket_option.constants import Regions
from pocket_option.contrib.default_init import default_init
from pocket_option.models import Asset, AuthorizationData


# ============================================================
# POCKET OPTION 0.4.0 OTC M1 SIGNAL BOT
# ============================================================

print("=" * 58)
print("POCKET OPTION 0.4.0 OTC M1 SIGNAL BOT")
print("=" * 58)

ACCOUNT_MODE = "REAL"
TIMEFRAME = "M1"
CANDLE_PERIOD = 60

SIGNAL_ONLY = True
AUTOMATIC_TRADING = False

PORT = int(os.getenv("PORT", "10000"))

# ------------------------------------------------------------
# OTC MARKETS
# ------------------------------------------------------------

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

# ------------------------------------------------------------
# STRATEGY SETTINGS
# ------------------------------------------------------------

EMA_FAST = 9
EMA_SLOW = 21
RSI_PERIOD = 14

MIN_CANDLES = 30

# We only print a signal when the conditions are aligned.
# This is NOT a guarantee of accuracy.
MIN_SCORE = 80


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("PO_OTC_BOT")


# ============================================================
# HEALTH SERVER FOR RENDER
# ============================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

        message = (
            "Pocket Option OTC M1 Signal Bot is running\n"
            "Automatic trading: OFF\n"
            "Signal mode: ON\n"
        )

        self.wfile.write(message.encode())

    def log_message(self, format, *args):
        return


def start_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)

    print(f"Health server listening on port {PORT}")

    server.serve_forever()


# ============================================================
# DATA STORAGE
# ============================================================

price_history = defaultdict(lambda: deque(maxlen=500))

last_price = {}
last_candle_minute = {}
last_signal_time = {}


# ============================================================
# INDICATORS
# ============================================================

def calculate_ema(values, period):

    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)

    ema = sum(values[:period]) / period

    for price in values[period:]:
        ema = (price - ema) * multiplier + ema

    return ema


def calculate_rsi(values, period=14):

    if len(values) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(1, len(values)):
        change = values[i] - values[i - 1]

        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    if len(gains) < period:
        return None

    average_gain = sum(gains[:period]) / period
    average_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        average_gain = (
            (average_gain * (period - 1)) + gains[i]
        ) / period

        average_loss = (
            (average_loss * (period - 1)) + losses[i]
        ) / period

    if average_loss == 0:
        return 100.0

    relative_strength = average_gain / average_loss

    return 100 - (100 / (1 + relative_strength))


# ============================================================
# SIGNAL ENGINE
# ============================================================

def generate_signal(asset_name):

    values = list(price_history[asset_name])

    if len(values) < MIN_CANDLES:
        return None

    ema9 = calculate_ema(values, EMA_FAST)
    ema21 = calculate_ema(values, EMA_SLOW)
    rsi = calculate_rsi(values, RSI_PERIOD)

    if ema9 is None or ema21 is None or rsi is None:
        return None

    price = values[-1]

    score = 0
    direction = None

    # --------------------------------------------------------
    # BUY CONDITIONS
    # --------------------------------------------------------

    if ema9 > ema21:
        score += 40

    if price > ema9:
        score += 20

    if rsi > 50:
        score += 20

    if rsi < 70:
        score += 20

    if score >= MIN_SCORE and ema9 > ema21 and rsi > 50:
        direction = "BUY"

    # --------------------------------------------------------
    # SELL CONDITIONS
    # --------------------------------------------------------

    sell_score = 0

    if ema9 < ema21:
        sell_score += 40

    if price < ema9:
        sell_score += 20

    if rsi < 50:
        sell_score += 20

    if rsi > 30:
        sell_score += 20

    if sell_score >= MIN_SCORE and ema9 < ema21 and rsi < 50:
        direction = "SELL"
        score = sell_score

    if direction is None:
        return None

    return {
        "direction": direction,
        "score": score,
        "price": price,
        "ema9": ema9,
        "ema21": ema21,
        "rsi": rsi,
    }


# ============================================================
# PRINT SIGNAL
# ============================================================

def print_signal(asset_name, signal):

    now = datetime.now(timezone.utc)

    signal_key = (
        asset_name,
        now.strftime("%Y-%m-%d %H:%M"),
    )

    if last_signal_time.get(asset_name) == signal_key:
        return

    last_signal_time[asset_name] = signal_key

    print("")
    print("=" * 58)
    print("🚨 LIVE POCKET OPTION OTC M1 SIGNAL 🚨")
    print("=" * 58)

    print(f"MARKET:     {asset_name}")
    print(f"SIGNAL:     {signal['direction']}")
    print(f"TIME UTC:   {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"PRICE:      {signal['price']:.6f}")
    print(f"EMA(9):     {signal['ema9']:.6f}")
    print(f"EMA(21):    {signal['ema21']:.6f}")
    print(f"RSI(14):    {signal['rsi']:.2f}")
    print(f"SCORE:      {signal['score']}%")
    print("SOURCE:     Pocket Option OTC")
    print("TIMEFRAME:  M1")
    print("TRADE:      OFF")
    print("=" * 58)
    print("")


# ============================================================
# PRICE PROCESSING
# ============================================================

def process_price(asset_name, price):

    try:
        price = float(price)
    except (TypeError, ValueError):
        return

    if not math.isfinite(price):
        return

    previous = last_price.get(asset_name)

    last_price[asset_name] = price

    # --------------------------------------------------------
    # Store price
    # --------------------------------------------------------

    price_history[asset_name].append(price)

    # --------------------------------------------------------
    # Detect a new M1 period
    # --------------------------------------------------------

    now = datetime.now(timezone.utc)

    candle_minute = now.replace(
        second=0,
        microsecond=0,
    )

    previous_minute = last_candle_minute.get(asset_name)

    if previous_minute == candle_minute:
        return

    last_candle_minute[asset_name] = candle_minute

    count = len(price_history[asset_name])

    print(
        f"[M1 DATA] {asset_name} | "
        f"price={price:.6f} | "
        f"candles={count} | "
        f"time={candle_minute.strftime('%H:%M:%S')} UTC"
    )

    # --------------------------------------------------------
    # Wait until enough data exists
    # --------------------------------------------------------

    if count < MIN_CANDLES:
        print(
            f"[DATA] {asset_name}: "
            f"collecting candles "
            f"{count}/{MIN_CANDLES}"
        )
        return

    # --------------------------------------------------------
    # Generate signal
    # --------------------------------------------------------

    signal = generate_signal(asset_name)

    if signal:
        print_signal(asset_name, signal)
    else:
        print(
            f"[NO SIGNAL] {asset_name} | "
            f"EMA/RSI conditions not aligned"
        )


# ============================================================
# EVENT DATA EXTRACTION
# ============================================================

def extract_price(item):

    if item is None:
        return None

    # --------------------------------------------------------
    # Pydantic model
    # --------------------------------------------------------

    if hasattr(item, "model_dump"):

        try:
            data = item.model_dump()

            return extract_price(data)

        except Exception:
            pass

    # --------------------------------------------------------
    # Dictionary
    # --------------------------------------------------------

    if isinstance(item, dict):

        possible_keys = [
            "close",
            "price",
            "value",
            "rate",
            "ask",
            "bid",
        ]

        for key in possible_keys:

            if key in item:

                value = item[key]

                try:
                    return float(value)
                except (TypeError, ValueError):
                    pass

        # Search nested dictionaries

        for value in item.values():

            result = extract_price(value)

            if result is not None:
                return result

    # --------------------------------------------------------
    # List / tuple
    # --------------------------------------------------------

    if isinstance(item, (list, tuple)):

        for value in item:

            result = extract_price(value)

            if result is not None:
                return result

    # --------------------------------------------------------
    # Numeric
    # --------------------------------------------------------

    if isinstance(item, (int, float)):

        if math.isfinite(float(item)):
            return float(item)

    return None


def extract_asset_name(item):

    if item is None:
        return None

    if hasattr(item, "model_dump"):

        try:
            return extract_asset_name(item.model_dump())
        except Exception:
            pass

    if isinstance(item, dict):

        for key in [
            "asset",
            "symbol",
            "name",
            "active",
            "ticker",
        ]:

            if key in item:

                value = item[key]

                if value is not None:
                    return str(value)

        for value in item.values():

            result = extract_asset_name(value)

            if result:
                return result

    if isinstance(item, (list, tuple)):

        for value in item:

            result = extract_asset_name(value)

            if result:
                return result

    return None


# ============================================================
# POCKET OPTION STREAM EVENT
# ============================================================

async def on_update_stream(assets):

    try:

        if assets is None:
            return

        if not isinstance(assets, (list, tuple)):
            assets = [assets]

        for item in assets:

            asset_name = extract_asset_name(item)
            price = extract_price(item)

            if not asset_name:
                continue

            asset_name = asset_name.replace("-", "_")

            # ------------------------------------------------
            # Only process our OTC markets
            # ------------------------------------------------

            allowed = {
                str(asset).split(".")[-1]
                for asset in OTC_MARKETS
            }

            if asset_name not in allowed:
                continue

            if price is None:
                continue

            process_price(
                asset_name,
                price,
            )

    except Exception as exc:

        logger.exception(
            "STREAM PROCESSING ERROR: %s",
            exc,
        )


# ============================================================
# CONNECTION EVENTS
# ============================================================

async def on_connect(_data):

    print("POCKET OPTION SOCKET CONNECTED")


async def on_success_auth(data):

    print("POCKET OPTION AUTHORIZATION SUCCESSFUL")

    print("SUBSCRIBING TO OTC MARKETS...")

    for asset in OTC_MARKETS:

        try:

            await client.emit.subscribe_to_asset(asset)

            print(
                f"SUBSCRIBED: {asset}"
            )

        except Exception as exc:

            print(
                f"SUBSCRIBE ERROR {asset}: {exc}"
            )


async def on_disconnect(_data):

    print("POCKET OPTION DISCONNECTED")


# ============================================================
# CLIENT
# ============================================================

client = PocketOptionClient(
    logger=True,
)


# ============================================================
# EVENT REGISTRATION
# ============================================================

client.on.connect(on_connect)

client.on.success_auth(on_success_auth)

client.on.disconnect(on_disconnect)

client.on.update_close_value(on_update_stream)


# ============================================================
# MAIN
# ============================================================

async def main():

    session = os.getenv("PO_SESSION")
    uid = os.getenv("PO_UID")

    if not session:
        print("ERROR: PO_SESSION is missing")
        return

    if not uid:
        print("ERROR: PO_UID is missing")
        return

    print("ACCOUNT MODE:", ACCOUNT_MODE)
    print("TIMEFRAME:", TIMEFRAME)
    print("SIGNAL ONLY")
    print("AUTOMATIC TRADING: OFF")

    print("PO_SESSION found")
    print("PO_UID found")

    authorization = AuthorizationData.model_validate(
        {
            "session": session,
            "isDemo": 0,
            "uid": int(uid),
            "platform": 2,
            "isFastHistory": True,
            "isOptimized": True,
        }
    )

    print("AUTHORIZATION DATA CREATED")

    print("Pocket Option client created")

    # --------------------------------------------------------
    # Initialize the official 0.4.0 client
    # --------------------------------------------------------

    default_init(
        client,
        authorization=authorization,
        sub_assets=OTC_MARKETS,
        sub_period=CANDLE_PERIOD,
    )

    print("M1 CANDLE STORAGE INITIALIZED")

    print(
        f"{len(OTC_MARKETS)} OTC MARKETS REGISTERED"
    )

    for asset in OTC_MARKETS:

        print(
            f"WATCHING: {asset}"
        )

    print("CONNECTING TO POCKET OPTION...")

    try:

        await client.connect(
            Regions.REAL
        )

    except AttributeError:

        # Compatibility fallback if the installed
        # SDK exposes the real region under another name.

        print(
            "Regions.REAL not available; "
            "trying United States South..."
        )

        await client.connect(
            Regions.UNITED_STATES_SOUTH
        )

    print("POCKET OPTION CONNECTION ACTIVE")

    print("")
    print("=" * 58)
    print("BOT READY")
    print("=" * 58)
    print("REAL ACCOUNT CONNECTION ACTIVE")
    print("8 OTC MARKETS SUBSCRIBED")
    print("M1 SIGNAL MONITORING ACTIVE")
    print("AUTOMATIC TRADING: OFF")
    print("WAITING FOR OTC MARKET DATA...")
    print("=" * 58)

    # --------------------------------------------------------
    # Keep Render service alive
    # --------------------------------------------------------

    while True:

        await asyncio.sleep(30)

        now = datetime.now(timezone.utc)

        print(
            f"BOT ALIVE: "
            f"{now.strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    health_thread = Thread(
        target=start_health_server,
        daemon=True,
    )

    health_thread.start()

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        print("BOT STOPPED")

    except Exception as exc:

        print("")
        print("FATAL BOT ERROR")
        print(exc)
        print("")

        raise
