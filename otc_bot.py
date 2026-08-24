
import inspect
from pocket_option import PocketOptionClient

print("==========================================")
print("POCKET OPTION 0.4.0 CONSTRUCTOR CHECK")
print("==========================================")

print("CONSTRUCTOR:")
print(inspect.signature(PocketOptionClient))

print("")
print("CLASS MEMBERS:")

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

print("")
print("==========================================")
print("CHECK COMPLETE")
print("==========================================")
