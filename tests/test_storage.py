# from assets.authentication.storage import save_master_hash, load_master_hash

# test_hash = "test_hash_123"

# save_master_hash(test_hash)

# loaded_hash = load_master_hash()

# print("Loaded hash:", loaded_hash)
# print("Hashes match:", loaded_hash == test_hash)

from assets.authentication.storage import (
    load_master_hash,
    load_legacy_encryption_salt,
    save_encryption_salt
)
from assets.authentication.key_derivation import generate_salt

# Preserve the existing master password hash
original_hash = load_master_hash()

# Generate a new salt
salt = generate_salt()

# Save the salt
result = save_encryption_salt(salt)

# Load the values again
loaded_hash = load_master_hash()
loaded_salt = load_legacy_encryption_salt()

print("Salt saved:", result)
print("Master hash preserved:", original_hash == loaded_hash)
print("Salt preserved:", salt == loaded_salt)