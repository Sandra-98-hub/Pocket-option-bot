import pocket_option

print("PACKAGE LOCATION:")
print(pocket_option.__file__)

print("\nPACKAGE CONSTANTS:")

try:
    from pocket_option import constants

    for name in dir(constants):
        if not name.startswith("_"):
            value = getattr(constants, name)

            if isinstance(value, (str, int, float, bool)):
                print(name, "=", value)

except Exception as e:
    print("ERROR:", type(e).__name__, str(e))

print("\nDONE")
