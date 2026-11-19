import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from redis import Redis
from config import AnalyticsConfig

app = FastAPI(title="EDAA Live Analytics WebSocket Streamer")

redis_client = Redis(
    host=AnalyticsConfig.REDIS_HOST, 
    port=AnalyticsConfig.REDIS_PORT, 
    db=0, 
    decode_responses=True
)

@app.websocket("/ws/analytics")
async def websocket_endpoint(websocket: WebSocket):
    """Establishes real-time connection contexts to push computed metrics."""
    await websocket.accept()
    print("🔌 [WS CONNECTED] Client channel initialized for analytics pipeline.")
    
    try:
        while True:
            # Pull down the latest calculated window snapshot from Redis cache
            latest_stats_raw = redis_client.get(AnalyticsConfig.AGGREGATED_STATS_KEY)
            
            if latest_stats_raw:
                payload = json.loads(latest_stats_raw)
                await websocket.send_json(payload)
            else:
                await websocket.send_json({"message": "Awaiting initial metric data pipeline computations..."})
            
            # Match the engine's processing rate
            await asyncio.sleep(AnalyticsConfig.ENGINE_TICK_RATE_SEC)
            
    except WebSocketDisconnect:
        print("🔌 [WS DISCONNECTED] Client client dropped channel cleanly.")
    except Exception as e:
        print(f"❌ WebSocket tracking interface execution exception: {str(e)}")
