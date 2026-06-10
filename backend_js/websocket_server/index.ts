import WebSocket, { WebSocketServer } from "ws";

const port = 8081;

const wss = new WebSocketServer({ port });
console.log(`Connected to WebSocket Server on port:- ${port}`);

const relayPort = 3000;
const relaySocket = new WebSocket(`ws://localhost:${relayPort}`);

interface message {
    name: string;
    message: string;
}
interface Room {
    users: WebSocket[];
    messages: message[];
}

const Rooms: Record<string, Room> = {
    // roomId: {
    //     users: [ws1, ws2, ws3],
    //     content: [
    //          {
    //              "name": "Mihir",
    //              "message": "hi"
    //          },
    //          {
    //              "name": "Soham",
    //              "message": "hello"
    //          },
    //
    //      ]
    // }
};

relaySocket.onopen = function open() {
    console.log(`Connected to Relay Server on PORT ${relayPort}`);
};

relaySocket.onerror = function error(error) {
    console.log(`Relay Websocket error:- ${error.message}`);
};

relaySocket.onmessage = function message({data}) {
    const { type, roomId, name, content } = JSON.parse(data.toString());

    if (type === "chat") {
        if (!Rooms[roomId]) {
            console.log(`No room with roomId ${roomId} found!`);
            return;
        }

        const room = Rooms[roomId];

        room.messages.push({ name, message: content });

        room.users.map((socket) => {
            socket.send(
                `Message received from ${name} in roomId:- ${roomId} with content:- ${content}`,
            );
        });
    }
};

wss.on("connection", function connection(ws) {
    ws.on("error", console.error);

    ws.on("message", function messsage(data) {
        const { type, roomId } = JSON.parse(data.toString());

        if (type === "join") {
            if (!Rooms[roomId]) {
                Rooms[roomId] = {
                    users: [],
                    messages: [],
                };
            }

            relaySocket.send(data);

            Rooms[roomId].users.push(ws);

            ws.send(`User connected to room ${roomId}`);
        }

        if (type === "chat") {
            relaySocket.send(data);
        }

        if (type === "getChat") {
            const room = Rooms[roomId];
            if (!room) {
                console.log(`No room with roomId ${roomId} found!`);
                return;
            }

            const message = room.messages;
            console.log("GET CHAT MESSAGE:- ", message)
            ws.send(JSON.stringify(message));
        }
    });

    ws.send(`User connected to the WebSocket Server on port ${port}`);
});

