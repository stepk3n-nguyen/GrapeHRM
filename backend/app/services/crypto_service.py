"""
Mã hóa/giải mã chuỗi nhạy cảm (mật khẩu SMTP) bằng Fernet (đối xứng).
Khóa đọc từ biến môi trường ENCRYPTION_KEY. Nếu thiếu, dùng khóa dev cố định
(CHỈ dùng cho môi trường phát triển — production phải đặt ENCRYPTION_KEY).
"""

import os
import base64
import hashlib

# Khóa dev mặc định (sinh từ chuỗi cố định) — production hãy đặt ENCRYPTION_KEY thật.
_DEV_SEED = "grapehrm-dev-encryption-key-change-me"


def _get_fernet():
    from cryptography.fernet import Fernet

    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        # Sinh Fernet key hợp lệ (32 byte url-safe base64) từ seed cố định
        digest = hashlib.sha256(_DEV_SEED.encode()).digest()
        key = base64.urlsafe_b64encode(digest).decode()
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_secret(plaintext):
    if not plaintext:
        return None
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(token):
    if not token:
        return None
    try:
        return _get_fernet().decrypt(token.encode()).decode()
    except Exception:
        return None
