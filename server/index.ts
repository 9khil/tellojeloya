const DRONES = "drones" as const
const FE = "fe" as const

type FromFeToDrone = {
    id: string
    action: string
    duration: number
}

const server = Bun.serve<{ id: string, type: string }>({
    fetch(req, server) {
        const url = new URL(req.url)
        const clientId = url.searchParams.get('clientId')
        const type = url.searchParams.get('type')
        const upgrade = server.upgrade(req, {
            data: { id: clientId, type }
        })
        return upgrade ? undefined : new Response('Handshake failed', { status: 400 })
    },
    websocket: {
        async message(ws, message) {
            if (ws.isSubscribed(DRONES)) {
                server.publish(FE, message)
            }
            if (ws.isSubscribed(FE)) {
                if (message.includes("1")) {
                    server.publish("1", message)
                }
                if (message.includes("2")) {
                    server.publish("2", message)
                }
            } else {
                server.publish(DRONES, message)
            }
        },
        open(ws) {
            if (ws.data.type == DRONES) {
                ws.subscribe(DRONES)
                ws.subscribe(ws.data.id)
                server.publish(DRONES, JSON.stringify(ws.data.id + " joined drones"))
            }
            if (ws.data.type == FE) {
                ws.subscribe(FE)
                server.publish(FE, JSON.stringify(ws.data.id + " joined FE"))
            }
        },
        close(ws, code, reason) {
            if (ws.isSubscribed(DRONES)) {
                server.publish(DRONES, `Lost connection with ${ws.data.id}, reason: ${reason}`)
            }
        },
        ping(ws, data) {
            console.log('PING')
        },
        pong(ws, data) {
            console.log('PONG')
        },
        sendPings: true,
    }
})

console.log(`Listening on http://${server.hostname}:${server.port}`)