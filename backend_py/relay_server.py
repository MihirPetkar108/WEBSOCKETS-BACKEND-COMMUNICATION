import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

servers: list[WebSocket] = []

@app.websocket("/rs")
async def relaysocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    host, port = websocket.scope["server"]
    await websocket.send_text(json.dumps({
        "type": "connected",
        "host": host,
        "port": port
    }))

    servers.append(websocket)

    try:
        while True:
            message = await websocket.receive()

            print("Relay received:", message)

            if message["type"] == "websocket.disconnect":
                print("Server disconnected")
                break

            if "text" in message:
                data = message["text"]
            elif "bytes" in message:
                data = message["bytes"].decode("utf-8")
            else:
                print("Unknown message format:", message)
                continue

            parsedData = json.loads(data)

            if parsedData["type"] in ["join", "chat"]:
                print(
                    f"Broadcasting {parsedData['type']} to {len(servers)} backend server(s)"
                )

                for socket in servers:
                    await socket.send_text(data)

    except WebSocketDisconnect:
        print("Backend server disconnected from relay")
        if websocket in servers:
            servers.remove(websocket)
        print(f"Remaining backend servers: {len(servers)}")
