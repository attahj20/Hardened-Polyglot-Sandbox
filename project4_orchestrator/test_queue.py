import json
import uuid
from redis import Redis
from config import Config

def inject_test_tasks():
    redis_client = Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=0, decode_responses=True)
    
    tasks = [
        {
            "task_id": str(uuid.uuid4()),
            "type": "math_compute",
            "payload": {"numbers": [12, 45, 78, 23]},
            "webhook_url": "http://127.0.0.1:5001",
            "retries": 0
        },
        {
            "task_id": str(uuid.uuid4()),
            "type": "video_transcode",
            "payload": {"duration_sec": 3},
            "webhook_url": "http://127.0.0.1:5001",
            "retries": 0
        }
    ]
    
    print("🚀 Connecting to Redis broker...")
    for task in tasks:
        redis_client.lpush(Config.TASK_QUEUE_NAME, json.dumps(task))
        print(f"✅ Enqueued Task {task['task_id']} of type [{task['type']}]")

if __name__ == "__main__":
    inject_test_tasks()
