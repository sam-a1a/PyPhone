#Signup verification codes
"""
A one-time code is generated at signup, delivered to the user as a system
notification, and typed back in before the account is created. Nothing is
written to the database until the code checks out.

Codes live in memory for the life of the process. They are short-lived by
design, so there is nothing worth persisting across a restart: a signup that
was interrupted starts over.
"""
import hmac
import secrets
import time

CODE_LENGTH = 6
CODE_TTL_SECONDS = 600      # 10 minutes
MAX_ATTEMPTS = 5            # wrong guesses before the code is burned
RESEND_COOLDOWN_SECONDS = 30

# Outcomes of a verify() call, so the screen can say what actually went wrong
OK = "ok"
INCORRECT = "incorrect"
EXPIRED = "expired"
NO_CODE = "no_code"
TOO_MANY_ATTEMPTS = "too_many_attempts"

MESSAGES = {
    INCORRECT: "That code is not right",
    EXPIRED: "That code has expired. Request a new one",
    NO_CODE: "Request a code first",
    TOO_MANY_ATTEMPTS: "Too many attempts. Request a new code",
}


def generate_code() -> str:
    #A CODE_LENGTH-digit code, zero-padded so 42 reads as 000042
    return f"{secrets.randbelow(10 ** CODE_LENGTH):0{CODE_LENGTH}d}"


class _PendingCode:

    def __init__(self, code, issued_at):
        self.code = code
        self.issued_at = issued_at
        self.attempts = 0


class VerificationService:
    """Issues and checks signup codes, keyed by email.

    The clock is injectable so expiry can be tested without waiting.
    """

    def __init__(self, clock=time.monotonic):
        self._clock = clock
        self._pending = {}

    @staticmethod
    def _key(email):
        # Emails are matched case-insensitively, as they are everywhere else
        return (email or "").strip().lower()

    def send_code(self, email) -> str:
        #Issue a fresh code, replacing any code already outstanding
        code = generate_code()
        self._pending[self._key(email)] = _PendingCode(code, self._clock())
        return code

    def has_pending_code(self, email) -> bool:
        return self._key(email) in self._pending

    def peek_code(self, email):
        #The outstanding code, or None. For redisplaying the notification
        pending = self._pending.get(self._key(email))
        return pending.code if pending else None

    def seconds_until_resend(self, email) -> int:
        #How long the user must wait before asking for another code
        pending = self._pending.get(self._key(email))
        if pending is None:
            return 0
        elapsed = self._clock() - pending.issued_at
        return max(0, int(RESEND_COOLDOWN_SECONDS - elapsed))

    def can_resend(self, email) -> bool:
        return self.seconds_until_resend(email) == 0

    def verify(self, email, code) -> str:
        #Check a code. Returns one of the outcome constants above
        key = self._key(email)
        pending = self._pending.get(key)

        if pending is None:
            return NO_CODE

        if self._clock() - pending.issued_at > CODE_TTL_SECONDS:
            del self._pending[key]
            return EXPIRED

        if pending.attempts >= MAX_ATTEMPTS:
            del self._pending[key]
            return TOO_MANY_ATTEMPTS

        # compare_digest, not ==, so the comparison time gives nothing away
        if hmac.compare_digest(str(code or ""), pending.code):
            del self._pending[key]
            return OK

        pending.attempts += 1
        if pending.attempts >= MAX_ATTEMPTS:
            del self._pending[key]
            return TOO_MANY_ATTEMPTS
        return INCORRECT

    def clear(self, email):
        #Abandon an outstanding code, e.g. the user backed out of signup
        self._pending.pop(self._key(email), None)

    def clear_all(self):
        self._pending.clear()


# The app shares one service; screens import this rather than building their own
verification = VerificationService()
