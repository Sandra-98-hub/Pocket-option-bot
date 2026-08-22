import inspect
from pocket_option import PocketOptionClient

print("POCKET OPTION PACKAGE OK")

print("\nCLIENT CONSTRUCTOR:")
print(inspect.signature(PocketOptionClient))

print("\nCLIENT MODULE:")
print(inspect.getmodule(PocketOptionClient))

print("\nDONE")
