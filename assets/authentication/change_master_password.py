import getpass as gp
import binascii
from cryptography.exceptions import InvalidTag

from assets.authentication.hashing import hash_password, verify_password
from assets.authentication.storage import load_master_hash, load_kek_salt, load_wrapped_vault_key, save_master_hash
from assets.authentication.key_derivation import generate_salt, derive_key
from assets.authentication.key_wrapping import unwrap_vault_key, wrap_vault_key


def change_master_password():

    # ---------- Verify current master password ----------

    master_hash = load_master_hash()

    if not master_hash:
        print("Unable to load master password metadata.")
        return False

    current_password = gp.getpass("Enter your current master password: ")

    if not verify_password(current_password, master_hash):
        print("Incorrect master password.")
        return False

    # ---------- Recover existing vault key ----------

    kek_salt = load_kek_salt()
    wrapped_vault_key = load_wrapped_vault_key()

    if not kek_salt or not wrapped_vault_key:
        print("Required encryption metadata is missing.")
        return False

    try:
        old_kek = derive_key(current_password, kek_salt)
        vault_key = unwrap_vault_key(wrapped_vault_key, old_kek)

    except (InvalidTag, KeyError, ValueError, TypeError, binascii.Error):
        print("Unable to recover vault key.")
        return False

    # ---------- Get new master password ----------

    while True:
        new_password = gp.getpass("Enter your new master password: ")

        if not new_password:
            print("Password cannot be empty.")
            continue

        if new_password == current_password:
            print("New password must be different from the current password.")
            continue

        confirm_password = gp.getpass("Confirm your new master password: ")

        if new_password != confirm_password:
            print("Passwords do not match. Try again.")
            continue

        break

    # ---------- Generate new encryption metadata ----------

    try:
        new_salt = generate_salt()
        new_hash = hash_password(new_password)

        new_kek = derive_key(new_password, new_salt)

        # Re-wrap the SAME vault key.
        new_wrapped_vault_key = wrap_vault_key(vault_key, new_kek)

        # ---------- Save updated master metadata ----------

        if not save_master_hash(new_hash, new_salt, new_wrapped_vault_key):
            print("Master password change failed. Existing metadata preserved.")
            return False

        print("Master password changed successfully!")
        return True

    except (OSError, ValueError, TypeError):
        print("Unable to change master password.")
        return False
