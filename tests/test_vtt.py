from cyber_talks.transcripts import _parse_vtt, _segments_to_text


def test_parse_vtt_basic():
    vtt = """WEBVTT

00:00:01.000 --> 00:00:03.000
Hello detection engineering

00:00:03.000 --> 00:00:05.500
from DEF CON
"""
    segs = _parse_vtt(vtt)
    assert len(segs) == 2
    assert segs[0].start == 1.0
    text = _segments_to_text(segs)
    assert "detection engineering" in text
    assert "DEF CON" in text
