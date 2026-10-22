from app.dork_engine import SearchParams, generate_dorks


def test_preset_fills_empty_titles_on_api():
    params = SearchParams(preset_id="cybersecurity")
    assert params.titles
    assert "Security Engineer" in params.titles or any(
        "Security" in t for t in params.titles
    )


def test_preset_fills_skills_when_empty():
    params = SearchParams(preset_id="cybersecurity", title="Analyst")
    assert params.skills
    assert any(s.lower() == "siem" for s in params.skills)


def test_preset_does_not_override_user_titles():
    params = SearchParams(preset_id="cybersecurity", titles=["Custom Role"])
    assert params.titles == ["Custom Role"]
