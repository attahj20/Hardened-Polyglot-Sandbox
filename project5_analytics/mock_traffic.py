import time
import json
import random
import logging
from redis import Redis
from config import AnalyticsConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("EDAA-TrafficGen")

# Initialize connection back to the shared Redis infrastructure
redis_client = Redis(
    host=AnalyticsConfig.REDIS_HOST, 
    port=AnalyticsConfig.REDIS_PORT, 
    db=0, 
    decode_responses=True
)

def emit_mock_metric():
    """Generates a randomized performance packet and injects it into the Redis Sorted Set."""
    # Randomly select a metric category defined in our configuration
    metric_name = random.choice(AnalyticsConfig.METRIC_TYPES)
    
    # Simulate realistic performance variations based on metric type
    if metric_name == "cpu_utilization_pct":
        value = random.uniform(15.0, 95.0)  # CPU spikes can get high
    elif metric_name == "memory_rss_mb":
        value = random.uniform(2048.0, 8192.0)  # Standard RAM usage footprint
    else:  # request_latency_ms
        # Introduce occasional high-latency spikes to test max_spike captures
        value = random.uniform(10.0, 150.0) if random.random() > 0.05 else random.uniform(400.0, 1200.0)

    current_timestamp = time.time()
    
    # Construct standard event packet payload
    packet = {
        "metric_name": metric_name,
        "value": round(value, 2),
        "host_id": f"srv-node-0{random.randint(1, 4)}"
    }
    
    # Convert payload to clean JSON string
    serialized_packet = json.dumps(packet)
    
    # Append unique microsecond suffix to make the string strictly unique within ZSET
    unique_zset_member = f"{serialized_packet}::{current_timestamp}"

    # Pipeline structural addition directly using the timestamp as the score
    redis_client.zadd(AnalyticsConfig.METRICS_ZSET_KEY, {unique_zset_member: current_timestamp})

def run_simulation_loop():
    """Continuously pumps varying bundles of metric packets into the stream."""
    logger.info("⚡ EDAA High-Volume Traffic Generator active. Emitting data bursts...")
    
    try:
        while True:
            # Emit a random batch size of metrics per tick (between 5 and 25 packets)
            batch_size = random.randint(5, 25)
            for _ in range(batch_size):
                emit_mock_metric()
                
            logger.info(f"🚀 Dispatched batch of {batch_size} performance packets to Redis infrastructure.")
            
            # Throttle slightly to simulate steady-state continuous delivery
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        logger.info("Traffic generation loop halted cleanly.")

if __name__ == "__main__":
    run_simulation_loop()
