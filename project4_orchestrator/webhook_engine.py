import hmac
import hashlib
from flask import Flask, request, jsonify
from config import Config

app = Flask(__name__)

def verify_signature(payload: str, signature: str, secret: str) -> bool:
    """Computes an expected HMAC-SHA256 hash to verify incoming webhook authenticity."""
    expected_signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_signature, signature)

@app.route("/webhook-receiver", methods=["POST"])
def receive_webhook():
    """Simulates a premium client endpoint that validates inbound task security signatures."""
    raw_payload = request.get_data(as_text=True)
    incoming_signature = request.headers.get("X-DTO-Signature")
    event_type = request.headers.get("X-DTO-Event", "UNKNOWN")

    if not incoming_signature:
        return jsonify({"status": "REJECTED", "reason": "Missing security signature header"}), 401

    # Cryptographically validate payload origins
    if not verify_signature(raw_payload, incoming_signature, Config.WEBHOOK_SECRET_SIGNING_KEY):
        return jsonify({"status": "REJECTED", "reason": "Invalid cryptographic signature signature mismatch"}), 403

    # Successfully validated
    data = request.get_json()
    print(f"🔒 [SECURITY VALIDATED] Received '{event_type}' for Task {data.get('task_id')}")
    print(f"📦 [DATA] Resulting Payload: {data.get('result')}\n")

    return jsonify({"status": "ACKNOWLEDGED", "message": "Signature verified securely"}), 200

if __name__ == "__main__":
    # Run receiver on port 5001 to avoid conflicting with the ingestion app
    app.run(host="0.0.0.0", port=5001, debug=True)
