import os

class AnalyticsConfig:
    # Infrastructure Core
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    
    # Storage Namespace / Keys
    METRICS_ZSET_KEY = "edaa:stream:time_series"
    AGGREGATED_STATS_KEY = "edaa:stats:latest"
    
    # Sliding Window Configurations
    WINDOW_SIZE_SECONDS = 60  # Only process the last 1 minute of data
    ENGINE_TICK_RATE_SEC = 1.0  # Recalculate metrics every second
    
    # Targeted Metric Categories
    METRIC_TYPES = ["cpu_utilization", "clickstream_event", "transaction_value"]
