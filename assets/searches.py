import binascii

from assets.authentication.encryption import decrypt_password
from cryptography.exceptions import InvalidTag

def search(accounts, encryption_key):
    """Search for an account by website/service name and print it if found."""
    website = input("Enter your service/website name: ").strip()
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
        account_number = int(input("Enter the account number you want to view: "))
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

    print("\nAccount Details:")
    print(f"Username: {selected_account['username']}")
    print(f"Website: {selected_account['website']}")

    reveal = input("Do you want to reveal the password? (y/n): ").lower()

    if reveal == "y":
        encrypted_data = selected_account["password"]
        
        if not isinstance(encrypted_data, dict):
            print("This account has not been encrypted yet.")
            return
        try:
            decrypted_password = decrypt_password(encrypted_data, encryption_key)
            print(f"Password: {decrypted_password}")
        except (InvalidTag, KeyError, ValueError, TypeError, binascii.Error):
            print("Unable to decrypt password. The encrypted data may be invalid or corrupted.")
    elif reveal == "n":
        print("Password remains hidden.")
    else:
        print("Invalid choice.")