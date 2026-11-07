from assets.save_account import save_accounts

def delete(accounts):
    if not accounts:
            print("No accounts available to update.")
            return

    """Delete an account by username and save the updated list."""
    print("Which account do you want to delete?")
    service = input("Enter the service/website name of the account you want to delete: ").strip()
    if not service:
        print("Website name cannot be empty.")
        return

    matching_accounts = []

    print(f"Finding all accounts with service/website name: {service}...")

    # Filter accounts
    for user in accounts:
        if service.lower() in user['website'].lower():
            matching_accounts.append(user)

     # Check whether any accounts matched
    if not matching_accounts:
        print("No account was found.")
        return

    # Display the matching accounts
    for index, account in enumerate(matching_accounts, start=1):
        print(f"{index}. {account['website']} ({account['username']})")

    try:
        account_number = int(input("Enter an account number you want to delete among given options."))
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

    # Remove the selected account
    for index, account in enumerate(accounts):
        if account['id'] == selected_id:
            deleted_account = accounts.pop(index)

            if save_accounts(accounts):
                print("Account deleted successfully!")
            else:
                # Restore the account at its original position
                accounts.insert(index, deleted_account)
                print("Deletion cancelled because saving failed.")
            return