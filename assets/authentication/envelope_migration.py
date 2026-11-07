
import copy
import os
import json
import tempfile
import binascii
from cryptography.exceptions import InvalidTag
import shutil
import filecmp
# Notice: This whole function is directly written by ChatGPT...
from assets.config import FILE_NAME, MASTER_FILE
from assets.authentication.hashing import verify_password
from assets.authentication.key_derivation import derive_key, generate_salt, generate_vault_key
from assets.authentication.encryption import encrypt_password, decrypt_password
from assets.authentication.key_wrapping import wrap_vault_key, unwrap_vault_key
from assets.authentication.storage import load_master_hash, load_legacy_encryption_salt
from assets.save_account import save_accounts

# <---------------------------------------------------------------------------------------------------------->
# PURPOSE:
# Your old system encrypts account passwords directly using a key derived from your master password. Your new system uses a separate randomly generated vault key (DEK), which is protected by another key (KEK) derived from your master password.

# The migration function converts your existing vault from the old architecture to the new one without changing the actual account passwords.

# <---------------------------------------------------------------------------------------------------------->

# HELPER 1: Write JSON data to a temporary file without replacing the original.
def write_temp_json(data, destination):
    directory = os.path.dirname(os.path.abspath(destination))
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directory,
            delete=False,
            suffix=".tmp"
        ) as temp_file:

            temp_path = temp_file.name
            json.dump(data, temp_file, indent=4)
            temp_file.flush()
            os.fsync(temp_file.fileno())

        return temp_path

    except (OSError, TypeError, ValueError):
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

        raise

# HELPER 2: Create a backup of an existing file and verify that it matches.
def create_backup(source):
    backup_path = source + ".pre_envelope_migration.bak"

    if not os.path.isfile(source):
        raise FileNotFoundError(f"Original file missing: {source}")

    if os.path.exists(backup_path):
        raise FileExistsError(f"Backup already exists: {backup_path}")

    shutil.copy2(source, backup_path)

    if not filecmp.cmp(source, backup_path, shallow=False):
        raise OSError(f"Backup verification failed: {backup_path}")

    return backup_path

def restore_backup(backup_path, original_path):
    directory = os.path.dirname(os.path.abspath(original_path))
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            dir=directory,
            delete=False,
            suffix=".restore"
        ) as temp_file:
            temp_path = temp_file.name

        shutil.copy2(backup_path, temp_path)
        os.replace(temp_path, original_path)

        return True

    except OSError:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

        return False

# HELPER 4: Create a journal to track an unfinished migration.
def create_migration_journal(accounts_backup, master_backup):
    journal_path = MASTER_FILE + ".migration_journal"

    journal_data = {
        "status": "in_progress",
        "accounts_backup": accounts_backup,
        "master_backup": master_backup
    }

    temp_path = write_temp_json(journal_data, journal_path)

    os.replace(temp_path, journal_path)

    return journal_path

# HELPER 5: Detect and recover an interrupted migration.
def recover_interrupted_migration():
    journal_path = MASTER_FILE + ".migration_journal"

    # No journal means there is no interrupted migration to recover.
    if not os.path.exists(journal_path):
        return True

    try:
        with open(journal_path, "r", encoding="utf-8") as file:
            journal_data = json.load(file)

        # Verify that the journal describes an unfinished migration.
        if journal_data.get("status") != "in_progress":
            print("Invalid migration journal.")
            return False

        # Verify that the backup paths point to the expected files.
        expected_accounts_backup = FILE_NAME + ".pre_envelope_migration.bak"
        expected_master_backup = MASTER_FILE + ".pre_envelope_migration.bak"

        accounts_backup = journal_data["accounts_backup"]
        master_backup = journal_data["master_backup"]

        if accounts_backup != expected_accounts_backup or master_backup != expected_master_backup:
            print("Migration journal contains unexpected backup paths.")
            return False

        # Make sure both backups exist before restoring either file.
        if not os.path.isfile(accounts_backup) or not os.path.isfile(master_backup):
            print("Required migration backups are missing.")
            return False

        # Restore both original files.
        accounts_restored = restore_backup(accounts_backup, FILE_NAME)
        master_restored = restore_backup(master_backup, MASTER_FILE)

        if not accounts_restored or not master_restored:
            print("CRITICAL: Migration recovery was unsuccessful.")
            print("Keep the journal and backup files safe.")
            return False

        # Remove the journal only after both restorations succeed.
        os.remove(journal_path)

        print("Interrupted migration detected.")
        print("Original vault files successfully restored.")

        return True

    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        print("Migration recovery failed:", error)
        return False

def migrate_to_envelope_encryption(accounts, master_password):

    # Step 1: Authenticate the user by verifying the supplied master password.
    master_hash = load_master_hash()

    if not master_hash or not verify_password(master_password, master_hash):
        print("Invalid master password.")
        return False

    # Step 2: Retrieve the legacy salt used by the old encryption system.
    legacy_salt = load_legacy_encryption_salt()

    if not legacy_salt:
        print("Legacy encryption salt is missing or invalid.")
        return False

    # Step 3: Derive the old encryption key and create a copy of the accounts.
    old_key = derive_key(master_password, legacy_salt)
    migrated_accounts = copy.deepcopy(accounts)

    # Step 4: Decrypt all existing account passwords using the old key.
    try:
        for account in migrated_accounts:
            account["password"] = decrypt_password(account["password"], old_key)

    except (InvalidTag, KeyError, ValueError, TypeError, binascii.Error):
        print("Migration failed. Could not decrypt existing account data.")
        return False

    # Step 5: Generate a new vault key (DEK) and a new KEK salt.
    new_vault_key = generate_vault_key()
    new_kek_salt = generate_salt()

    # Step 6: Derive the new KEK using the master password and new salt.
    new_kek = derive_key(master_password, new_kek_salt)

    # Step 7: Wrap (encrypt) the new vault key using the new KEK.
    wrapped_vault_key = wrap_vault_key(new_vault_key, new_kek)

    # Step 8: Preserve the decrypted passwords so they can be verified later.
    plaintext_passwords = [
        account["password"] for account in migrated_accounts
    ]

    # Step 9: Re-encrypt every account password using the new vault key.
    for account in migrated_accounts:
        account["password"] = encrypt_password(account["password"], new_vault_key)
    
    # Step 10: Verify that every newly encrypted password decrypts correctly.
    try:
        for account, original_password in zip(migrated_accounts, plaintext_passwords):
            recovered_password = decrypt_password(account["password"], new_vault_key)

            if recovered_password != original_password:
                print("Password verification failed.")
                return False

    except (InvalidTag, KeyError, ValueError, TypeError, binascii.Error):
        print("New encryption verification failed.")
        return False

    # Step 11: Verify that the wrapped vault key can be recovered using the KEK.
    # Verify that the wrapped vault key can be recovered
    try:
        recovered_vault_key = unwrap_vault_key(wrapped_vault_key, new_kek)

        if recovered_vault_key != new_vault_key:
            print("Vault key verification failed.")
            return False

    except (InvalidTag, KeyError, ValueError, TypeError, binascii.Error):
        print("Unable to verify wrapped vault key.")
        return False

    # Step 12: Prepare the new master metadata containing the hash, KEK salt, and wrapped DEK.
    new_master_data = {
        "password_hash": master_hash,
        "kek_salt": new_kek_salt.hex(),
        "wrapped_vault_key": wrapped_vault_key
    }

    # Step 13: Initialize paths for the temporary account and master files.
    accounts_temp_path = None
    master_temp_path = None

    # Step 14: Write the migrated accounts and new master metadata to temporary files.
    try:
        accounts_temp_path = write_temp_json(migrated_accounts, FILE_NAME)

        master_temp_path = write_temp_json(new_master_data, MASTER_FILE)

    except (OSError, TypeError, ValueError) as error:
        print("Could not prepare migration files.")

        for path in (accounts_temp_path, master_temp_path):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    print("Warning: Could not remove a temporary file.")

        return False

    # Step 15: Read the temporary files back and verify their contents.
    try:
        with open(accounts_temp_path, "r", encoding="utf-8") as file:
            staged_accounts = json.load(file)

        with open(master_temp_path, "r", encoding="utf-8") as file:
            staged_master_data = json.load(file)

        # Verify account data
        if len(staged_accounts) != len(plaintext_passwords):
            raise ValueError("Account count mismatch.")

        for account, original_password in zip(staged_accounts, plaintext_passwords):
            recovered = decrypt_password(account["password"], new_vault_key)

            if recovered != original_password:
                raise ValueError("Account verification failed.")

        # Verify master metadata
        if staged_master_data["password_hash"] != master_hash:
            raise ValueError("Master hash mismatch.")

        staged_kek_salt = bytes.fromhex(staged_master_data["kek_salt"])
        staged_kek = derive_key(master_password, staged_kek_salt)

        staged_vault_key = unwrap_vault_key(staged_master_data["wrapped_vault_key"], staged_kek)

        if staged_vault_key != new_vault_key:
            raise ValueError("Vault key mismatch.")

    except (OSError, json.JSONDecodeError, KeyError, ValueError, TypeError, InvalidTag, binascii.Error):
        for path in (accounts_temp_path, master_temp_path):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    print("Warning: Could not remove a temporary file.")
        print("Staged file verification failed.")
        return False

    # Step 16: Create and verify backups of both original files before replacing anything.
    accounts_backup = None
    master_backup = None

    try:
        accounts_backup = create_backup(FILE_NAME)
        master_backup = create_backup(MASTER_FILE)

    except (OSError, FileNotFoundError, FileExistsError) as error:
        print("Could not safely create migration backups.")
        # Remove any backup created during this attempt
        for path in (accounts_backup, master_backup):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    print("Warning: Could not remove a backup file.")

        return False

    # Step 21: Create a journal before replacing either original file.
    try:
        journal_path = create_migration_journal(accounts_backup, master_backup)

    except (OSError, TypeError, ValueError) as error:
        print("Could not create migration journal:", error)
        return False

    # Step 17: Replace both original files with the verified temporary files.
    try:
        os.replace(accounts_temp_path, FILE_NAME)
        accounts_temp_path = None

        os.replace(master_temp_path, MASTER_FILE)
        master_temp_path = None

    except OSError as error:
        print("Migration commit failed:", error)

        # Step 18: Restore both original files from their backups.
        accounts_restored = restore_backup(accounts_backup, FILE_NAME)
        master_restored = restore_backup(master_backup, MASTER_FILE)

        if accounts_restored and master_restored:
            print("Original files successfully restored.")
        else:
            print("CRITICAL: Could not restore both original files.")
            print("Keep your backup files safe.")

        return False

    # Step 19: Verify the files after replacing the originals.
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            final_accounts = json.load(file)

        with open(MASTER_FILE, "r", encoding="utf-8") as file:
            final_master_data = json.load(file)

        if final_accounts != migrated_accounts:
            raise ValueError("Final account data does not match.")

        if final_master_data != new_master_data:
            raise ValueError("Final master metadata does not match.")

    except (OSError, json.JSONDecodeError, ValueError) as error:
        print("Final migration verification failed:", error)

        accounts_restored = restore_backup(accounts_backup, FILE_NAME)
        master_restored = restore_backup(master_backup, MASTER_FILE)

        if accounts_restored and master_restored:
            print("Original files successfully restored.")
        else:
            print("CRITICAL: Could not restore both original files.")

        return False

    # Step 22: Remove the migration journal after successful verification.
    try:
        os.remove(journal_path)

    except OSError as error:
        print("Could not finalize migration:", error)
        print("The journal has been preserved for startup recovery.")
        return False

    # Step 20: Update the in-memory accounts after successful verification.
    accounts[:] = migrated_accounts

    print("Envelope encryption migration completed successfully!")
    print("Original backup files have been preserved.")
    return new_vault_key
# Here's the entire process in simple terms:
# 1. Authenticate: Check whether the supplied master password is correct.
# 2. Get old salt: Retrieve the salt used by the previous encryption system.
# 3. Recover old key: Regenerate the original encryption key using the master password and old salt.
# 4. Copy accounts: Create an independent copy so the original data remains untouched.
# 5. Decrypt passwords: Decrypt all existing account passwords using the old key.
# 6. Generate new keys: Create a new DEK and a new KEK salt.
# 7. Derive KEK: Use the master password and new salt to generate the KEK.
# 8. Wrap DEK: Encrypt the new DEK using the KEK.
# 9. Re-encrypt passwords: Encrypt all account passwords using the new DEK.
# 10. Verify encryption: Check that every password can be decrypted correctly.
# 11. Verify key wrapping: Check that the wrapped DEK can be recovered correctly.

# In one sentence:
# Your function takes existing encrypted passwords, decrypts them using the old encryption key, re-encrypts them using a new vault key, and verifies that the new encryption system works.
