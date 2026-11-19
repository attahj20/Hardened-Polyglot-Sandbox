import asyncio
import json
import websockets

WS_URL = "ws://127.0.0.1:8000/ws/analytics"

async def listen_to_stream():
    print(f"📡 Connecting to EDAA WebSocket stream at {WS_URL}...")
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("✅ Connected! Receiving live sliding-window updates (Press Ctrl+C to stop):\n")
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                print(json.dumps(data, indent=2))
                print("-" * 50)
    except ConnectionRefusedError:
        print("❌ Connection refused. Make sure Uvicorn is running on port 8000.")
    except KeyboardInterrupt:
        print("\n🔌 Disconnected from stream cleanly.")

if __name__ == "__main__":
    asyncio.run(listen_to_stream())
