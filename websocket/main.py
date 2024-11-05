import uvicorn
from fastapi import FastAPI, WebSocket
import cv2

app = FastAPI()

@app.websocket("/ws/video")
async def video_stream(websocket: WebSocket):
    await websocket.accept()
    cap = cv2.VideoCapture("rtsp://admin:GWDCOI@192.168.1.5:554/stream?timeout=1000")
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Encode the frame as JPEG
            _, jpeg = cv2.imencode('.jpg', frame)
            
            # Send the frame as binary data over the WebSocket
            try:
                await websocket.send_bytes(jpeg.tobytes())
            except Exception as e:
                print(f"WebSocket send error: {e}")
                break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cap.release()
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run("main:app", host='0.0.0.0', port=8088)
