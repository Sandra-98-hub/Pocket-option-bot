import inspect
from pocket_option import PocketOptionClient

print("CLIENT SOURCE")
print(inspect.getsource(PocketOptionClient.__init__))

print("\nMODULE ATTRIBUTES")
import pocket_option.client as client_module

for name in dir(client_module):
    if not name.startswith("_"):
        value = getattr(client_module, name)
        if isinstance(value, str):
            print(name, "=", value)

print("\nDONE")
