from cyber_talks.attribution import extract_speakers
from cyber_talks.models import TalkCandidate


def test_speaker_from_dash_title():
    c = TalkCandidate(
        video_id="abcdefghijk",
        title="Detection Engineering Demystified - David French",
        url="https://www.youtube.com/watch?v=abcdefghijk",
    )
    speakers = extract_speakers(c)
    assert any(s.name and "David French" in s.name for s in speakers)


def test_speaker_from_colon_conf_title():
    c = TalkCandidate(
        video_id="abcdefghijk",
        title="UniCon 2024: Zack Allen - Detection Engineering Trends",
        url="https://www.youtube.com/watch?v=abcdefghijk",
    )
    speakers = extract_speakers(c)
    assert any(s.name and "Zack Allen" in s.name for s in speakers)
    assert not any(s.name and "Detection Engineering" in (s.name or "") for s in speakers)


def test_speaker_from_description():
    c = TalkCandidate(
        video_id="abcdefghijk",
        title="Threat Hunting at Scale",
        url="https://www.youtube.com/watch?v=abcdefghijk",
        description="Speaker: Jane Doe\nTrack: Blue",
    )
    speakers = extract_speakers(c)
    assert any(s.name == "Jane Doe" for s in speakers)


def test_registry_size():
    from cyber_talks.config import load_conferences

    confs = load_conferences()
    assert len(confs) >= 100
