"""Encryption for workload payloads persisted by the Execution Plane."""

from __future__ import annotations

import base64
import json
import os
import secrets
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator

_MARKER = "_ep_encrypted_payload_v1"
_ASSOCIATED_DATA = b"syntara-execution-plane-work-item-payload-v1"
_AES_KEY_LENGTH_BYTES = 32


class EncryptedWorkItemPayload(TypeDecorator[dict[str, Any]]):
    """Encrypt payload objects while retaining the existing JSONB column shape."""

    impl = JSONB
    cache_ok = True

    @staticmethod
    def _key() -> bytes:
        encoded = os.environ.get("EP_CREDENTIAL_ENCRYPTION_KEY")
        if encoded is None:
            key_path = os.environ.get("EP_CREDENTIAL_ENCRYPTION_KEY_PATH")
            if key_path:
                encoded = Path(key_path).read_text(encoding="ascii").strip()
        if not encoded:
            msg = "EP payload encryption requires EP_CREDENTIAL_ENCRYPTION_KEY or EP_CREDENTIAL_ENCRYPTION_KEY_PATH"
            raise RuntimeError(msg)
        try:
            key = base64.urlsafe_b64decode(encoded)
        except ValueError as exc:
            msg = "EP_CREDENTIAL_ENCRYPTION_KEY is not valid base64url"
            raise ValueError(msg) from exc
        if len(key) != _AES_KEY_LENGTH_BYTES:
            msg = "EP_CREDENTIAL_ENCRYPTION_KEY must decode to 32 bytes"
            raise ValueError(msg)
        return key

    def process_bind_param(self, value: dict[str, Any] | None, _dialect: object) -> dict[str, Any] | None:
        """Encrypt newly written payloads; legacy plain objects remain readable."""
        if value is None:
            return None
        nonce = secrets.token_bytes(12)
        cleartext = json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8")
        encrypted = AESGCM(self._key()).encrypt(nonce, cleartext, _ASSOCIATED_DATA)
        return {_MARKER: base64.urlsafe_b64encode(nonce + encrypted).decode("ascii")}

    def process_result_value(self, value: dict[str, Any] | None, _dialect: object) -> dict[str, Any] | None:
        """Decrypt tagged values and pass legacy JSONB objects through for migration."""
        if value is None or not isinstance(value, dict) or _MARKER not in value:
            return value
        encoded = value.get(_MARKER)
        if not isinstance(encoded, str):
            msg = "Encrypted Execution Plane payload has an invalid format"
            raise TypeError(msg)
        encrypted = base64.urlsafe_b64decode(encoded)
        cleartext = AESGCM(self._key()).decrypt(encrypted[:12], encrypted[12:], _ASSOCIATED_DATA)
        payload = json.loads(cleartext)
        if not isinstance(payload, dict):
            msg = "Decrypted Execution Plane payload is not an object"
            raise TypeError(msg)
        return payload
