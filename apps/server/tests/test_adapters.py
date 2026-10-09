import os
from app.core.credentials import (
    save_credential,
    get_credential,
    delete_credential,
    has_credential,
    mask_credential,
)
from app.adapters.heuristic import HeuristicExtractor
from app.adapters.manager import (
    get_active_provider_name,
    set_active_provider_name,
    get_model_settings,
    extract_tasks_from_context,
)


def test_credentials_management(tmp_path, monkeypatch):
    monkeypatch.setenv("LEAVES_DATA_DIR", str(tmp_path))
    assert not has_credential("openai")
    save_credential("openai", "sk-proj-1234567890abcdef")
    assert has_credential("openai")
    assert get_credential("openai") == "sk-proj-1234567890abcdef"
    assert mask_credential(get_credential("openai")) == "sk-...cdef"
    assert delete_credential("openai")
    assert not has_credential("openai")


def test_heuristic_extractor():
    extractor = HeuristicExtractor()
    sample = [
        {
            "source_type": "markdown",
            "source_ref": "/test/notes.md",
            "title": "Meeting Notes",
            "content": """
            # Project Notes
            - [ ] Submit quarterly tax report today
            TODO: Review pull request from teammate
            Action Item: Prepare slides for tomorrow
            """,
        }
    ]
    tasks = extractor.extract_tasks_and_urgency(sample)
    assert len(tasks) >= 3
    titles = [t["title"] for t in tasks]
    assert any("tax report" in t.lower() for t in titles)
    assert any("pull request" in t.lower() for t in titles)
    assert any("slides" in t.lower() for t in titles)
    # Check urgency scoring
    for t in tasks:
        assert 1 <= t["urgency_score"] <= 10
        assert t["urgency_reason"]
        assert t["suggested_duration_minutes"] > 0


def test_active_provider_selection():
    set_active_provider_name("heuristic")
    assert get_active_provider_name() == "heuristic"
    set_active_provider_name("openai")
    assert get_active_provider_name() == "openai"
    settings = get_model_settings()
    assert settings["active_provider"] == "openai"
    assert "openai" in settings["providers"]
    assert "heuristic" in settings["providers"]
