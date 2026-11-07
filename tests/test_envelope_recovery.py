
import json
import os
import shutil
import tempfile
import unittest

from unittest.mock import patch
from assets.authentication import envelope_migration as migration


class TestEnvelopeRecovery(unittest.TestCase):
    def test_invalid_journal(self):
        # Create a journal with an invalid status.
        journal_path = migration.MASTER_FILE + ".migration_journal"

        with open(journal_path, "w", encoding="utf-8") as file:
            json.dump({"status": "completed"}, file)

        result = migration.recover_interrupted_migration()

        self.assertFalse(result)

        # The invalid journal should remain for investigation.
        self.assertTrue(os.path.exists(journal_path))

    def test_missing_backup(self):
        # Create only one of the two required backups.
        accounts_backup = migration.FILE_NAME + ".pre_envelope_migration.bak"
        master_backup = migration.MASTER_FILE + ".pre_envelope_migration.bak"

        with open(accounts_backup, "w", encoding="utf-8") as file:
            json.dump([], file)

        # Create a journal referencing both backups.
        migration.create_migration_journal(accounts_backup, master_backup)

        result = migration.recover_interrupted_migration()

        self.assertFalse(result)

        # Recovery should preserve the journal.
        journal_path = migration.MASTER_FILE + ".migration_journal"
        self.assertTrue(os.path.exists(journal_path))

    def test_restore_failure(self):
        # Create both backup files.
        accounts_backup = migration.FILE_NAME + ".pre_envelope_migration.bak"
        master_backup = migration.MASTER_FILE + ".pre_envelope_migration.bak"

        with open(accounts_backup, "w", encoding="utf-8") as file:
            json.dump([], file)

        with open(master_backup, "w", encoding="utf-8") as file:
            json.dump({}, file)

        migration.create_migration_journal(accounts_backup, master_backup)

        # Simulate failure while restoring the accounts file.
        with patch.object(
            migration,
            "restore_backup",
            side_effect=[False, True]
        ):
            result = migration.recover_interrupted_migration()

        self.assertFalse(result)

        # The journal must remain because recovery was unsuccessful.
        journal_path = migration.MASTER_FILE + ".migration_journal"
        self.assertTrue(os.path.exists(journal_path))

    def setUp(self):
        # Create an isolated temporary directory for every test.
        self.temp_dir = tempfile.TemporaryDirectory()
        self.directory = self.temp_dir.name

        # Redirect the migration module to temporary files.
        self.original_file_name = migration.FILE_NAME
        self.original_master_file = migration.MASTER_FILE

        migration.FILE_NAME = os.path.join(self.directory, "accounts.json")
        migration.MASTER_FILE = os.path.join(self.directory, "master.json")

    def tearDown(self):
        # Restore the original paths after each test.
        migration.FILE_NAME = self.original_file_name
        migration.MASTER_FILE = self.original_master_file

        self.temp_dir.cleanup()

    def test_no_journal_exists(self):
        # Recovery should succeed when there is nothing to recover.
        result = migration.recover_interrupted_migration()

        self.assertTrue(result)

    def test_interrupted_migration_restores_original_files(self):
        # Create the original vault files.
        original_accounts = [
            {"username": "test_user", "website": "example.com", "password": "old_password"}
        ]

        original_master = {
            "password_hash": "old_hash",
            "encryption_salt": "old_salt"
        }

        with open(migration.FILE_NAME, "w", encoding="utf-8") as file:
            json.dump(original_accounts, file)

        with open(migration.MASTER_FILE, "w", encoding="utf-8") as file:
            json.dump(original_master, file)

        # Create backups of both original files.
        accounts_backup = migration.FILE_NAME + ".pre_envelope_migration.bak"
        master_backup = migration.MASTER_FILE + ".pre_envelope_migration.bak"

        shutil.copy2(migration.FILE_NAME, accounts_backup)
        shutil.copy2(migration.MASTER_FILE, master_backup)

        # Simulate a partially completed migration.
        migrated_accounts = [
            {"username": "test_user", "website": "example.com", "password": "new_encrypted_password"}
        ]

        migrated_master = {
            "password_hash": "new_hash",
            "kek_salt": "new_salt",
            "wrapped_vault_key": "new_wrapped_key"
        }

        with open(migration.FILE_NAME, "w", encoding="utf-8") as file:
            json.dump(migrated_accounts, file)

        with open(migration.MASTER_FILE, "w", encoding="utf-8") as file:
            json.dump(migrated_master, file)

        # Create the journal indicating that migration is unfinished.
        migration.create_migration_journal(accounts_backup, master_backup)

        # Run recovery.
        result = migration.recover_interrupted_migration()

        self.assertTrue(result)

        # Verify that both original files were restored.
        with open(migration.FILE_NAME, "r", encoding="utf-8") as file:
            restored_accounts = json.load(file)

        with open(migration.MASTER_FILE, "r", encoding="utf-8") as file:
            restored_master = json.load(file)

        self.assertEqual(restored_accounts, original_accounts)
        self.assertEqual(restored_master, original_master)

        # Verify that the journal was removed.
        journal_path = migration.MASTER_FILE + ".migration_journal"
        self.assertFalse(os.path.exists(journal_path))

    

if __name__ == "__main__":
    unittest.main(verbosity=2)
