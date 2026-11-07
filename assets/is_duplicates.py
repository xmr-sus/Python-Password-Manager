def is_duplicate(accounts, username, website, exclude_account=None):
    """
    Check if an account with the same username AND website already exists.
    If exclude_account is given, that account is ignored (useful when updating).
    """
    for account in accounts:
        # Skip the account we are currently updating
        if account is exclude_account:
            continue

        if (account["username"].lower() == username.lower() and 
            account["website"].lower() == website.lower()):
            return True
    return False