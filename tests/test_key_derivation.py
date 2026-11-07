from assets.authentication.key_derivation import generate_salt, derive_key

password = "MyMasterPassword123"

# Generate one salt
salt1 = generate_salt()

# Derive keys using the same password and salt
key1 = derive_key(password, salt1)
key2 = derive_key(password, salt1)

# Generate a different salt
salt2 = generate_salt()

# Derive another key
key3 = derive_key(password, salt2)

print("Key 1:", key1.hex())
print("Key 2:", key2.hex())
print("Key 3:", key3.hex())

print("Same password + same salt:", key1 == key2)
print("Same password + different salt:", key1 != key3)
print("Key length:", len(key1), "bytes")