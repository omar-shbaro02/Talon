from app.core.config import settings


def _fernet():
    if not settings.token_encryption_key:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY is required for calendar token encryption")
    from cryptography.fernet import Fernet

    return Fernet(settings.token_encryption_key.encode("utf-8"))


def encrypt_token(token: str) -> str:
    return _fernet().encrypt(token.encode("utf-8")).decode("utf-8")


def decrypt_token(token: str) -> str:
    return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
