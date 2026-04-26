import base64
import hashlib

from app.core.config import settings


class TokenCipher:
    """Lightweight symmetric obfuscation for API tokens at rest.

    For high-security production environments replace with KMS/Vault-backed encryption.
    """

    @staticmethod
    def _key_stream(length: int) -> bytes:
        digest = hashlib.sha256(settings.secret_key.encode('utf-8')).digest()
        repeated = (digest * ((length // len(digest)) + 1))[:length]
        return repeated

    @classmethod
    def encrypt(cls, value: str) -> str:
        if not value:
            return ''
        raw = value.encode('utf-8')
        key = cls._key_stream(len(raw))
        encrypted = bytes(b ^ k for b, k in zip(raw, key, strict=False))
        return base64.urlsafe_b64encode(encrypted).decode('ascii')

    @classmethod
    def decrypt(cls, value: str) -> str:
        if not value:
            return ''
        encrypted = base64.urlsafe_b64decode(value.encode('ascii'))
        key = cls._key_stream(len(encrypted))
        raw = bytes(b ^ k for b, k in zip(encrypted, key, strict=False))
        return raw.decode('utf-8')
