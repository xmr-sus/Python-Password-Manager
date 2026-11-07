import copy

from assets.authentication.encryption import encrypt_password
from assets.save_account import save_accounts


def migrate_accounts(accounts, encryption_key):
    # Work on a separate copy so the original remains unchanged
    migrated_accounts = copy.deepcopy(accounts)

    migrated = False

    for account in migrated_accounts:
        if isinstance(account["password"], str):
            account["password"] = encrypt_password(account["password"], encryption_key)
            migrated = True

    if migrated:
        if save_accounts(migrated_accounts):
            accounts[:] = migrated_accounts
            print("Account migration completed successfully!")
            return True
        else:
            print("Account migration failed. Original data preserved.")
            return False

    else:
        print("No accounts required migration.")
        return True

# Why copy.deepcopy()?
# A normal copy would still share the inner account dictionaries with the original list. A deep copy gives us independent dictionaries too.

# So now:
# 1. Migration happens on the copy.
# 2. The copy is saved.
# 3. Only after a successful save do we update the original list.
# 4. If saving fails, the original in-memory data stays unchanged.


# <--------------------------------------------- OLD CODE -------------------------------------------------->
# from assets.authentication.encryption import encrypt_password
# from assets.save_account import save_accounts

# def migrate_accounts(accounts, encryption_key):
#     migrated = False
#     for account in accounts:
#         if isinstance(account["password"], str):
#             account["password"] = encrypt_password(account["password"], encryption_key)
#             migrated = True

#     if migrated:
#         if save_accounts(accounts):
#             print("Account migration completed successfully!")
#         else:
#             print("Account migration failed. Please restore your backup.")
#     else:
#         print("No accounts required migration.")