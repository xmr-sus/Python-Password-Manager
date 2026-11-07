import secrets
from argon2.low_level import Type, hash_secret_raw

def generate_salt():
    return secrets.token_bytes(16)

def derive_key(password, salt):
    return hash_secret_raw(password.encode(), salt, 3, 65536, 4, 32, Type.ID) # ChatGPT...

def generate_vault_key():
    return secrets.token_bytes(32)
