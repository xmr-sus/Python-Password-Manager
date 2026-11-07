import getpass as gp

from assets.is_duplicates import is_duplicate
from assets.save_account import save_accounts
from assets.authentication.encryption import encrypt_password

def update_account(accounts, encryption_key):
    if not accounts:
        print("No accounts available to update.")
        return
        
    website = input("Which account you want to update(Enter your website name): ").strip()
    if not website:
        print("Website name cannot be empty.")
        return

    matching_accounts = []
    print(f"Finding all accounts with service/website name: {website}...")

    # Filter accounts
    for user in accounts:
        if website.lower() in user['website'].lower():
            matching_accounts.append(user)

    # Check whether any accounts matched
    if not matching_accounts:
        print("No account was found.")
        return

    # Display the matching accounts
    for index, account in enumerate(matching_accounts, start=1):
        print(f"{index}. {account['website']} ({account['username']})")

    try:
        account_number = int(input("Enter the account number you want to update: "))
    except ValueError as error:
        print("Please enter a valid number.")
        print(error)
        return

    # Validate the selected number
    if account_number < 1 or account_number > len(matching_accounts):
        print("Please select a valid number.")
        return

    # Get the selected account
    selected_account = matching_accounts[account_number - 1] # "-1" bcz list indexing starts with 0 and enumerate operation starts with 1

    # Identify the exact account using its UUID
    selected_id = selected_account['id']

    original_account = selected_account.copy()

    for user in accounts:
        if user['id'] == selected_id:
            print("What information you want to change?")
            print("1. Change username")
            print("2. Change website/service name")
            print("3. Change password")
            try:
                new_Choice = int(input("Please choose one of the options: "))
            except ValueError:
                print("Please print a valid number of choice from above given choices.")
                print(error)
                return

            updated = False  # Track whether an actual change was made

            if new_Choice == 1:
                update_username = input("Enter the new username: ").strip()
                if len(update_username) != 0:
                    # Check for duplicate (ignore the current account)
                    if is_duplicate(accounts, update_username, user['website'], exclude_account=user):
                        print(f"Account with username '{update_username}' for '{user['website']}' already exists!")
                        print("Update cancelled.")
                        return
                    user['username'] = update_username
                    updated = True
                else:
                    print("Empty value not allowed. Update cancelled.")

            elif new_Choice == 2:
                update_website = input("Enter the new website/service name: ").strip()
                if len(update_website) != 0:
                    # Check for duplicate (ignore the current account)
                    if is_duplicate(accounts, user['username'], update_website, exclude_account=user):
                        print(f"Account with username '{user['username']}' for '{update_website}' already exists!")
                        print("Update cancelled.")
                        return
                    user['website'] = update_website
                    updated = True
                else:
                    print("Empty value not allowed. Update cancelled.")

            elif new_Choice == 3:
                update_password = gp.getpass("Enter the new password: ")
                if len(update_password) != 0:
                    user['password'] = encrypt_password(update_password, encryption_key)
                    updated = True
                else:
                    print("Empty value not allowed. Update cancelled.")

            else:
                print("Choose any one options from given above!")
                return

            if updated:
                if save_accounts(accounts):
                    print("Account updated successfully!")
                else:
                    selected_account.update(original_account)
                    print("Update cancelled because saving failed.")
            break

    else:
        print("Account not found!")