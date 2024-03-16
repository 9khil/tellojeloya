const DRONES = "drones" as const
const FE = "fe" as const

type MsgFromFeToDrone = {
    id: string
    type: string
    duration: number
}

type MsgToDrone = {
    type: string
    duration: number
}

const server = Bun.serve<{ id: string, type: string }>({
    fetch(req, server) {
        const url = new URL(req.url)
        const client_id = url.searchParams.get('clientId')
        const type = url.searchParams.get('type')
        const upgrade = server.upgrade(req, {
            data: { id: client_id, type }
        })
        return upgrade ? undefined : new Response('Handshake failed', { status: 400 })
    },
    websocket: {
        async message(ws, message) {
            console.log(ws.data.id, message)
            if (ws.isSubscribed(DRONES)) {
                server.publish(FE, JSON.stringify({ id: ws.data.id, message }))
            }
            if (ws.isSubscribed(FE)) {
                try {
                    const msg = JSON.parse(message as string) as MsgFromFeToDrone
                    const msg_to_drone = {
                        type: msg.type,
                        duration: msg.duration
                    } satisfies MsgToDrone
                    server.publish(msg.id, JSON.stringify(msg_to_drone))
                } catch (e) {
                    console.log("Error parsing message", e)
                }
            }
        },
        open(ws) {
            console.log(`id ${ws.data.id}, type ${ws.data.type} joined`)
            if (ws.data.type == DRONES) {
                ws.subscribe(DRONES)
                ws.subscribe(ws.data.id)
                server.publish(DRONES, JSON.stringify({
                    id: ws.data.id,
                    type: "joined"
                }))
            }
            if (ws.data.type == FE) {
                ws.subscribe(FE)
            }
        },
        close(ws, code, reason) {
            console.log(`Lost connection with ${ws.data.id}`, { code, reason })
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