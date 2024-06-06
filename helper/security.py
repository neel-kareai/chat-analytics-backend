import bcrypt

def get_hashed_password(password: str) -> bytes:
    """
        Hash a password for the first time
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())


def verify_password(password: bytes, hashed_password: bytes) -> bool:
    """
        Check hashed password. Using bcrypt, the salt is saved into the hash itself
    """
    return bcrypt.checkpw(password, hashed_password)

