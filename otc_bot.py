import inspect
from pocket_option import PocketOptionClient

client = PocketOptionClient

print("POCKET OPTION 0.4.0")
print("===================")

print("CANDLES:")
print(client.candles)

try:
    print("CANDLES SIGNATURE:")
    print(inspect.signature(client.candles))
except Exception as e:
    print("NO SIGNATURE:", e)

print("===================")
print("ASSETS:")
print(client.assets)

try:
    print("ASSETS SIGNATURE:")
    print(inspect.signature(client.assets))
except Exception as e:
    print("NO SIGNATURE:", e)

print("===================")
