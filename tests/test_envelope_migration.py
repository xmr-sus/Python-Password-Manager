
import unittest
import tempfile
import os
import json

from unittest.mock import patch

from assets.authentication.hashing import hash_password
from assets.authentication.key_derivation import generate_salt, derive_key
from assets.authentication.encryption import encrypt_password, decrypt_password

import assets.authentication.storage as storage
import assets.authentication.envelope_migration as migration


class TestEnvelopeMigration(unittest.TestCase):

    def setUp(self):
        # Create an isolated temporary directory for every test.
        self.temp_dir = tempfile.TemporaryDirectory()

        self.original_file_name = migration.FILE_NAME
        self.original_master_file = migration.MASTER_FILE
        self.original_storage_master_file = storage.MASTER_FILE

        migration.FILE_NAME = os.path.join(self.temp_dir.name, "accounts.json")
        migration.MASTER_FILE = os.path.join(self.temp_dir.name, "master.json")
        storage.MASTER_FILE = migration.MASTER_FILE

        self.master_password = "TestMasterPassword123!"

        # Create a legacy master password hash and encryption salt.
        self.password_hash = hash_password(self.master_password)
        self.legacy_salt = generate_salt()
        self.old_key = derive_key(self.master_password, self.legacy_salt)

        # Create sample accounts encrypted with the legacy key.
        self.plaintext_passwords = [
            "EmailPassword123",
            "GamingPassword456",
            "SocialPassword789"
        ]

        self.accounts = []

        for index, password in enumerate(self.plaintext_passwords):
            self.accounts.append({
                "id": f"test-id-{index}",
                "username": f"user{index}",
                "website": f"website{index}.com",
                "password": encrypt_password(password, self.old_key)
            })

        # Save the legacy accounts file.
        with open(migration.FILE_NAME, "w", encoding="utf-8") as file:
            json.dump(self.accounts, file, indent=4)

        # Save legacy master metadata.
        self.master_data = {
            "password_hash": self.password_hash,
            "encryption_salt": self.legacy_salt.hex()
        }

        with open(migration.MASTER_FILE, "w", encoding="utf-8") as file:
            json.dump(self.master_data, file, indent=4)

        # Keep the original file contents for rollback checks.
        with open(migration.FILE_NAME, "rb") as file:
            self.original_accounts_data = file.read()

        with open(migration.MASTER_FILE, "rb") as file:
            self.original_master_data = file.read()

    def tearDown(self):
        migration.FILE_NAME = self.original_file_name
        migration.MASTER_FILE = self.original_master_file
        storage.MASTER_FILE = self.original_storage_master_file

        self.temp_dir.cleanup()

    def assert_original_files_unchanged(self):
        with open(migration.FILE_NAME, "rb") as file:
            self.assertEqual(file.read(), self.original_accounts_data)

        with open(migration.MASTER_FILE, "rb") as file:
            self.assertEqual(file.read(), self.original_master_data)

    # Test 1: Successful migration.
    def test_successful_migration(self):
        migrated_accounts = json.loads(json.dumps(self.accounts))

        vault_key = migration.migrate_to_envelope_encryption(
            migrated_accounts,
            self.master_password
        )

        self.assertIsInstance(vault_key, bytes)
        self.assertEqual(len(vault_key), 32)

        # Verify that the original passwords survived migration.
        with open(migration.FILE_NAME, "r", encoding="utf-8") as file:
            saved_accounts = json.load(file)

        for account, original_password in zip(
            saved_accounts,
            self.plaintext_passwords
        ):
            recovered_password = decrypt_password(
                account["password"],
                vault_key
            )

            self.assertEqual(recovered_password, original_password)

        # Verify the new master metadata.
        with open(migration.MASTER_FILE, "r", encoding="utf-8") as file:
            new_master_data = json.load(file)

        self.assertIn("kek_salt", new_master_data)
        self.assertIn("wrapped_vault_key", new_master_data)
        self.assertNotIn("encryption_salt", new_master_data)

        # Verify the migration journal was removed.
        journal_path = migration.MASTER_FILE + ".migration_journal"
        self.assertFalse(os.path.exists(journal_path))

        # Verify that both original backups were preserved.
        self.assertTrue(
            os.path.exists(
                migration.FILE_NAME + ".pre_envelope_migration.bak"
            )
        )

        self.assertTrue(
            os.path.exists(
                migration.MASTER_FILE + ".pre_envelope_migration.bak"
            )
        )

    # Test 2: Incorrect master password.
    def test_wrong_master_password(self):
        migrated_accounts = json.loads(json.dumps(self.accounts))

        result = migration.migrate_to_envelope_encryption(
            migrated_accounts,
            "WrongMasterPassword"
        )

        self.assertFalse(result)
        self.assert_original_files_unchanged()

    # Test 3: Incorrect legacy encryption key.
    def test_incorrect_legacy_encryption_key(self):
        # Replace the legacy salt with another valid salt.
        wrong_salt = generate_salt()

        modified_master_data = {
            "password_hash": self.password_hash,
            "encryption_salt": wrong_salt.hex()
        }

        with open(migration.MASTER_FILE, "w", encoding="utf-8") as file:
            json.dump(modified_master_data, file, indent=4)

        # Record the current master file contents.
        with open(migration.MASTER_FILE, "rb") as file:
            self.original_master_data = file.read()

        migrated_accounts = json.loads(json.dumps(self.accounts))

        result = migration.migrate_to_envelope_encryption(
            migrated_accounts,
            self.master_password
        )

        self.assertFalse(result)
        self.assert_original_files_unchanged()

    # Test 4: Account file replacement failure.
    def test_accounts_replacement_failure(self):
        migrated_accounts = json.loads(json.dumps(self.accounts))

        original_replace = os.replace
        failure_triggered = False

        def fail_once(source, destination):
            nonlocal failure_triggered

            if (
                os.fspath(destination) == migration.FILE_NAME
                and not failure_triggered
            ):
                failure_triggered = True
                raise OSError("Simulated accounts replacement failure.")

            return original_replace(source, destination)

        with patch(
            "assets.authentication.envelope_migration.os.replace",
            side_effect=fail_once
        ):
            result = migration.migrate_to_envelope_encryption(
                migrated_accounts,
                self.master_password
            )

        self.assertFalse(result)
        self.assertTrue(failure_triggered)
        self.assert_original_files_unchanged()

    # Test 5: Master file replacement failure.
    def test_master_replacement_failure(self):
        migrated_accounts = json.loads(json.dumps(self.accounts))

        original_replace = os.replace
        failure_triggered = False

        def fail_once(source, destination):
            nonlocal failure_triggered

            if (
                os.fspath(destination) == migration.MASTER_FILE
                and not failure_triggered
            ):
                failure_triggered = True
                raise OSError("Simulated master replacement failure.")

            return original_replace(source, destination)

        with patch(
            "assets.authentication.envelope_migration.os.replace",
            side_effect=fail_once
        ):
            result = migration.migrate_to_envelope_encryption(
                migrated_accounts,
                self.master_password
            )

        self.assertFalse(result)
        self.assertTrue(failure_triggered)
        self.assert_original_files_unchanged()


if __name__ == "__main__":
    unittest.main()
