import getpass as gp

from assets.authentication.hashing import verify_password
from assets.authentication.storage import load_master_hash


def legacy_login():
    master_hash = load_master_hash()

    if not master_hash:
        print("No master password found.")
        return False

    attempt = 5

    while attempt > 0:
        master_password = gp.getpass("Enter your master password: ")

        if verify_password(master_password, master_hash):
            print("Legacy authentication successful.")
            return master_password

        attempt -= 1
        print("Wrong Password.")
        print(f"{attempt} attempts remaining.")

        if attempt == 0:
            print("Too many failed attempts.")
            return False

# What makes this different from login.py?
# - login() verifies the password and unwraps the existing vault key.
# - legacy_login() verifies the password and returns the master password so the migration can derive the old encryption key.