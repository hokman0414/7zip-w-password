from cyber_talks.config import load_topic_config
from cyber_talks.filter import score_talk
from cyber_talks.models import TalkCandidate


def test_detection_engineering_match():
    cfg = load_topic_config()
    c = TalkCandidate(
        video_id="abcdefghijk",
        title="BSidesSF 2025 - How to Train Your Detection Dragon",
        url="https://www.youtube.com/watch?v=abcdefghijk",
        description="Building a detection and response pipeline with Sigma rules",
        channel="Security BSides SF",
        upload_date="20250501",
    )
    scored = score_talk(c, cfg, min_score=3.0)
    assert scored is not None
    assert scored.score >= 3.0
    topics = {t.topic for t in scored.topics}
    assert "detection_engineering" in topics


def test_noise_rejected():
    cfg = load_topic_config()
    c = TalkCandidate(
        video_id="xyzxyzxyzxy",
        title="Opening Remarks and Happy Hour",
        url="https://www.youtube.com/watch?v=xyzxyzxyzxy",
        description="Welcome to the party",
        upload_date="20250501",
    )
    assert score_talk(c, cfg, min_score=3.0) is None


def test_agentic_match():
    cfg = load_topic_config()
    c = TalkCandidate(
        video_id="agentic00001",
        title="DEF CON 32 - Agentic Workflows for the SOC",
        url="https://www.youtube.com/watch?v=agentic00001",
        description="Using LLM agents for alert triage and autonomous response",
        upload_date="20240812",
    )
    scored = score_talk(c, cfg, min_score=3.0)
    assert scored is not None
    assert any(t.topic == "agentic_workflows" for t in scored.topics)


def test_short_term_no_false_positive():
    cfg = load_topic_config()
    c = TalkCandidate(
        video_id="falseposit01",
        title="Capturing Packets for Fun",
        url="https://www.youtube.com/watch?v=falseposit01",
        description="A gentle introduction to adapting wifi adapters",
        upload_date="20250501",
    )
    # "apt" must not match inside "capturing" / "adapting"
    scored = score_talk(c, cfg, min_score=3.0)
    assert scored is None
