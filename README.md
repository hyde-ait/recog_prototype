# recog_prototype

Realtim face detection FastAPI app using OpenCV and streaming via WebRTC (using aiortc).

Converted the code in https://github.com/aiortc/aiortc/tree/main/examples/server into a FastAPI app and added face detection functionality.

## Requirements

Python 3.9+

## Startup

git clone https://github.com/RumbleFiend/recog_prototype.git

cd recog_prototype

pip install -r requirements.txt

uvicorn server:app --reload

