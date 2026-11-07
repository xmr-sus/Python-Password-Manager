from assets.authentication.login import login

key = login()

print("Key generated:", isinstance(key, bytes))
print("Key length:", len(key) if key else 0)