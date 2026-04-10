"""Generate API 스모크 테스트"""


def test_generate_routes_registered(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/generate/log" in paths
