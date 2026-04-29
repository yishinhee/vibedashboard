"""
개발 환경 settings — 로컬 개발용.
사용: DJANGO_SETTINGS_MODULE=config.settings.dev (.env 또는 manage.py 기본값)
"""
from .base import *  # noqa: F401,F403

# .env 의 DEBUG/ALLOWED_HOSTS 를 그대로 사용하되, 안전망으로 dev 기본값 보장
DEBUG = True

if not ALLOWED_HOSTS:  # noqa: F405 — base 에서 import
    ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Django 디버그 도구 설정 (debug-toolbar 도입 시 INTERNAL_IPS 활용)
INTERNAL_IPS = ["127.0.0.1"]
