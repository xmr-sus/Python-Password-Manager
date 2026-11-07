import secrets
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def wrap_vault_key(vault_key, kek):
    nonce = secrets.token_bytes(12)

    aes = AESGCM(kek)

    ciphertext = aes.encrypt(nonce, vault_key, None) # This encrypts the vault_key
    encrypted_key = base64.b64encode(ciphertext).decode("utf-8")
    encoded_nonce = base64.b64encode(nonce).decode("utf-8")

    return{
        "ciphertext": encrypted_key,
        "nonce": encoded_nonce
    }
def unwrap_vault_key(wrapped_key, kek):
    ciphertext = base64.b64decode(wrapped_key["ciphertext"])
    nonce = base64.b64decode(wrapped_key["nonce"])

    aes = AESGCM(kek)
    vault_key = aes.decrypt(nonce, ciphertext, None)

    return vault_key

# For details, open encryption.py