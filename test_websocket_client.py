import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/chat"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket")
            
            # Send a test message
            message = {
                "type": "message",
                "message": "Hello Emreq"
            }
            await websocket.send(json.dumps(message))
            print("Sent message:", message)
            
            # Listen for responses
            response_count = 0
            while response_count < 10:  # Limit to prevent infinite loop
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    print(f"Received: {data}")
                    response_count += 1
                    
                    if data.get("type") == "complete":
                        print("Conversation complete")
                        break
                        
                except asyncio.TimeoutError:
                    print("Timeout waiting for response")
                    break
                    
    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket()) 