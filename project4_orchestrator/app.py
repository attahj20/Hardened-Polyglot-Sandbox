import json
import uuid
from flask import Flask, request, jsonify
from redis import Redis
from config import Config

app = Flask(__name__)

# Initialize the Redis connection for task ingestion
redis_client = Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=0, decode_responses=True)

@app.route("/api/v1/tasks", methods=["POST"])
def ingest_task():
    """Accepts task payloads and instantly queues them into the Redis FIFO pipeline."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Missing JSON request body"}), 400

        task_type = data.get("type")
        payload = data.get("payload")
        webhook_url = data.get("webhook_url")

        # Validate mandatory structural fields
        if not task_type or payload is None:
            return jsonify({"status": "error", "message": "Missing required fields: 'type' or 'payload'"}), 400

        # Construct the internal task envelope
        task_id = str(uuid.uuid4())
        task_envelope = {
            "task_id": task_id,
            "type": task_type,
            "payload": payload,
            "webhook_url": webhook_url,
            "retries": 0
        }

        # Push token instantly to the left of the list (LPUSH)
        # The worker fetches from the right (RPOP), achieving strict FIFO behavior
        redis_client.lpush(Config.TASK_QUEUE_NAME, json.dumps(task_envelope))

        return jsonify({
            "status": "QUEUED",
            "task_id": task_id,
            "message": f"Task of type '{task_type}' successfully enqueued."
        }), 202

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/v1/health", methods=["GET"])
def health_check():
    """Verifies API health and tests broker connection."""
    try:
        redis_client.ping()
        queue_depth = redis_client.llen(Config.TASK_QUEUE_NAME)
        return jsonify({
            "status": "HEALTHY",
            "broker_connected": True,
            "backlog_count": queue_depth
        }), 200
    except Exception as e:
        return jsonify({
            "status": "UNHEALTHY",
            "broker_connected": False,
            "error": str(e)
        }), 500

if __name__ == "__main__":
    # Standard engineering debug port
    app.run(host="0.0.0.0", port=5000, debug=True)
