import inspect
from pocket_option import PocketOptionClient, AuthorizationData

print("POCKET OPTION PACKAGE OK")

print("AUTHORIZATION DATA:")
print(AuthorizationData)

print("\nAUTHORIZATION SIGNATURE:")
try:
    print(inspect.signature(AuthorizationData))
except Exception as e:
    print("Could not read signature:", e)

print("\nAUTHORIZATION FIELDS:")
try:
    print(AuthorizationData.model_fields)
except Exception as e:
    print("Could not read fields:", e)

print("\nDONE")
