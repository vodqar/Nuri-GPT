"""
메인 애플리케이션 테스트
"""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """루트 엔드포인트 헬스체크 테스트"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "Nuri-GPT"
    assert "version" in data
    assert "timestamp" in data


def test_health_endpoint(client: TestClient):
    """헬스체크 엔드포인트 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "Nuri-GPT"
    assert "version" in data
    assert "timestamp" in data
    assert "uptime_seconds" in data


def test_api_docs_accessible(client: TestClient):
    """API 문서 접근성 테스트 (개발 모드)"""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
