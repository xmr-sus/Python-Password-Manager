from assets.authentication.key_derivation import (
    generate_vault_key,
    generate_salt,
    derive_key
)
from assets.authentication.key_wrapping import (
    wrap_vault_key,
    unwrap_vault_key
)
from cryptography.exceptions import InvalidTag


def test_wrap_and_unwrap_vault_key():
    # Generate a random vault key (DEK)
    vault_key = generate_vault_key()

    # Generate salt and derive KEK
    salt = generate_salt()
    kek = derive_key("test_master_password", salt)

    # Wrap the vault key
    wrapped_key = wrap_vault_key(vault_key, kek)

    # Unwrap it using the same KEK
    recovered_key = unwrap_vault_key(wrapped_key, kek)

    # Both keys should be identical
    assert recovered_key == vault_key


def test_unwrap_with_wrong_kek():
    vault_key = generate_vault_key()

    # Derive the correct KEK
    salt = generate_salt()
    correct_kek = derive_key("test_master_password", salt)

    # Wrap using the correct KEK
    wrapped_key = wrap_vault_key(vault_key, correct_kek)

    # Derive a different KEK
    wrong_kek = derive_key("wrong_password", salt)

    # Unwrapping with the wrong KEK should fail
    try:
        unwrap_vault_key(wrapped_key, wrong_kek)
    except InvalidTag:
        pass
    else:
        raise AssertionError("Unwrapping with the wrong KEK should fail!")


if __name__ == "__main__":
    test_wrap_and_unwrap_vault_key()
    test_unwrap_with_wrong_kek()
    print("All key-wrapping tests passed!")