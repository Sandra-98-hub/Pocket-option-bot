import inspect
from pocket_option import PocketOptionClient
from pocket_option import AuthorizationData

print("CLIENT CONNECT SOURCE")
print(inspect.getsource(PocketOptionClient.connect))

print("\nAUTHORIZATION SOURCE")
print(inspect.getsource(AuthorizationData))

print("\nDONE")
