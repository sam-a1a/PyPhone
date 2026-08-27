#Password hashing
"""
Passwords are hashed with bcrypt: salted per-password and deliberately slow,
so a stolen database cannot be cracked with a rainbow table or a fast GPU.

Older rows in hospital.db hold bare SHA-256 digests (unsalted, and fast enough
to brute-force). Those are still recognised so existing accounts can log in,
and are replaced with a bcrypt hash on the next successful login.
"""
import base64
import hashlib
import hmac
import re

import bcrypt

# Work factor. Each +1 doubles the time to hash. 12 keeps a login at roughly
# a quarter of a second, which is slow for an attacker and unnoticeable here.
BCRYPT_ROUNDS = 12

# A legacy hash is exactly 64 lowercase hex characters (a SHA-256 digest).
# A bcrypt hash always starts with "$2" so the two can never be confused.
LEGACY_SHA256_PATTERN = re.compile(r'^[0-9a-f]{64}$')

# bcrypt only reads the first 72 bytes of a password and raises on anything
# longer, so the password is folded into a fixed-length digest first. Base64 of
# a SHA-256 digest is 44 ASCII bytes: always under the limit, and never
# contains a null byte (which bcrypt would treat as the end of the password).
def _prepare(password) -> bytes:
    if not password:
        password = ""
    digest = hashlib.sha256(password.encode('utf-8')).digest()
    return base64.b64encode(digest)


def hash_password(password) -> str:
    #Hash a password for storage. Same password in, different hash out
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(_prepare(password), salt).decode('ascii')


def is_legacy_hash(password_hash) -> bool:
    #True if this is one of the old unsalted SHA-256 digests
    if not password_hash or not isinstance(password_hash, str):
        return False
    return LEGACY_SHA256_PATTERN.match(password_hash) is not None


def verify_password(password, password_hash) -> bool:
    #Check a password against a stored hash. Never raises, just returns False
    if not password_hash or not isinstance(password_hash, str):
        return False

    if is_legacy_hash(password_hash):
        legacy = hashlib.sha256((password or "").encode('utf-8')).hexdigest()
        # compare_digest, not ==, so the comparison time gives nothing away
        return hmac.compare_digest(legacy, password_hash)

    try:
        return bcrypt.checkpw(_prepare(password), password_hash.encode('ascii'))
    except (ValueError, TypeError, UnicodeEncodeError):
        # Malformed hash in the database, treat as a failed login
        return False


def needs_rehash(password_hash) -> bool:
    #True if the stored hash is legacy or weaker than the current work factor
    if is_legacy_hash(password_hash):
        return True
    if not password_hash or not isinstance(password_hash, str):
        return False
    try:
        rounds = int(password_hash.split('$')[2])
    except (IndexError, ValueError):
        return False
    return rounds < BCRYPT_ROUNDS
