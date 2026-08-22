from pocket_option import AuthorizationData

print("AUTHORIZATION MODEL")

for name, field in AuthorizationData.model_fields.items():
    print(name, "->", field.annotation)

print("DONE")
