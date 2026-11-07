import getpass as gp

from assets.authentication.hashing import hash_password
from assets.authentication.storage import save_master_hash
from assets.authentication.key_derivation import generate_salt, derive_key, generate_vault_key
from assets.authentication.key_wrapping import wrap_vault_key

def get_password():
    while True:
        print("Create a master password.")
        password = gp.getpass("Enter your master password: ")
        if not password:
            print("Password cannot be empty.")
            continue

        confirm = gp.getpass("Confirm the master password: ")
        if confirm != password:
            print("Password does not match. \nTry Again.")
            continue

        salt = generate_salt()

        password_hash = hash_password(password)

        kek = derive_key(password, salt)
        vault_key = generate_vault_key()
        wrapped_vault_key = wrap_vault_key(vault_key, kek)
        saving_succeed = save_master_hash(password_hash, salt, wrapped_vault_key)
        if not saving_succeed:
            raise OSError("Failed to save master password metadata.")
        return vault_key
# New setup:
# 1. Generate salt.
# 2. Hash master password.
# 3. Derive KEK.
# 4. Generate a random DEK.
# 5. Wrap DEK using KEK.
# 6. Save hash, salt and wrapped DEK.
# 7. Return the DEK.
# Notice that derive_key() now produces the KEK, not the key used to encrypt account passwords.

if __name__ == "__main__":
    get_password()

# Why? This tells Python to call get_password() when you execute setup.py directly as a module, but not when another module imports it.