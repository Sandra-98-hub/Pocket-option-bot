import os
from pocket_option import PocketOptionClient

print("POCKET OPTION PACKAGE OK")

session = os.getenv("PO_SESSION")

if not session:
    print("ERROR: PO_SESSION is missing")
    raise SystemExit(1)

print("PO_SESSION found")
print("Creating Pocket Option client...")

client = PocketOptionClient()

print("Pocket Option client created")
print("Testing live connection...")
