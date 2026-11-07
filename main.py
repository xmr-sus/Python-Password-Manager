import os
import json
import sys
import uuid

from assets.config import MASTER_FILE
from assets.config import FILE_NAME
from assets.authentication.setup import get_password
from assets.authentication.login import login
from assets.add_accounts import add_account
from assets.account_ids import assign_missing_ids
from assets.deletes import delete
from assets.searches import search
from assets.update_accounts import update_account
from assets.save_account import save_accounts
from assets.migrate_accounts import migrate_accounts
from assets.authentication.storage import get_vault_format
from assets.authentication.legacy_login import legacy_login
from assets.authentication.envelope_migration import recover_interrupted_migration, migrate_to_envelope_encryption
from assets.authentication.change_master_password import change_master_password


# Global list that stores all account details in memory
list_of_accounts = []

# Recover the vault if a previous migration was interrupted.
if not recover_interrupted_migration():
    print("Vault recovery failed. Exiting program.")
    sys.exit()

# # ---------- Authenticate user before loading accounts ----------
# if os.path.exists(MASTER_FILE):
#     vault_key = login()
# else:
#     vault_key = get_password()

# if not vault_key:
#     print("Authentication failed. Exiting program.")
#     sys.exit()

# print("Authentication completed.")


def valid_account_ids(accounts):
    if not isinstance(accounts, list):
        return False

    account_ids = []

    for account in accounts:
        if not isinstance(account, dict):
            return False

        # Allow missing IDs because assign_missing_ids() handles them.
        if "id" not in account:
            continue

        account_id = account["id"]

        try:
            uuid.UUID(account_id)
        except (ValueError, TypeError, AttributeError):
            return False

        account_ids.append(account_id)

    # Check that all existing IDs are unique.
    return len(account_ids) == len(set(account_ids))

# ---------- Identify vault format and authenticate user ----------

vault_format = get_vault_format()
legacy_master_password = None
vault_key = None

if vault_format == "new":
    vault_key = get_password()

elif vault_format == "legacy":
    legacy_master_password = legacy_login()

elif vault_format == "envelope":
    vault_key = login()

else:
    print("Invalid or unrecognized vault metadata. Exiting program.")
    sys.exit()

if vault_format == "legacy" and not legacy_master_password:
    print("Authentication failed. Exiting program.")
    sys.exit()

if vault_format != "legacy" and not vault_key:
    print("Authentication failed. Exiting program.")
    sys.exit()

# ---------- Load existing accounts when the program starts ----------

if os.path.exists(FILE_NAME):
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as userDetails:
            list_of_accounts = json.load(userDetails)

        if (
            isinstance(list_of_accounts, list)
            and valid_account_ids(list_of_accounts)
            and all(
                isinstance(account, dict)

                and "username" in account
                and isinstance(account["username"], str)
                and bool(account["username"].strip())

                and "website" in account
                and isinstance(account["website"], str)
                and bool(account["website"].strip())

                and "password" in account
                and (
                    (
                        isinstance(account["password"], str)
                        and bool(account["password"])
                    )
                    or
                    (
                        isinstance(account["password"], dict)
                        and isinstance(account["password"].get("ciphertext"), str)
                        and bool(account["password"]["ciphertext"])
                        and isinstance(account["password"].get("nonce"), str)
                        and bool(account["password"]["nonce"])
                    )
                )

                for account in list_of_accounts
            )
        ):
            print(f"Loaded {len(list_of_accounts)} saved account(s).")

        else:
            print("Please restore your accounts file from a backup.")
            sys.exit()
            # print("Invalid data format in the saved file. Starting with an empty list.")
            # list_of_accounts = []

    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        print("Please restore your accounts file from a backup.")
        sys.exit()
        # print("Couldn't load saved User Details. Starting with an empty list.")
        # list_of_accounts = []

else:
    list_of_accounts = []

# ---------- Migrate legacy vault to envelope encryption ----------

if vault_format == "legacy":
    vault_key = migrate_to_envelope_encryption(list_of_accounts, legacy_master_password)

    if not vault_key:
        print("Envelope migration failed. Exiting program.")
        sys.exit()

    print("Vault successfully upgraded to envelope encryption.")

# Assign IDs to accounts missing them
result = assign_missing_ids(list_of_accounts)

if result:
    if not save_accounts(list_of_accounts):
        print("Unable to save generated account IDs. Exiting.")
        sys.exit()

# Migrate any remaining plaintext passwords.
if not migrate_accounts(list_of_accounts, vault_key):
    print("Password migration failed. Exiting program.")
    sys.exit()

# ---------- Main menu loop ----------
while True:
    print("\n====== USER DETAILS ======")
    print("1. Add account")
    print("2. View saved accounts")
    print("3. Search for an account")
    print("4. Delete an account")
    print("5. Update an account")
    print("6. Change master password")
    print("7. Exit")

    try:
        choice = int(input("Enter your choice: "))

    except ValueError as error:
        print("Please print a valid number of choice from above given choices.")
        print(error)
        continue

    if choice == 1:
        # Add a new account
        add_account(list_of_accounts, vault_key)

    elif choice == 2:
        # Display all saved accounts (password is intentionally hidden)

        if(len(list_of_accounts) == 0):
            print("No accounts recorded yet.")

        else:

            for details in list_of_accounts:
                print(f"\nUsername: {details['username']}")
                print(f"\nWebsite/Service: {details['website']}")
                # print(f"\nPassword: {details['password']}")

    elif choice == 3:
        # Search by website/service name
        search(list_of_accounts, vault_key)

    elif choice == 4:
        # Delete an account by username
        delete(list_of_accounts)

    elif choice == 5:
        # Update an existing account
        update_account(list_of_accounts, vault_key)

    elif choice == 6:
        change_master_password()
        
    elif choice == 7:
        # Exit the program
        print("Exiting Password Manager. GoodBye!")
        break

    else:
        print("Choose anyone number of options from given choices.")