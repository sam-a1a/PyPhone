"""Tests for password hashing.

These pin down bcrypt specifically. The project used to store bare SHA-256
digests; a test that only checked "the right password verifies" would have
passed against that too, so most of what follows is about the properties
SHA-256 did *not* have.
"""
import hashlib

import bcrypt
import pytest

from apps.shared import security


class TestHashFormat:

    def test_produces_a_bcrypt_hash(self):
        digest = security.hash_password("correct horse battery staple")
        # $2b$ is the bcrypt identifier, followed by the cost
        assert digest.startswith("$2b$")
        assert len(digest) == 60

    def test_uses_the_configured_work_factor(self):
        digest = security.hash_password("hunter2000")
        cost = int(digest.split("$")[2])
        assert cost == security.BCRYPT_ROUNDS

    def test_work_factor_is_not_trivially_low(self):
        # Below ~10 rounds bcrypt stops being meaningfully slow to attack
        assert security.BCRYPT_ROUNDS >= 10

    def test_hash_does_not_contain_the_password(self):
        digest = security.hash_password("swordfish")
        assert "swordfish" not in digest

    def test_is_not_a_plain_sha256_digest(self):
        # The exact regression being fixed
        password = "adminadmin"
        digest = security.hash_password(password)
        assert digest != hashlib.sha256(password.encode()).hexdigest()


class TestSalting:

    def test_same_password_hashes_differently_each_time(self):
        # The property unsalted SHA-256 lacked: identical passwords across two
        # accounts produced identical digests, so cracking one cracked both
        first = security.hash_password("shared-password")
        second = security.hash_password("shared-password")
        assert first != second

    def test_both_hashes_of_the_same_password_still_verify(self):
        first = security.hash_password("shared-password")
        second = security.hash_password("shared-password")
        assert security.verify_password("shared-password", first)
        assert security.verify_password("shared-password", second)

    def test_salts_differ_between_hashes(self):
        salts = {security.hash_password("same")[:29] for _ in range(5)}
        assert len(salts) == 5


class TestVerify:

    def test_correct_password_verifies(self):
        digest = security.hash_password("letmein12")
        assert security.verify_password("letmein12", digest) is True

    def test_wrong_password_is_rejected(self):
        digest = security.hash_password("letmein12")
        assert security.verify_password("letmein13", digest) is False

    def test_verification_is_case_sensitive(self):
        digest = security.hash_password("CaseSensitive")
        assert security.verify_password("casesensitive", digest) is False

    def test_empty_password_is_rejected_against_a_real_hash(self):
        digest = security.hash_password("letmein12")
        assert security.verify_password("", digest) is False

    def test_a_hash_of_the_empty_password_verifies(self):
        # Nothing should crash on it; it just is not a useful password
        digest = security.hash_password("")
        assert security.verify_password("", digest) is True
        assert security.verify_password("x", digest) is False

    @pytest.mark.parametrize("stored", ["", None, "not-a-hash", "$2b$12$tooshort", 12345, b"bytes"])
    def test_malformed_stored_hash_fails_closed(self, stored):
        # A corrupt or missing hash must read as "login failed", never as an
        # exception the caller might mistake for success
        assert security.verify_password("anything", stored) is False

    def test_none_password_is_rejected(self):
        digest = security.hash_password("letmein12")
        assert security.verify_password(None, digest) is False

    def test_verifies_a_hash_made_by_bcrypt_directly(self):
        # Guards against hash_password and verify_password drifting together
        # into a scheme that only agrees with itself
        prepared = security._prepare("interop")
        digest = bcrypt.hashpw(prepared, bcrypt.gensalt(rounds=4)).decode()
        assert security.verify_password("interop", digest) is True


class TestUnicodeAndLength:

    @pytest.mark.parametrize("password", [
        "pässwörd",
        "密码密码密码",
        "🔒🔑 emoji password",
        "  leading and trailing  ",
        "tabs\tand\nnewlines",
    ])
    def test_round_trips_non_ascii_and_whitespace(self, password):
        digest = security.hash_password(password)
        assert security.verify_password(password, digest) is True
        assert security.verify_password(password + "x", digest) is False

    def test_accepts_a_password_longer_than_bcrypts_72_byte_limit(self):
        # Raw bcrypt raises ValueError past 72 bytes
        long_password = "a" * 200
        digest = security.hash_password(long_password)
        assert security.verify_password(long_password, digest) is True

    def test_long_passwords_sharing_a_72_byte_prefix_do_not_collide(self):
        # Raw bcrypt would truncate both to the same 72 bytes and accept either
        digest = security.hash_password("a" * 72 + "FIRST")
        assert security.verify_password("a" * 72 + "SECOND", digest) is False

    def test_multibyte_password_over_72_bytes_round_trips(self):
        password = "é" * 50  # 100 bytes once encoded
        digest = security.hash_password(password)
        assert security.verify_password(password, digest) is True


class TestLegacySha256:
    """The old scheme: unsalted hex SHA-256, still readable so nobody is locked out."""

    @staticmethod
    def legacy(password):
        return hashlib.sha256(password.encode()).hexdigest()

    def test_recognises_a_legacy_digest(self):
        assert security.is_legacy_hash(self.legacy("adminadmin")) is True

    def test_does_not_mistake_a_bcrypt_hash_for_a_legacy_one(self):
        assert security.is_legacy_hash(security.hash_password("adminadmin")) is False

    @pytest.mark.parametrize("value", ["", None, "abc", "z" * 64, "A" * 64, 64 * "0" + "0"])
    def test_rejects_near_misses(self, value):
        # Uppercase hex and wrong lengths are not digests this app ever wrote
        assert security.is_legacy_hash(value) is False

    def test_legacy_password_still_verifies(self):
        assert security.verify_password("adminadmin", self.legacy("adminadmin")) is True

    def test_wrong_legacy_password_is_rejected(self):
        assert security.verify_password("wrong", self.legacy("adminadmin")) is False

    def test_legacy_hash_needs_rehashing(self):
        assert security.needs_rehash(self.legacy("adminadmin")) is True

    def test_current_hash_does_not_need_rehashing(self):
        assert security.needs_rehash(security.hash_password("adminadmin")) is False

    def test_weaker_bcrypt_cost_needs_rehashing(self):
        weak = bcrypt.hashpw(security._prepare("x"), bcrypt.gensalt(rounds=4)).decode()
        assert security.needs_rehash(weak) is True

    @pytest.mark.parametrize("value", ["", None, "garbage", "$2b$notanumber$xyz"])
    def test_needs_rehash_is_safe_on_junk(self, value):
        assert security.needs_rehash(value) is False


class TestCost:

    def test_hashing_is_deliberately_slow(self):
        # A GPU can do billions of SHA-256 digests a second. bcrypt at this
        # cost should take a measurable fraction of a second per attempt.
        import time
        start = time.perf_counter()
        security.hash_password("timing-check")
        elapsed = time.perf_counter() - start
        assert elapsed > 0.01, f"hashing took {elapsed:.4f}s, work factor looks too low"
