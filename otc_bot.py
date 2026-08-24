import inspect
from pocket_option import PocketOptionClient

print("POCKET OPTION 0.4.0 AUTH CHECK")
print("================================")

print("CLIENT CONSTRUCTOR:")
print(inspect.signature(PocketOptionClient))

print("")
print("CONNECT:")
print(inspect.signature(PocketOptionClient.connect))

print("")
print("AUTH PARSER:")
print(inspect.signature(PocketOptionClient.get_auth_from_packet))

print("")
print("CLIENT MODULE:")
print(PocketOptionClient.**module**)

print("")
print("CLIENT FILE:")
print(inspect.getfile(PocketOptionClient))

print("")
print("DONE")
