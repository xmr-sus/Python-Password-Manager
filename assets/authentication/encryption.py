from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import secrets
import base64

def encrypt_password(password, encryption_key):
    nonce = secrets.token_bytes(12)

    aes = AESGCM(encryption_key)

    # ChatGPT...
    ciphertext = aes.encrypt(nonce, password.encode(), None) # This encrypts the password
    encrypted_password = base64.b64encode(ciphertext).decode("utf-8") #
    encoded_nonce = base64.b64encode(nonce).decode("utf-8")

    # b64encode() converts bytes into Base64 bytes.
    # .decode("utf-8") converts those bytes into a normal Python string.
    # Both strings can now be stored in JSON.

    return {
        "ciphertext": encrypted_password,
        "nonce": encoded_nonce
    }

def decrypt_password(encrypted_data, encryption_key):
    # - encrypted_data["ciphertext"] retrieves the Base64 ciphertext.
    # - b64decode() converts it back into bytes.
    # - We do the same for the nonce.
    ciphertext = base64.b64decode(encrypted_data["ciphertext"])
    nonce = base64.b64decode(encrypted_data["nonce"])
    # This reverses the Base64 encoding we performed during encryption.

    aes = AESGCM(encryption_key)
    password = aes.decrypt(nonce, ciphertext, None) # Decrypt the ciphertext

    return password.decode("utf-8")
    # Encryption uses password.encode() to convert text into bytes.
    # Decryption gives us bytes back.
    # .decode("utf-8") converts those bytes into the original readable password.
