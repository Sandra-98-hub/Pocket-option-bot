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
# STRATEGY
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

logger = logging.getLogger("POCKET_OPTION_OTC")


# ============================================================
# HEALTH SERVER
# ============================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

        self.wfile.write(
            b"Pocket Option OTC M1 Signal Bot is running"
        )

    def log_message(self, format, *args):
        return


def start_health_server():

    server = HTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler,
    )

    print(
        f"Health server listening on port {PORT}"
    )

    server.serve_forever()


# ============================================================
# DATA STORAGE
# ============================================================

price_history = defaultdict(
    lambda: deque(maxlen=500)
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


# ============================================================
# INDICATORS
# ============================================================

def ema(values, period):

    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)

    result = sum(values[:period]) / period

    for value in values[period:]:
        result = (
            (value - result) * multiplier
            + result
        )

    return result


def rsi(values, period=14):

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

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):

        avg_gain = (
            (avg_gain * (period - 1))
            + gains[i]
        ) / period

        avg_loss = (
            (avg_loss * (period - 1))
            + losses[i]
        ) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


# ============================================================
# SIGNAL
# ============================================================

def calculate_signal(asset_name):

    values = list(
        price_history[asset_name]
    )

    if len(values) < MIN_PRICES:
        return None

    current_price = values[-1]

    fast_ema = ema(
        values,
        EMA_FAST,
    )

    slow_ema = ema(
        values,
        EMA_SLOW,
    )

    current_rsi = rsi(
        values,
        RSI_PERIOD,
    )

    if (
        fast_ema is None
        or slow_ema is None
        or current_rsi is None
    ):
        return None

    # --------------------------------------------------------
    # BUY
    # --------------------------------------------------------

    buy_score = 0

    if fast_ema > slow_ema:
        buy_score += 40

    if current_price > fast_ema:
        buy_score += 20

    if current_rsi > 50:
        buy_score += 20

    if current_rsi < 70:
        buy_score += 20

    if (
        buy_score >= MIN_SCORE
        and fast_ema > slow_ema
        and current_rsi > 50
    ):

        return {
            "direction": "BUY",
            "score": buy_score,
            "price": current_price,
            "ema9": fast_ema,
            "ema21": slow_ema,
            "rsi": current_rsi,
        }

    # --------------------------------------------------------
    # SELL
    # --------------------------------------------------------

    sell_score = 0

    if fast_ema < slow_ema:
        sell_score += 40

    if current_price < fast_ema:
        sell_score += 20

    if current_rsi < 50:
        sell_score += 20

    if current_rsi > 30:
        sell_score += 20

    if (
        sell_score >= MIN_SCORE
        and fast_ema < slow_ema
        and current_rsi < 50
    ):

        return {
            "direction": "SELL",
            "score": sell_score,
            "price": current_price,
            "ema9": fast_ema,
            "ema21": slow_ema,
            "rsi": current_rsi,
        }

    return None


# ============================================================
# PRINT SIGNAL
# ============================================================

def print_signal(asset_name, signal):

    now = datetime.now(timezone.utc)

    minute_key = now.strftime(
        "%Y-%m-%d %H:%M"
    )

    if (
        last_signal_minute.get(asset_name)
        == minute_key
    ):
        return

    last_signal_minute[asset_name] = minute_key

    print("")
    print("=" * 60)
    print("🚨 LIVE POCKET OPTION OTC M1 SIGNAL 🚨")
    print("=" * 60)

    print(
        f"MARKET:     {asset_name}"
    )

    print(
        f"SIGNAL:     {signal['direction']}"
    )

    print(
        f"TIME UTC:   "
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

    print("SOURCE:     Pocket Option OTC")
    print("TIMEFRAME:  M1")
    print("TRADE:      OFF")

    print("=" * 60)
    print("")


# ============================================================
# PROCESS PRICE
# ============================================================

def process_price(asset_name, price):

    try:
        price = float(price)
    except (
        TypeError,
        ValueError,
    ):
        return

    if price <= 0:
        return

    last_price[asset_name] = price

    price_history[asset_name].append(price)

    now = datetime.now(timezone.utc)

    current_minute = now.replace(
        second=0,
        microsecond=0,
    )

    previous_minute = last_minute.get(
        asset_name
    )

    if previous_minute == current_minute:
        return

    last_minute[asset_name] = current_minute

    count = len(
        price_history[asset_name]
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
            f"[DATA] {asset_name}: "
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
            signal,
        )

    else:

        print(
            f"[NO SIGNAL] "
            f"{asset_name} | "
            f"EMA/RSI not aligned"
        )


# ============================================================
# REAL-TIME MARKET EVENT
# ============================================================

@client_event_placeholder
async def unused_placeholder():
    pass
