import inspect
from pocket_option import PocketOptionClient

print("POCKET OPTION 0.4.0 API CHECK")
print("================================")

print("CLIENT METHODS:")

for name in dir(PocketOptionClient):
    if not name.startswith("_"):
        try:
            obj = getattr(PocketOptionClient, name)

            if callable(obj):
                try:
                    print(name, inspect.signature(obj))
                except Exception:
                    print(name)
            else:
                print(name)

        except Exception:
            pass

print("================================")
print("LOOKING FOR CANDLE / MARKET METHODS")
print("================================")

for name in dir(PocketOptionClient):
    if any(x in name.lower() for x in [
        "candle",
        "market",
        "asset",
        "subscribe",
        "history",
        "quote"
    ]):
        print(name)

print("================================")
print("API CHECK COMPLETE")
print("================================")
