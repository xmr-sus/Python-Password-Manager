import getpass as gp
import binascii
from cryptography.exceptions import InvalidTag

from assets.authentication.hashing import verify_password
from assets.authentication.storage import load_master_hash, load_kek_salt, load_wrapped_vault_key
from assets.authentication.key_derivation import derive_key
from assets.authentication.key_wrapping import unwrap_vault_key

def login():
    master_hash = load_master_hash()

    if not master_hash:
        print("No master password yet. Please set up a master password.")
        return

    attempt = 5
    while attempt > 0:
        get_pass = gp.getpass("Enter your master password: ")
    
        verify = verify_password(get_pass, master_hash)

        if verify:
            kek_salt = load_kek_salt()
            wrapped_vault_key = load_wrapped_vault_key()

            if not kek_salt or not wrapped_vault_key:
                print("Required encryption metadata is missing. Cannot continue.")
                return False
            try:
                kek = derive_key(get_pass, kek_salt)
                vault_key = unwrap_vault_key(wrapped_vault_key, kek)

                print("Login Succeeded.")
                return vault_key
            except (InvalidTag, KeyError, ValueError, TypeError, binascii.Error):
                print("Unable to recover vault key. Master metadata may be corrupted.")
                return False
        else:
            print("Wrong Password.")
            attempt -= 1
            print(f"{attempt} attempts remaining.")
            if attempt == 0:
                print("Too many failed attempts.")
                return False