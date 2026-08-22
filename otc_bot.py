from pocket_option import IsDemo

print("IsDemo type:")
print(IsDemo)

print("IsDemo values:")
try:
    print(list(IsDemo))
except Exception as e:
    print("Not an enum:", e)

print("DONE")
