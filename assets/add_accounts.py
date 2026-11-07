import uuid
import getpass as gp

from assets.is_duplicates import is_duplicate
from assets.save_account import save_accounts
from assets.authentication.encryption import encrypt_password

def add_account(accounts, encryption_key):
    """Add a new account (username, website, password) to the list and save it."""
    try:
        # Get username and validate minimum length
        username = input("Enter the username: ").strip()

        if(len(username) < 3 or len(username) == 0):
            print("Username can't be less than 3!")
            return

        # Get the remaining details
        website = input("Enter your Service/Website name: ").strip()

        # ---------- Duplicate Detection ----------
        if is_duplicate(accounts, username, website):
            print(f"Account with username '{username}' for '{website}' already exists!")
            print("Duplicate entry not allowed.")
            return
        # ----------------------------------------

        password = gp.getpass("Enter the password: ")
        encrypted_data = encrypt_password(password, encryption_key)

        # Get a unique ID
        account_id = str(uuid.uuid4())

        # Create a dictionary for the new account
        details = {
            "id" : account_id,
            "username" : username,
            "website" : website,
            "password": encrypted_data
        }

        # Add to the list and persist to file
        accounts.append(details)
        if not save_accounts(accounts):
            accounts.pop()
            print("Account was not added because saving failed.")
        # Why accounts.pop()? 
        # It removes the account we just appended, keeping the in-memory list consistent with the file on disk.
        
    except OSError as error:
        print("File error:", error)