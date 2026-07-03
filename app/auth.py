import os
import time
import hmac
import hashlib

# --- Configuration (from environment) ---
# ACCESS_PASSWORD: 친구들과 공유하는 공용 비밀번호. 비어 있으면 인증이 완전히 비활성화된다.
ACCESS_PASSWORD = os.environ.get("ACCESS_PASSWORD", "")
# SECRET_KEY: 쿠키 서명용 키. 지정하지 않아도 동작하지만, 지정하면 엔트로피가 늘어난다.
SECRET_KEY = os.environ.get("SECRET_KEY", "cyber-topgoal-default-secret")
# COOKIE_SECURE: HTTPS로 서비스할 때만 true 로 두면 쿠키가 HTTP로는 전송되지 않는다.
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() in ("1", "true", "yes")

COOKIE_NAME = "tg_auth"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1 year

# 비밀번호가 설정되어 있을 때만 인증을 활성화한다 (로컬 개발/기존 동작 보존).
AUTH_ENABLED = bool(ACCESS_PASSWORD)


def _secret() -> bytes:
    """서명 키. 비밀번호를 포함시켜, 비밀번호가 바뀌면 기존 쿠키가 자동으로 무효화되도록 한다."""
    return (SECRET_KEY + "|" + ACCESS_PASSWORD).encode("utf-8")


def _sign(payload: str) -> str:
    return hmac.new(_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def make_token() -> str:
    """만료 시각과 서명을 담은 쿠키 토큰을 생성한다."""
    expiry = str(int(time.time()) + COOKIE_MAX_AGE)
    return f"{expiry}.{_sign(expiry)}"


def verify_token(token: str | None) -> bool:
    """쿠키 토큰의 서명과 만료 여부를 검증한다."""
    if not token or "." not in token:
        return False
    payload, sig = token.rsplit(".", 1)
    if not hmac.compare_digest(sig, _sign(payload)):
        return False
    try:
        return int(payload) >= int(time.time())
    except ValueError:
        return False


def check_password(password: str) -> bool:
    """입력한 비밀번호가 공용 비밀번호와 일치하는지 상수 시간 비교로 확인한다."""
    if not ACCESS_PASSWORD:
        return True
    return hmac.compare_digest(password or "", ACCESS_PASSWORD)
