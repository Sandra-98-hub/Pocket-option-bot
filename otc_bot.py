import asyncio
import os

from pocket_option import PocketOptionClient
from pocket_option.constants import Regions
from pocket_option.models import Asset

SSID = os.environ.get("POCKET_OPTION_SSID")

if not SSID:
    print("ERROR: POCKET_OPTION_SSID is not set")
    raise SystemExit(1)

client = PocketOptionClient(logger=True)


async def main():
    print("Pocket Option OTC Signal Bot")
    print("Connecting...")

    await client.connect(Regions.DEMO)

    print("Connected!")
    print("Market: EURUSD OTC")
    print("Timeframe: M1")
    print("Waiting for OTC candles...")

    await client.emit.subscribe_symbol(Asset.EURUSD_otc)

    while True:
        await asyncio.sleep(60)


asyncio.run(main())
