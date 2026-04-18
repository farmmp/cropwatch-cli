import pytest
from cropwatch.anomaly import detect_anomalies, format_anomalies, AnomalyError


def _records(values):
    return [{"week_ending": f"2024-0{i+1}-01", "value": v} for i, v in enumerate(values)]


def test_detect_no_anomalies_uniform():
    records = _records([50, 50, 50, 50, 50])
    result = detect_anomalies(records, "value")
    assert result == []


def test_detect_finds_outlier():
    records = _records([50, 51, 49, 50, 95])
    result = detect_anomalies(records, "value", threshold=1.5)
    assert len(result) == 1
    assert result[0].value == 95


def test_detect_negative_outlier():
    records = _records([50, 51, 49, 50, 2])
    result = detect_anomalies(records, "value", threshold=1.5)
    assert len(result) == 1
    assert result[0].value == 2


def test_empty_records_raises():
    with pytest.raises(AnomalyError, match="No records"):
        detect_anomalies([], "value")


def test_no_numeric_raises():
    records = [{"week_ending": "2024-01-01", "value": "n/a"}]
    with pytest.raises(AnomalyError, match="No numeric"):
        detect_anomalies(records, "value")


def test_missing_key_skipped():
    records = [{"week_ending": "2024-01-01"}] + _records([50, 51, 49, 50, 95])
    result = detect_anomalies(records, "value", threshold=1.5)
    assert any(a.value == 95 for a in result)


def test_format_no_anomalies():
    assert format_anomalies([], "value") == "No anomalies detected."


def test_format_contains_week():
    records = _records([50, 51, 49, 50, 95])
    anomalies = detect_anomalies(records, "value", threshold=1.5)
    out = format_anomalies(anomalies, "value")
    assert "Week" in out
    assert "95" in out


def test_deviation_stored():
    records = _records([50, 51, 49, 50, 95])
    anomalies = detect_anomalies(records, "value", threshold=1.5)
    assert anomalies[0].deviation > 1.5
