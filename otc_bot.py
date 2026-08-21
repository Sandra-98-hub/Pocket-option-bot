import os
from pocket_option import PocketOptionClient

print("POCKET OPTION PACKAGE OK")

session = os.getenv("PO_SESSION")

if not session:
    print("ERROR: PO_SESSION is missing")
    raise SystemExit(1)

print("PO_SESSION found")

client = PocketOptionClient()

print("Pocket Option client created")
print("Available client methods:")

for name in dir(client):
    if not name.startswith("_"):
        print(name)

print("END OF CLIENT METHODS")
