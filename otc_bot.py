import os
import asyncio
from pocketoptionapi_async import AsyncPocketOptionClient

ASSET = "EURUSD_otc"
TIMEFRAME = 60
EMA_PERIOD = 9
RSI_PERIOD = 14


def calculate_ema(prices, period):
    multiplier = 2 / (period + 1)
    ema = prices[0]

    for price in prices[1:]:
        ema = ((price - ema) * multiplier) + ema

    return ema


def calculate_rsi(prices, period=14):
    if len(prices) <= period:
        return None

    gains = 0
    losses = 0

    for i in range(len(prices) - period, len(prices)):
        change = prices[i] - prices[i - 1]

        if change > 0:
            gains += change
        elif change < 0:
            losses += abs(change)

    if losses == 0:
        return 100.0

    rs = gains / losses
    return 100 - (100 / (1 + rs))


async def main():
    ssid = os.getenv("POCKET_OPTION_SSID")

    if not ssid:
        print("ERROR: POCKET_OPTION_SSID is not configured.")
        return

    print("Pocket Option OTC Signal Bot")
    print("============================")
    print("Asset: EUR/USD OTC")
    print("Timeframe: M1")
    print("Strategy: EMA 9 + RSI 14")
    print("Mode: SIGNAL ONLY")
    print("Connecting to Pocket Option...")

    client = AsyncPocketOptionClient(
        ssid=ssid,
        enable_logging=False
    )

    await client.connect()

    print("Connected to Pocket Option.")
    print("Receiving OTC candles...")

    while True:
        try:
            candles = await client.get_candles(
                asset=ASSET,
                timeframe=TIMEFRAME
            )

            if not candles:
                print("No OTC candles received.")
                await asyncio.sleep(10)
                continue

            closes = [float(c.close) for c in candles]

            if len(closes) < 30:
                print("Waiting for enough candles...")
                await asyncio.sleep(10)
                continue

            price = closes[-1]
            ema = calculate_ema(closes, EMA_PERIOD)
            rsi = calculate_rsi(closes, RSI_PERIOD)

            if rsi is None:
                print("Waiting for RSI data...")
                await asyncio.sleep(10)
                continue

            signal = "NO TRADE"

            if price > ema and rsi >= 55:
                signal = "BUY"
            elif price < ema and rsi <= 45:
                signal = "SELL"

            print("")
            print("================================")
            print("EUR/USD OTC M1")
            print(f"Price : {price:.5f}")
            print(f"EMA 9 : {ema:.5f}")
            print(f"RSI 14: {rsi:.2f}")
            print(f"SIGNAL: {signal}")
            print("================================")

            await asyncio.sleep(60)

        except Exception as e:
            print(f"Connection/data error: {e}")
            print("Retrying...")
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
