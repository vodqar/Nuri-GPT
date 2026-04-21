"""
pytest 설정 및 픽스처
"""

import os

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

# 테스트 환경에서 DEBUG 모드 활성화 (API 문서 접근용)
os.environ["DEBUG"] = "True"

from app.main import app

# 테스트 환경에서 Rate Limiter 비활성화
from app.core.rate_limiter import limiter
limiter.enabled = False


@pytest.fixture
def client():
    """FastAPI 테스트 클라이언트 픽스처"""
    return TestClient(app)


@pytest.fixture
def mock_journal_repo():
    """JournalRepository mock 픽스처"""
    return MagicMock()
