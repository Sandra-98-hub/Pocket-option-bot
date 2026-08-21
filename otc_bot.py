import inspect
from pocket_option import PocketOptionClient

print("POCKET OPTION PACKAGE OK")

client = PocketOptionClient()

print("CONNECT SIGNATURE:")
print(inspect.signature(client.connect))

print("CONNECT DOC:")
print(inspect.getdoc(client.connect))

print("DONE")
