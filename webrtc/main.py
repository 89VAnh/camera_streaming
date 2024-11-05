import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from aiortc import RTCPeerConnection, VideoStreamTrack
from aiortc.contrib.media import MediaPlayer
import os

app = FastAPI()

# Clients dictionary to manage connections
clients = {}

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to the origins you want to allow
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


class VideoStream(VideoStreamTrack):
    def __init__(self, player: MediaPlayer):
        super().__init__()  # Initialize base class
        self.player = player

    async def recv(self):
        frame = await self.player.recv()
        return frame


@app.get("/")
async def get():
    file_path = os.path.join(os.path.dirname(__file__), "index.html")
    return HTMLResponse(content=open(file_path).read())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients[websocket] = True

    pc = RTCPeerConnection()

    @pc.on("icecandidate")
    async def on_icecandidate(candidate):
        if candidate:
            await websocket.send_json({"type": "candidate", "candidate": candidate})

    @pc.on("track")
    def on_track(track):
        # Here we could handle the incoming track
        pass

    try:
        while True:
            data = await websocket.receive_json()
            if data["type"] == "offer":
                await pc.set_remote_description(data["sdp"])
                answer = await pc.create_answer()
                await pc.set_local_description(answer)
                await websocket.send_json(
                    {"type": "answer", "sdp": pc.local_description.sdp}
                )

            if data["type"] == "disconnect":
                await pc.close()
                break
    except WebSocketDisconnect:
        print("Client disconnected")
    finally:
        del clients[websocket]


@app.get("/video_feed/{camera_id}")
async def video_feed(camera_id: int):
    rtsp_urls = [
        "rtsp://admin:GWDCOI@192.168.1.5:554/stream?timeout=1000",
        "rtsp://admin:CHZPLD@192.168.1.6:554/stream?timeout=1000",
    ]

    # Initialize MediaPlayer with the RTSP URL
    player = MediaPlayer(rtsp_urls[camera_id])
    video_track = VideoStream(player)

    # Add video track to PeerConnection
    pc = RTCPeerConnection()
    pc.addTrack(video_track)

    # Notify client that the WebRTC connection has been established
    return {"message": "WebRTC connection established for camera " + str(camera_id)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8088)
