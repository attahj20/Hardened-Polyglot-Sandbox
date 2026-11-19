import json
import time
import pytest
from unittest.mock import patch
from config import AnalyticsConfig
import engine

@patch("engine.redis_client")
def test_compute_sliding_aggregates_math(mock_redis):
    """Verifies averages, event counts, and max spikes across active metrics."""
    now = time.time()
    metric_a = AnalyticsConfig.METRIC_TYPES[0]  # e.g. "cpu_utilization"
    metric_b = AnalyticsConfig.METRIC_TYPES[1]  # e.g. "clickstream_event"

    # Simulate two metric_a packets and one metric_b spike returned by Redis ZSET
    mock_active_items = [
        f'{json.dumps({"metric_name": metric_a, "value": 40.0})}::{now - 5}',
        f'{json.dumps({"metric_name": metric_a, "value": 80.0})}::{now - 2}',
        f'{json.dumps({"metric_name": metric_b, "value": 512.5})}::{now - 1}',
    ]

    mock_redis.zremrangebyscore.return_value = 2
    mock_redis.zrangebyscore.return_value = mock_active_items

    engine.compute_sliding_aggregates()

    # Ensure stale records were purged
    mock_redis.zremrangebyscore.assert_called_once()

    # Extract the JSON payload saved to Redis
    mock_redis.set.assert_called_once()
    saved_key, saved_json_str = mock_redis.set.call_args[0]
    assert saved_key == AnalyticsConfig.AGGREGATED_STATS_KEY

    result = json.loads(saved_json_str)

    # Verify total event count
    assert result["window_meta"]["total_active_events"] == 3

    # Verify metric_a math (avg of 40 and 80 = 60, max = 80)
    stats_a = result["metrics"][metric_a]
    assert stats_a["event_count"] == 2
    assert stats_a["moving_average"] == 60.0
    assert stats_a["max_value_spike"] == 80.0

    # Verify metric_b spike capture
    stats_b = result["metrics"][metric_b]
    assert stats_b["event_count"] == 1
    assert stats_b["moving_average"] == 512.5
    assert stats_b["max_value_spike"] == 512.5

@patch("engine.redis_client")
def test_compute_sliding_aggregates_empty_window(mock_redis):
    """Ensures zero-division is prevented when no events exist in the window."""
    mock_redis.zremrangebyscore.return_value = 0
    mock_redis.zrangebyscore.return_value = []

    engine.compute_sliding_aggregates()

    _, saved_json_str = mock_redis.set.call_args[0]
    result = json.loads(saved_json_str)

    assert result["window_meta"]["total_active_events"] == 0
    for metric in AnalyticsConfig.METRIC_TYPES:
        assert result["metrics"][metric]["event_count"] == 0
        assert result["metrics"][metric]["moving_average"] == 0.0
        assert result["metrics"][metric]["max_value_spike"] == 0.0
