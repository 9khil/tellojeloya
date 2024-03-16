import asyncio
import websockets

async def send_message(uri, message):
    async with websockets.connect(uri) as websocket:
        await websocket.send(message)
        print(f"Message sent: {message}")

async def receive_message(uri):
    async with websockets.connect(uri) as websocket:
        received_message = await websocket.recv()
        print(f"Message received: {received_message}")
        return received_message

async def main():
    uri = "ws://10.168.119.237:3000"  # Replace this with the actual WebSocket server address

    # Sending a message
    message_to_send = "Hello, WebSocket Server!"
    await send_message(uri, message_to_send)

    # Receiving a message
    received_message = await receive_message(uri)
    print(f"Received message: {received_message}")

asyncio.run(main())

