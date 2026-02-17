"""Unit tests for token encryption."""
import pytest

from config.crypto import encrypt, decrypt


def test_encrypt_decrypt_roundtrip():
    """Encrypted value decrypts back to original."""
    plain = "my-secret-refresh-token-123"
    cipher = encrypt(plain)
    assert decrypt(cipher) == plain


def test_encrypt_produces_different_output_each_time():
    """Encryption uses random IV, so same plaintext yields different ciphertext."""
    plain = "same-input"
    c1 = encrypt(plain)
    c2 = encrypt(plain)
    assert c1 != c2
    assert decrypt(c1) == plain
    assert decrypt(c2) == plain


def test_decrypt_empty_string_raises():
    """Invalid/tampered ciphertext raises on decrypt."""
    from cryptography.fernet import InvalidToken

    with pytest.raises(InvalidToken):
        decrypt("not-valid-ciphertext")


def test_encrypt_empty_string():
    """Empty string can be encrypted and decrypted."""
    cipher = encrypt("")
    assert decrypt(cipher) == ""


def test_encrypt_unicode():
    """Unicode strings are handled correctly."""
    plain = "tëst-tóken-日本語"
    assert decrypt(encrypt(plain)) == plain
