import time
import json
import logging
from redis import Redis
from config import AnalyticsConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("EDAA-Engine")

redis_client = Redis(
    host=AnalyticsConfig.REDIS_HOST, 
    port=AnalyticsConfig.REDIS_PORT, 
    db=0, 
    decode_responses=True
)

def compute_sliding_aggregates():
    """Calculates real-time math metrics across a moving 60-second window."""
    current_time = time.time()
    boundary_time = current_time - AnalyticsConfig.WINDOW_SIZE_SECONDS

    try:
        # 1. Purge stale records older than our 60-second window limit
        dropped_elements = redis_client.zremrangebyscore(
            AnalyticsConfig.METRICS_ZSET_KEY, 
            "-inf", 
            boundary_time
        )
        if dropped_elements > 0:
            logger.info(f"🧹 Cleaned {dropped_elements} expired metrics from the sliding window.")

        # 2. Extract all elements currently remaining inside the valid window
        active_metrics = redis_client.zrangebyscore(
            AnalyticsConfig.METRICS_ZSET_KEY, 
            boundary_time, 
            "+inf"
        )

        # Initialize bucket states for mathematical aggregation
        stats_collector = {m: {"count": 0, "total_value": 0.0, "max_spike": 0.0} for m in AnalyticsConfig.METRIC_TYPES}
        
        # 3. Parse active packets and compute raw totals
        for item in active_metrics:
            # Strip out unique timestamp suffix added during ingestion
            raw_json = item.split("::")[0]
            packet = json.loads(raw_json)
            
            name = packet.get("metric_name")
            value = float(packet.get("value", 0))

            if name in stats_collector:
                stats_collector[name]["count"] += 1
                stats_collector[name]["total_value"] += value
                if value > stats_collector[name]["max_spike"]:
                    stats_collector[name]["max_spike"] = value

        # 4. Formulate finalized analytics output payload
        computed_summary = {
            "window_meta": {
                "window_size_sec": AnalyticsConfig.WINDOW_SIZE_SECONDS,
                "recalculated_at": current_time,
                "total_active_events": len(active_metrics)
            },
            "metrics": {}
        }

        for metric_name, raw_data in stats_collector.items():
            count = raw_data["count"]
            avg = raw_data["total_value"] / count if count > 0 else 0.0
            
            computed_summary["metrics"][metric_name] = {
                "event_count": count,
                "moving_average": round(avg, 2),
                "max_value_spike": round(raw_data["max_spike"], 2)
            }

        # 5. Commit computed map to Redis for streaming broadcasts
        redis_client.set(AnalyticsConfig.AGGREGATED_STATS_KEY, json.dumps(computed_summary))
        logger.info(f"📊 Recalculated moving matrix metrics. Active volume: {len(active_metrics)} items.")

    except Exception as e:
        logger.error(f"Engine computation cycle fault: {str(e)}")

def main_loop():
    logger.info("EDAA Sliding-Window Aggregator active. Polling data loops...")
    while True:
        compute_sliding_aggregates()
        time.sleep(AnalyticsConfig.ENGINE_TICK_RATE_SEC)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        logger.info("Analytics computation loop terminated cleanly.")
