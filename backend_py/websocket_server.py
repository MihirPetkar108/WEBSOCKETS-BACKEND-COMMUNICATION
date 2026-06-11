import json
from contextlib import asynccontextmanager
import asyncio
import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict

relay_socket = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global relay_socket

    relay_socket = await websockets.connect("ws://localhost:3000")
    # relay_socket = await websockets.connect("ws://127.0.0.1:3000/rs")
    relay_listener_task = asyncio.create_task(listen_to_relay())
    print("Connected to relay server at ws://127.0.0.1:3000/rs")

    yield

    relay_listener_task.cancel()
    await relay_socket.close()


app = FastAPI(lifespan=lifespan)


class Message(BaseModel):
    name: str
    message: str


class Room(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    users: list[WebSocket]
    messages: list[Message]


Rooms: dict[str, Room] = {
    # roomId: {
    #     users: [ws1, ws2, ws3]
    #     messages: [
    #         {
    #             "name": "Mihir",
    #             "message": "Hi"
    #         },
    #         {
    #             "name": "Soham",
    #             "message": "Hello"
    #         }
    #     ]
    # }
}


async def listen_to_relay():
    while True:
        try:
            if relay_socket is None:
                return

            data = await relay_socket.recv()

            if isinstance(data, bytes):
                data = data.decode()

            try:
                parsedData = json.loads(data)
            except json.JSONDecodeError:
                print("Ignoring non-JSON relay message:", data)
                continue

            if not isinstance(parsedData, dict):
                print("Ignoring unexpected payload:", parsedData)
                continue

            roomId = parsedData["roomId"]
            name = parsedData["name"]
            content = parsedData["content"]

            if roomId not in Rooms:
                print(f"Room {roomId} not found on this backend server")
                continue

            message = Message(name=name, message=content)

            Rooms[roomId].messages.append(message)

            for socket in Rooms[roomId].users:
                await socket.send_text(f"Message received from {name} in roomId:- {roomId} with content:- {content}")
        except Exception as e: 
            print("LISTENER ERROR:", repr(e))
            raise


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    host, port = websocket.scope["server"]
    await websocket.send_text(f"Websocket connected on {host}:{port}")
    print(f"Websocket connected on {host}:{port}")

    try:
        while True:
            data = await websocket.receive_text()

            parsedData = json.loads(data)

            type = parsedData["type"]
            roomId = parsedData["roomId"]

            if type == "join":

                if roomId not in Rooms:
                    Rooms[roomId] = Room(users=[], messages=[])

                Rooms[roomId].users.append(websocket)
                await websocket.send_text(f"User connected to roomId:- {roomId}")

            if type == "chat":
                if relay_socket == None:
                    return

                await relay_socket.send(data)

            if type == "getChat":
                message = Rooms[roomId].messages
                await websocket.send_text(json.dumps([msg.model_dump() for msg in message]))

    except WebSocketDisconnect:
        for room in Rooms.values():
            if websocket in room.users:
                room.users.remove(websocket)
