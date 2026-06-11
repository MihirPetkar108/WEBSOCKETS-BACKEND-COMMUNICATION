import WebSocket, { WebSocketServer } from "ws";

const port = 3000;

const relayServer = new WebSocketServer({ port });
console.log(`Connected to the Relay Server on port ${port}`);

const servers: WebSocket[] = [];

relayServer.on("connection", function connection(ws) {
  ws.on("error", console.error);

  servers.push(ws);

  ws.on("message", function message(data) {
    const { type } = JSON.parse(data.toString());

    if (type === "chat") {
      servers.forEach((socket) => {
        socket.send(data);
      });
    }
  });
});
