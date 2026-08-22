import pocket_option
from pocket_option import IsDemo

print("PACKAGE:", pocket_option.__file__)

print("ISDEMO:")
print(IsDemo)

print("ISDEMO TYPE:")
try:
    print(IsDemo.__value__)
except Exception as e:
    print(e)

print("DONE")
