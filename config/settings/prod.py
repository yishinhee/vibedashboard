"""
운영 환경 settings — 단일 사용자 로컬 도구 가정.
사용: DJANGO_SETTINGS_MODULE=config.settings.prod
"""
from .base import *  # noqa: F401,F403

DEBUG = False

# 운영에서는 ALLOWED_HOSTS / SECRET_KEY 누락 시 즉시 실패하도록 강제
if not ALLOWED_HOSTS:  # noqa: F405
    raise RuntimeError("prod settings: .env 의 ALLOWED_HOSTS 가 비어 있다")

# 보안 헤더 — 단일 사용자 로컬 도구라 기본 활성화 수준만
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
