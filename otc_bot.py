import os
import inspect

from pocket_option import PocketOptionClient

print("POCKET OPTION PACKAGE OK", flush=True)

client = PocketOptionClient()

print("AVAILABLE CLIENT METHODS", flush=True)

for name in dir(client):
    if not name.startswith("_"):
        try:
            value = getattr(client, name)

            if callable(value):
                try:
                    print(
                        name,
                        inspect.signature(value),
                        flush=True
                    )
                except Exception:
                    print(name, flush=True)

        except Exception:
            pass

print("DONE", flush=True)
