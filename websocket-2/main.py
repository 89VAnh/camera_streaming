import uvicorn
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import StreamingResponse
import cv2
from urllib.parse import unquote

app = FastAPI()

# This is just for managing WebRTC signaling
clients = {}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients[websocket] = True
    try:
        while True:
            data = await websocket.receive_text()
            # Here you can process signaling messages if needed
            print("Received:", data)
            await websocket.send_text(f"Echo: {data}")
    except Exception as e:
        print("Client disconnected", e)
    finally:
        del clients[websocket]

# Video stream function
def video_stream(url: str):
    cap = cv2.VideoCapture(url)

    if not cap.isOpened():
        raise HTTPException(status_code=404, detail="Could not open video stream")

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Encode frame to JPEG format
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                break

            frame_bytes = buffer.tobytes()
            
            # Create a multipart response for MJPEG
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    finally:
        cap.release()

@app.get("/video_feed")
async def video_feed(url: str):
    # Stream the video feed using StreamingResponse
    decoded_url = unquote(url)
    return StreamingResponse(video_stream(decoded_url), media_type="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    uvicorn.run("main:app", host='0.0.0.0', port=8088)
