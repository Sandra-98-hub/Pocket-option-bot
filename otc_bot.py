import os
import asyncio
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

from pocket_option import PocketOptionClient
from pocket_option.constants import Regions
from pocket_option.contrib.default_init import default_init
from pocket_option.models import Asset, AuthorizationData

PORT = int(os.getenv("PORT", "10000"))

# REAL ACCOUNT

IS_DEMO = 0

# M1 candles

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
Asset.USDCAD_otc,
]

class HealthHandler(BaseHTTPRequestHandler):

```
def do_GET(self):
    self.send_response(200)
    self.send_header("Content-Type", "text/plain")
    self.end_headers()
    self.wfile.write(
        b"Pocket Option OTC Signal Bot is running"
    )

def log_message(self, format, *args):
    pass
```

def start_health_server():

```
server = HTTPServer(
    ("0.0.0.0", PORT),
    HealthHandler
)

print(
    f"Health server listening on port {PORT}",
    flush=True
)

server.serve_forever()
```

def value_of(obj, name, default=None):

```
try:

    if isinstance(obj, dict):
        return obj.get(name, default)

    return getattr(obj, name, default)

except Exception:

    return default
```

def candle_market_name(market):

```
try:
    return market.value

except Exception:
    return str(market)
```

def print_candle(market, candle):

```
received = datetime.now(
    timezone.utc
).strftime(
    "%Y-%m-%d %H:%M:%S UTC"
)

candle_time = value_of(
    candle,
    "time"
)

open_price = value_of(
    candle,
    "open"
)

high_price = value_of(
    candle,
    "high"
)

low_price = value_of(
    candle,
    "low"
)

close_price = value_of(
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
    candle_market_name(market),
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
```

async def monitor_candles(client):

```
print(
    "M1 CANDLE MONITORING ACTIVE",
    flush=True
)

candles = getattr(
    client,
    "candles",
    None
)

if candles is None:

    print(
        "CANDLE STORAGE NOT AVAILABLE",
        flush=True
    )

    return

print(
    "CANDLE STORAGE READY:",
    type(candles).__name__,
    flush=True
)

last_seen = {}

while True:

    try:

        for market in OTC_MARKETS:

            result = None

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

            if isinstance(
                result,
                (list, tuple)
            ):

                candle_list = list(result)

            else:

                try:
                    candle_list = list(result)
                except Exception:
                    candle_list = [result]

            if not candle_list:
                continue

            latest = candle_list[-1]

            candle_time = value_of(
                latest,
                "time"
            )

            close_price = value_of(
                latest,
                "close"
            )

            key = (
                str(candle_time),
                str(close_price)
            )

            market_key = candle_market_name(
                market
            )

            if last_seen.get(
                market_key
            ) != key:

                last_seen[
                    market_key
                ] = key

                print_candle(
                    market,
                    latest
                )

        await asyncio.sleep(1)

    except asyncio.CancelledError:

        return

    except Exception as error:

        print(
            "CANDLE MONITOR ERROR:",
            type(error).__name__,
            str(error),
            flush=True
        )

        await asyncio.sleep(5)
```

async def main():

```
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

try:

    uid_number = int(uid)

except ValueError:

    print(
        "ERROR: PO_UID must be numeric",
        flush=True
    )

    return

try:

    client = PocketOptionClient(
        logger=False
    )

    print(
        "Pocket Option client created",
        flush=True
    )

except Exception as error:

    print(
        "CLIENT CREATION ERROR:",
        type(error).__name__,
        str(error),
        flush=True
    )

    return

try:

    authorization = AuthorizationData.model_validate(
        {
            "session": session,
            "isDemo": IS_DEMO,
            "uid": uid_number,
            "platform": 2,
            "isFastHistory": True,
            "isOptimized": True,
        }
    )

    print(
        "REAL authorization created",
        flush=True
    )

except Exception as error:

    print(
        "AUTHORIZATION ERROR:",
        type(error).__name__,
        str(error),
        flush=True
    )

    return

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

except Exception as error:

    print(
        "MARKET DATA INITIALIZATION ERROR:",
        type(error).__name__,
        str(error),
        flush=True
    )

    return

try:

    print(
        "Wildcard event listener installed",
        flush=True
    )

    client.on(
        "*",
        client.handle_new_event
    )

except Exception as error:

    print(
        "EVENT LISTENER ERROR:",
        type(error).__name__,
        str(error),
        flush=True
    )

print(
    "ABOUT TO CONNECT TO POCKET OPTION",
    flush=True
)

try:

    await client.connect(
        Regions.REAL
    )

except Exception as error:

    print(
        "CONNECTION ERROR:",
        type(error).__name__,
        str(error),
        flush=True
    )

    return

print(
    "CONNECT CALL FINISHED",
    flush=True
)

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

try:

    print(
        "ASSETS STORAGE READY:",
        type(client.assets).__name__,
        flush=True
    )

except Exception as error:

    print(
        "ASSET STORAGE ERROR:",
        type(error).__name__,
        str(error),
        flush=True
    )

try:

    print(
        "CANDLE STORAGE READY:",
        type(client.candles).__name__,
        flush=True
    )

except Exception as error:

    print(
        "CANDLE STORAGE ERROR:",
        type(error).__name__,
        str(error),
        flush=True
    )

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
        "OTC:",
        candle_market_name(market),
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

asyncio.create_task(
    monitor_candles(client)
)

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
```

if **name** == "**main**":

```
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

except Exception as error:

    print(
        "FATAL ERROR:",
        type(error).__name__,
        str(error),
        flush=True
    )
```
