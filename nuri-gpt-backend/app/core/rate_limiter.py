"""Rate Limiter 인스턴스

slowapi Limiter를 별도 모듈에서 초기화하여
main.py와 엔드포인트 간의 순환 import를 방지합니다.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
