import json
import re

from fastapi.testclient import TestClient

from app.main import _cv_requests, app

client = TestClient(app)


def test_index_bootstraps_presets_for_first_paint():
    response = client.get("/")
    assert response.status_code == 200
    assert "no-cache" in response.headers.get("cache-control", "")
    match = re.search(
        r'<script type="application/json" id="preset-bootstrap">(.*?)</script>',
        response.text,
        re.S,
    )
    assert match, "preset bootstrap block is missing"
    presets = json.loads(match.group(1))
    assert len(presets) == 16
    assert any(preset["id"] == "data" and preset["titles"] for preset in presets)
    assert "<!--PRESET_BOOTSTRAP-->" not in response.text


def test_index_bootstrap_escapes_script_breakout(monkeypatch):
    hostile = "</script><script>alert(1)</script>"
    monkeypatch.setattr(
        "app.main.list_domain_presets",
        lambda: [{"id": "x", "name": hostile, "titles": ["Engineer"]}],
    )
    response = client.get("/")
    marker = 'id="preset-bootstrap">'
    start = response.text.index(marker) + len(marker)
    payload = response.text[start : response.text.index("</script>", start)]
    assert "</" not in payload
    assert json.loads(payload)[0]["name"] == hostile


def test_preset_only_request_is_accepted():
    response = client.post("/api/dorks", json={"preset_id": "data"})
    assert response.status_code == 200
    body = response.json()
    assert body["params"]["titles"]
    assert body["categories"]


def test_seven_titles_are_trimmed_instead_of_rejected():
    response = client.post(
        "/api/dorks", json={"titles": [f"Title {i}" for i in range(7)]}
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["params"]["titles"]) == 6
    assert any("first 6 job titles" in warning for warning in body["warnings"])


def test_long_title_is_shortened_instead_of_rejected():
    response = client.post("/api/dorks", json={"title": "A" * 201})
    assert response.status_code == 200
    body = response.json()
    assert len(body["params"]["title"]) == 120
    assert any("shortened to 120" in warning for warning in body["warnings"])


def test_missing_title_returns_actionable_400():
    response = client.post("/api/dorks", json={})
    assert response.status_code == 400
    assert "job title" in response.json()["detail"].lower()


def test_unknown_preset_returns_400():
    response = client.post("/api/dorks", json={"preset_id": "nope"})
    assert response.status_code == 400
    assert "Unknown domain preset" in response.json()["detail"]


def test_unknown_ats_returns_400():
    response = client.post(
        "/api/dorks", json={"title": "Engineer", "ats_platforms": ["nope"]}
    )
    assert response.status_code == 400
    assert "Unknown ATS" in response.json()["detail"]


def test_wrong_field_type_returns_422_detail_array():
    response = client.post("/api/dorks", json={"titles": "Engineer"})
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)


def test_cv_upload_rate_limit():
    _cv_requests.clear()
    files = {
        "cv": (
            "cv.txt",
            b"Jane Doe\nPython Developer\nSkills\nPython, Docker\n",
            "text/plain",
        )
    }
    try:
        for _ in range(20):
            response = client.post("/api/cv/parse", files=files)
            assert response.status_code == 200
        blocked = client.post("/api/cv/parse", files=files)
        assert blocked.status_code == 429
        assert "Too many CV uploads" in blocked.json()["detail"]
    finally:
        _cv_requests.clear()
