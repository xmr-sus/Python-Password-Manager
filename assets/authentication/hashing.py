from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()

def hash_password(password):
    hashed = ph.hash(password)

    return hashed

def verify_password(password, hashed_password):
    try:
        verify = ph.verify(hashed_password, password)
    except VerifyMismatchError:
        return False

    return verify