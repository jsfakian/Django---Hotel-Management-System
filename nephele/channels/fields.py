# nephele/channels/fields.py
"""Fernet-encrypted CharField for channel API credentials."""

from __future__ import annotations

import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)

_FERNET_PREFIX = "gAAAAA"  # Fernet tokens always start with this


def _get_fernet() -> Fernet:
    """
    Build a Fernet instance from CHANNEL_CREDENTIALS_KEY or derive from SECRET_KEY.

    CHANNEL_CREDENTIALS_KEY may be a Fernet key (url-safe base64 of 32 bytes)
    or any passphrase (hashed via SHA256 → urlsafe_b64).
    """
    raw = getattr(settings, "CHANNEL_CREDENTIALS_KEY", None) or ""
    if not raw:
        digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
        return Fernet(base64.urlsafe_b64encode(digest))

    key_bytes = raw.encode("utf-8") if isinstance(raw, str) else raw
    try:
        return Fernet(key_bytes)
    except (ValueError, TypeError):
        digest = hashlib.sha256(key_bytes).digest()
        return Fernet(base64.urlsafe_b64encode(digest))


class EncryptedCharField(models.CharField):
    """CharField that encrypts values at rest with Fernet."""

    description = "Fernet-encrypted character field"

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def to_python(self, value):
        if value is None or value == "":
            return value
        if not isinstance(value, str):
            value = str(value)
        # Legacy plaintext rows (pre-encryption migration)
        if not value.startswith(_FERNET_PREFIX):
            return value
        try:
            return _get_fernet().decrypt(value.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            logger.warning("Failed to decrypt EncryptedCharField value; returning as-is")
            return value
        except Exception:
            logger.exception("Unexpected decrypt error for EncryptedCharField")
            return value

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None or value == "":
            return value
        if not isinstance(value, str):
            value = str(value)
        # Avoid double-encryption if already a Fernet token
        if value.startswith(_FERNET_PREFIX):
            return value
        token = _get_fernet().encrypt(value.encode("utf-8"))
        return token.decode("utf-8")
