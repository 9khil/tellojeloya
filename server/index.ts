import { createId } from '@paralleldrive/cuid2'

const server = Bun.serve<{ id: string }>({
    fetch(req, server) {
        const upgrade = server.upgrade(req, {
            data: { id: createId() }
        })
        console.log(upgrade)
        return upgrade ? undefined : new Response('Handshake failed', { status: 400 })
    },
    websocket: {
        async message(ws, message) {
            server.publish("room", message)
            if (message.includes("room")) {
                // server.publish("room", JSON.stringify({ user: ws.data.id, message }))
            }
        },
        open(ws) {
            ws.subscribe("room")
            server.publish("room", JSON.stringify(ws.data.id + " joined the room"))
        },
        ping(ws, data) {
            console.log('PING')
        },
        pong(ws, data) {
            console.log('PONG')
        },
        sendPings: true
    }
})

console.log(`Listening on ${server.hostname}:${server.port}`)