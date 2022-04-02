import argparse
import asyncio
import json
import logging
import os
import ssl
import uuid
import uvicorn

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder, MediaRelay

from fastapi import FastAPI, Request, Response

from videoProcessor import VideoTransformTrack

ROOT = os.path.dirname(__file__)

logger = logging.getLogger("pc")
pcs = set()
relay = MediaRelay()

app = FastAPI()

parser = argparse.ArgumentParser(
    description="WebRTC OpenCV Face Detection"
)
parser.add_argument("--cert-file", help="SSL certificate file (for HTTPS)")
parser.add_argument("--key-file", help="SSL key file (for HTTPS)")
parser.add_argument(
    "--host", default="0.0.0.0", help="Host for HTTP server (default: 0.0.0.0)"
)
parser.add_argument(
    "--port", type=int, default=8080, help="Port for HTTP server (default: 8080)"
)
parser.add_argument("--record-to", help="Write received media to a file."),
parser.add_argument("--verbose", "-v", action="count")
args, unknown = parser.parse_known_args()


@app.on_event("shutdown")
async def on_shutdown():
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()


@app.get("/")
async def root(request: Request):
    content = open(os.path.join(ROOT, "index.html"), "r").read()
    return Response(content=content, media_type="text/html")


@app.get("/client.js")
async def javascript(request: Request):
    content = open(os.path.join(ROOT, "client.js"), "r").read()
    return Response(content=content, media_type="application/javascript")


@app.post("/offer")
async def offer(request: Request):
    params = await request.json()
    print(json.dumps(params, indent=4, sort_keys=True))
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pc_id = "PeerConnection(%s)" % uuid.uuid4()
    pcs.add(pc)

    def log_info(msg, *args):
        logger.info(pc_id + " " + msg, *args)

    log_info("Created for %s", request.client)

    # prepare local media
    player = MediaPlayer(os.path.join(ROOT, "demo-instruct.wav"))
    if args.record_to:
        recorder = MediaRecorder(args.record_to)
    else:
        recorder = MediaBlackhole()

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            if isinstance(message, str) and message.startswith("ping"):
                channel.send("pong" + message[4:])

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        log_info("Connection state is %s", pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    @pc.on("track")
    def on_track(track):
        log_info("Track %s received", track.kind)

        if track.kind == "audio":
            pc.addTrack(player.audio)
            recorder.addTrack(track)
        elif track.kind == "video":
            pc.addTrack(
                VideoTransformTrack(
                    relay.subscribe(track), transform=params["video_transform"]
                )
            )
            if args.record_to:
                recorder.addTrack(relay.subscribe(track))

        @track.on("ended")
        async def on_ended():
            log_info("Track %s ended", track.kind)
            await recorder.stop()

    # handle offer
    await pc.setRemoteDescription(offer)
    await recorder.start()

    # send answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return Response(
        content=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
        media_type="application/json",
    )
