
from assets.authentication.encryption import encrypt_password, decrypt_password
from assets.authentication.key_derivation import generate_salt, derive_key
from cryptography.exceptions import InvalidTag

# Generate a temporary encryption key
salt = generate_salt()
encryption_key = derive_key("TestMasterPassword123", salt)

original_password = "MySecretPassword123!"

# ---------- Test Encryption ----------
encrypted_data = encrypt_password(original_password, encryption_key)

print("Encrypted data:", encrypted_data)

# ---------- Test Decryption ----------
decrypted_password = decrypt_password(encrypted_data, encryption_key)

print("Decrypted password:", decrypted_password)
print("Match:", original_password == decrypted_password)

# ---------- Test Wrong Key ----------
wrong_salt = generate_salt()
wrong_key = derive_key("WrongMasterPassword123", wrong_salt)

try:
    decrypt_password(encrypted_data, wrong_key)
except InvalidTag:
    print("Wrong key rejected successfully!")
