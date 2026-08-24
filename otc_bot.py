import os
import asyncio
import logging
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from pocket_option import PocketOptionClient
from pocket_option.constants import Regions
from pocket_option.contrib.default_init import default_init
from pocket_option.models import Asset, AuthorizationData

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

CANDLE_PERIOD = 60

logging.basicConfig(
level=logging.INFO,
format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(**name**)

class HealthHandler(BaseHTTPRequestHandler):
def do_GET(self):
self.send_response(200)
self.send_header("Content-Type", "text/plain")
self.end_headers()
self.wfile.write(b"Pocket Option OTC bot running")

```
def log_message(self, format, *args):
    return
```

def start_health_server():
server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
print(f"Health server listening on port {PORT}")
server.serve_forever()

def convert_assets():
assets = []

```
for name in OTC_MARKETS:
    try:
        asset = getattr(Asset, name)
        assets.append(asset)
    except AttributeError:
        print(f"WARNING: Asset not found: {name}")

return assets
```

async def main():
print("==========================================")
print("POCKET OPTION REAL OTC SIGNAL BOT")
print("==========================================")
print("ACCOUNT MODE: REAL")
print("TIMEFRAME: M1")
print("OTC MARKETS:", len(OTC_MARKETS))
print("SIGNAL MODE: SIGNAL ONLY")
print("AUTOMATIC TRADING: OFF")
print("")
print("MARKETS:")

```
for market in OTC_MARKETS:
    print(" -", market)

print("")
print("Starting Pocket Option connection...")

po_session = os.getenv("PO_SESSION")
po_uid = os.getenv("PO_UID")

if not po_session:
    print("ERROR: PO_SESSION is missing")
    return

if not po_uid:
    print("ERROR: PO_UID is missing")
    return

try:
    uid = int(po_uid)
except ValueError:
    print("ERROR: PO_UID must be numeric")
    return

print("PO_SESSION found")
print("PO_UID found")

client = PocketOptionClient(
    logger=True
)

print("Pocket Option client created")

authorization = AuthorizationData.model_validate(
    {
        "session": po_session,
        "isDemo": 0,
        "uid": uid,
        "platform": 2,
        "isFastHistory": True,
        "isOptimized": True,
    }
)

print("REAL authorization created")

assets = convert_assets()

if not assets:
    print("ERROR: No OTC assets were found")
    return

print("")
print("==========================================")
print("INITIALIZING OTC MARKET DATA")
print("==========================================")

try:
    default_init(
        client,
        authorization=authorization,
        sub_assets=assets,
        sub_period=CANDLE_PERIOD,
    )
except Exception as e:
    print("MARKET DATA INITIALIZATION ERROR:", repr(e))
    return

print("Market data initialization complete")
print("M1 period:", CANDLE_PERIOD, "seconds")
print(len(assets), "OTC subscriptions requested")

@client.on.update_close_value
async def on_update_close_value(data):
    print("")
    print("==========================================")
    print("OTC MARKET UPDATE RECEIVED")
    print("==========================================")
    print("UTC:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
    print("DATA:", data)
    print("==========================================")

@client.on.update_history_new_fast
async def on_update_history_new_fast(data):
    print("")
    print("M1 HISTORY UPDATE RECEIVED")
    print(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"))
    print(data)

@client.on.success_auth
async def on_success_auth(data):
    print("")
    print("==========================================")
    print("POCKET OPTION AUTHORIZATION SUCCESS")
    print("==========================================")
    print("REAL ACCOUNT AUTHORIZED")
    print(data)

print("")
print("ABOUT TO CONNECT TO POCKET OPTION")

try:
    await client.connect(
        Regions.EUROPE
    )
except Exception as e:
    print("CONNECT ERROR:", repr(e))
    return

print("CONNECT CALL FINISHED")

try:
    print("SOCKET CONNECTED:", client.sio.connected)
except Exception:
    print("SOCKET CONNECTED: UNKNOWN")

print("REAL MODE: TRUE")

try:
    await client.wait_for_authorization(timeout=20)
    print("AUTHORIZATION READY")
except Exception as e:
    print("AUTHORIZATION WAIT RESULT:", repr(e))

print("")
print("==========================================")
print("REAL ACCOUNT CONNECTION READY")
print(len(assets), "OTC MARKETS SUBSCRIBED")
print("M1 CANDLE MONITORING ACTIVE")
print("NO AUTOMATIC TRADES")
print("WAITING FOR OTC MARKET EVENTS...")
print("==========================================")

while True:
    now = datetime.now(timezone.utc)

    print(
        "BOT ALIVE:",
        now.strftime("%Y-%m-%d %H:%M:%S UTC")
    )

    await asyncio.sleep(30)
```

def run():
health_thread = Thread(
target=start_health_server,
daemon=True,
)

```
health_thread.start()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("BOT STOPPED")
```

if **name** == "**main**":
run()
