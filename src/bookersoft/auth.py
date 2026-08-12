import threading
import time

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from bookersoft.config import SESSION_MAX_AGE_SECONDS, SESSION_SECRET

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        _password_hasher.verify(password_hash, password)
        return True
    except (VerifyMismatchError, VerificationError):
        return False


def _serializer() -> URLSafeTimedSerializer:
    if not SESSION_SECRET:
        raise RuntimeError("SESSION_SECRET environment variable is not set")
    return URLSafeTimedSerializer(SESSION_SECRET, salt="bookersoft-session")


def create_session_token(user_id: int) -> str:
    return _serializer().dumps({"user_id": user_id})


def read_session_token(token: str) -> int | None:
    try:
        data = _serializer().loads(token, max_age=SESSION_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
    return data.get("user_id")


# Rate limiting: in-memory, keyed by client IP. Resets on process restart,
# which is an acceptable tradeoff for a personal library, not a bank.
MAX_LOGIN_ATTEMPTS = 5
LOGIN_ATTEMPT_WINDOW_SECONDS = 15 * 60

_failed_attempts: dict[str, list[float]] = {}
_failed_attempts_lock = threading.Lock()


def _prune(ip: str) -> None:
    cutoff = time.monotonic() - LOGIN_ATTEMPT_WINDOW_SECONDS
    attempts = _failed_attempts.get(ip)
    if attempts is not None:
        _failed_attempts[ip] = [t for t in attempts if t > cutoff]


def is_rate_limited(ip: str) -> bool:
    with _failed_attempts_lock:
        _prune(ip)
        return len(_failed_attempts.get(ip, [])) >= MAX_LOGIN_ATTEMPTS


def record_failed_login(ip: str) -> None:
    with _failed_attempts_lock:
        _prune(ip)
        _failed_attempts.setdefault(ip, []).append(time.monotonic())


def clear_failed_logins(ip: str) -> None:
    with _failed_attempts_lock:
        _failed_attempts.pop(ip, None)
