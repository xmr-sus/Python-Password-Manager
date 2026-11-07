from assets.config import MASTER_FILE 
import json
import os
import tempfile

# def save_master_hash(hashed_password, kek_salt, wrapped_vault_key):
    
#     master_data = {
#         "password_hash" : hashed_password,
#         "kek_salt": kek_salt.hex(),
#         "wrapped_vault_key": wrapped_vault_key
#     }
#     try:
#         with open(MASTER_FILE , "w") as hashings:
#             json.dump(master_data, hashings, indent=4)
#         return True
#     except (OSError, json.JSONDecodeError):
#         print("Couldn't save master hash.")
#         return False

def save_master_hash(hashed_password, kek_salt, wrapped_vault_key):

    master_data = {
        "password_hash": hashed_password,
        "kek_salt": kek_salt.hex(),
        "wrapped_vault_key": wrapped_vault_key
    }

    directory = os.path.dirname(os.path.abspath(MASTER_FILE))
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directory,
            delete=False
        ) as temp_file:

            temp_path = temp_file.name

            json.dump(master_data, temp_file, indent=4)
            temp_file.flush()
            os.fsync(temp_file.fileno())

        os.replace(temp_path, MASTER_FILE)

        return True

    except (OSError, TypeError, ValueError):
        print("Couldn't save master hash.")
        return False

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                print("Warning: Could not remove temporary master file.")

def load_master_hash():
    if os.path.exists(MASTER_FILE):
        try:
            with open(MASTER_FILE, "r") as hashings:
                master_data = json.load(hashings)
            return master_data.get("password_hash")

        except (OSError, json.JSONDecodeError):
            print("Couldn't load saved master_data.")
            return None
    else:
        return None

def load_kek_salt():
    if os.path.exists(MASTER_FILE):
        try:
            with open(MASTER_FILE, "r") as hashings:
                master_data = json.load(hashings)

            salt = master_data.get("kek_salt")

            if salt:
                return bytes.fromhex(salt)

            return None

        except (OSError, json.JSONDecodeError, ValueError):
            print("Couldn't load encryption salt.")
            return None

    return None

def load_legacy_encryption_salt():
    if os.path.exists(MASTER_FILE):
        try:
            with open(MASTER_FILE, "r") as hashings:
                master_data = json.load(hashings)

            salt = master_data.get("encryption_salt")

            if salt:
                return bytes.fromhex(salt)

            return None

        except (OSError, json.JSONDecodeError, ValueError, TypeError):
            print("Couldn't load legacy encryption salt.")
            return None

    return None

def load_wrapped_vault_key():
    if os.path.exists(MASTER_FILE):
        try:
            with open(MASTER_FILE, "r") as keys:
                master_data = json.load(keys)

            wrapped_vault_key = master_data.get("wrapped_vault_key")

            if wrapped_vault_key:
                return wrapped_vault_key
            else:
                return None
        except (OSError, json.JSONDecodeError, ValueError):
            print("Couldn't load wrapped vault key.")
            return None

    return None

def save_encryption_salt(salt):
    if os.path.exists(MASTER_FILE):
        try:
            with open(MASTER_FILE, "r") as hashings:
                master_data = json.load(hashings)

            master_data["encryption_salt"] = salt.hex()
            
            with open(MASTER_FILE, "w") as encryptions:
                json.dump(master_data, encryptions, indent=4)
            return True
        except (OSError, json.JSONDecodeError, ValueError):
            print("Couldn't save encryption salt.")
            return False
    return False

def get_vault_format():
    if not os.path.exists(MASTER_FILE):
        return "new"

    try:
        with open(MASTER_FILE, "r", encoding="utf-8") as file:
            master_data = json.load(file)

        if not isinstance(master_data, dict):
            return None

        if ("kek_salt" in master_data and "wrapped_vault_key" in master_data):
            return "envelope"

        if "encryption_salt" in master_data:
            return "legacy"

        return None

    except (OSError, json.JSONDecodeError):
        print("Unable to identify vault format.")
        return None
