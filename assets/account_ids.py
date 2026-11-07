import uuid

def assign_missing_ids(accounts):
    update = False

    for account in accounts:

        # Check whether each account contains an id
        if "id" in account:
            continue

        account_id = str(uuid.uuid4()) # Generate new ID
        account["id"] = account_id # Assign it to those account which dont conatins ids
        update = True
    
    return update
