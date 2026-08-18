import asyncio
import logging
import os

from pocket_option import PocketOptionClient
from pocket_option.constants import Regions
from pocket_option.contrib.candles import MemoryCandleStorage
from pocket_option.models import (
    Asset,
    AuthorizationData,
    SuccessAuthEvent,
)


# ============================================================
# SETTINGS
# ============================================================

MARKETS = [
    Asset.AUDCAD_otc,
    Asset.AEDCNY_otc,
    Asset.AUDNZD_otc,
]

IS_DEMO = 1


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# CLIENT
# ============================================================

client = PocketOptionClient(logger=True)

candles = MemoryCandleStorage(client)

connected_event = asyncio.Event()
authorized_event = asyncio.Event()


# ============================================================
# CONNECT
# ============================================================

@client.on.connect
async def on_connect(data=None):

    print("")
    print("==========================================")
    print("CONNECTED TO POCKET OPTION WEBSOCKET")
    print("==========================================")

    session = os.getenv("PO_SESSION")
    uid = os.getenv("PO_UID")

    if not session:
        print("❌ PO_SESSION is missing")
        return

    if not uid:
        print("❌ PO_UID is missing")
        return

    print("PO_SESSION: FOUND")
    print("PO_UID: FOUND")

    try:

        auth_data = AuthorizationData.model_validate(
            {
                "session": session,
                "isDemo": IS_DEMO,
                "uid": int(uid),
                "platform": 2,
                "isFastHistory": True,
                "isOptimized": True,
            }
        )

        await client.emit.auth(auth_data)

        connected_event.set()

        print("Authentication request sent.")

    except Exception as error:

        print("")
        print("❌ AUTHENTICATION ERROR")
        print(type(error).__name__)
        print(str(error))


# ============================================================
# AUTHORIZED
# ============================================================

@client.on.success_auth
async def on_success_auth(data: SuccessAuthEvent):

    print("")
    print("==========================================")
    print("✅ POCKET OPTION AUTHENTICATED")
    print("==========================================")

    print("Account connection successful.")

    authorized_event.set()

    # Load required account/market information.
    try:
        await client.emit.indicator_load()
        await client.emit.favorite_load()
        await client.emit.price_alert_load()
    except Exception as error:
        print(
            "Market initialization warning:",
            str(error)
        )

    # Subscribe to OTC markets.
    for market in MARKETS:

        try:

            print("")
            print(
                f"Subscribing to OTC: {market}"
            )

            await client.emit.subscribe_to_asset(
                market
            )

            print(
                f"✅ Subscription requested: {market}"
            )

        except Exception as error:

            print(
                f"❌ Could not subscribe to {market}"
            )

            print(
                type(error).__name__,
                str(error)
            )


# ============================================================
# CANDLE EVENTS
# ============================================================

@client.on.candle_generated
async def on_candle(candle):

    print("")
    print("==========================================")
    print("📊 OTC CANDLE RECEIVED")
    print("==========================================")

    print(candle)


# ============================================================
# MAIN
# ============================================================

async def main():

    print("")
    print("==========================================")
    print("POCKET OPTION OTC TEST")
    print("==========================================")
    print("")

    print("Markets:")
    print("  AUD/CAD OTC")
    print("  AED/CNY OTC")
    print("  AUD/NZD OTC")

    print("")
    print("Checking environment variables...")

    if not os.getenv("PO_SESSION"):
        print("❌ PO_SESSION is missing")
        return

    if not os.getenv("PO_UID"):
        print("❌ PO_UID is missing")
        return

    print("✅ PO_SESSION found")
    print("✅ PO_UID found")

    print("")
    print("Starting Pocket Option client...")

    try:

        await client.connect(
            Regions.DEMO
        )

        print("Connection process started.")

        # Keep service alive.
        while True:

            await asyncio.sleep(10)

    except asyncio.CancelledError:

        print("Bot stopped.")

    except Exception as error:

        print("")
        print("==========================================")
        print("❌ POCKET OPTION ERROR")
        print("==========================================")

        print(
            type(error).__name__
        )

        print(
            str(error)
        )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("Stopped.")
