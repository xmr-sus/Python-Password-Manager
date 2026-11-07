import os
import json
import tempfile

from assets.config import FILE_NAME

def save_accounts(accounts):
    """Safely save account details using atomic file replacement."""

    directory = os.path.dirname(os.path.abspath(FILE_NAME))
    temp_path = None

    try:
        # Create a temporary file in the same directory
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directory,
            delete=False
        ) as temp_file:

            temp_path = temp_file.name

            # Write account data
            json.dump(accounts, temp_file, indent=4)

            # Flush data to storage
            temp_file.flush()
            os.fsync(temp_file.fileno())

        # Replace the original file after writing succeeds
        os.replace(temp_path, FILE_NAME)

        print("Changes saved successfully!")
        return True

    except (OSError, TypeError, ValueError) as error:
        print("Unable to save account data:", error)
        return False

    finally:
        # Remove leftover temporary files if something failed
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                print("Warning: Could not remove temporary file.")

# A few important concepts:
# - NamedTemporaryFile() creates a temporary file with a unique name.
# - dir=directory ensures it's created alongside accounts.json.
# - delete=False prevents Python from automatically deleting it when the file closes.
# - flush() pushes buffered data toward the operating system.
# - os.fsync() asks the operating system to flush the file's data to storage.