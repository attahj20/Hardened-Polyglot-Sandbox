import os

class Config:
    # Redis Broker Configuration
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    TASK_QUEUE_NAME = "dto_task_queue"
    
    # Task Execution Tuning
    MAX_RETRIES = 3
    RETRY_DELAY_SEC = 2
    WORKER_CONCURRENCY_LIMIT = 5  # Max concurrent asyncio tasks
    
    # Webhook Security
    # In production, keep this secret. Used to sign webhook payloads.
    WEBHOOK_SECRET_SIGNING_KEY = os.getenv("WEBHOOK_SECRET", "dto_super_secret_signing_token_2026")
