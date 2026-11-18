from datetime import datetime, timezone
from types import SimpleNamespace

from silent_stocks.config import Settings
from silent_stocks.feedback import update_feedback


def _report(ticker, leading, survives):
    return SimpleNamespace(ticker=ticker, techniques=[
        SimpleNamespace(technique="Analysis of Competing Hypotheses", details={"leading": leading}),
        SimpleNamespace(technique="Red Team Analysis", details={"survives": survives}),
    ])


def test_feedback_loop_records_hypothesis_and_correlation_changes(tmp_path):
    settings = Settings(data_dir=tmp_path)
    now = datetime(2026, 11, 18, tzinfo=timezone.utc)

    class Holding:
        def __init__(self, symbol, weight):
            self.symbol, self.weight, self.value = symbol, weight, 100.0

    risk = {"holdings": [Holding("BIG", 0.5), Holding("IDX", 0.2)],
            "correlation_pairs": [{"a": "BIG", "b": "IDX", "corr": 0.40}]}
    first = update_feedback(settings, [_report("BIG", "H1", True), _report("IDX", "H2", True)], risk, now)
    assert "First SAT feedback" in first["notes"][0]
    risk["correlation_pairs"] = [{"a": "BIG", "b": "IDX", "corr": 0.81}]
    second = update_feedback(settings, [_report("BIG", "H3", False), _report("IDX", "H2", True)], risk, now)
    text = " ".join(second["notes"])
    assert "BIG ACH leading hypothesis H1 -> H3" in text
    assert "BIG red team now defeats the thesis" in text
    assert "BIG-IDX" in text and "0.75" in text
    assert "do not create an order" in text
