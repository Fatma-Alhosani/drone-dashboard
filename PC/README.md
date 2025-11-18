# PC Server – Detection Pipeline
Flask Processing Backend + YOLO + Supabase Dashboard

This directory contains the full computer-vision backend and dashboard server used to process images sent from the Raspberry Pi during drone missions.
The PC performs high-resolution cigarette detection, veto filtering, image annotation, GPS pairing, and dashboard hosting.

---

## Contents
```
pc/
|
|-- README.md                       <- This file
|-- app.py                          <- Main Flask server + YOLO pipeline
|-- detect_and_crop_green_box.py    <- Green-box crop utility
`-- templates/
    `-- index.html                  <- Dashboard front-end
```
---

## app.py (Main Server)

app.py is the heart of the system. It provides:

### 1. Upload processing
- Receives JPEG frames and GPS JSON from the Raspberry Pi
- Saves raw uploads to Supabase photos_pre and gps buckets
- Crops the frame using green-box detection
- Runs cigarette detection using a custom YOLO model
- Runs cup/bottle veto detection using a second YOLO model
- Draws bounding boxes on original frames
- Uploads annotated results to Supabase photos_post

### 2. Dashboard backend
Provides JSON endpoints for:
- Login (/api/login)
- List all detections (/api/list)
- Delete detections (/api/discard)
- Signed URL refresh
- Session management

### 3. Cleanup worker
A background thread removes all images from photos_pre every hour to prevent Supabase storage growth.

---

## detect_and_crop_green_box.py

This script isolates the green bounding box drawn by the Raspberry Pi YOLO preview.

It returns:
- x_offset
- y_offset
- cropped_image

The PC detection pipeline then applies cigarette detection only inside this region for efficiency and accuracy.

If no green box is detected, the function returns:
(None, None, None)
and the full image is used instead.

---

## Dashboard (index.html)

The dashboard displays all detected smoking events:

- High-resolution annotated images
- GPS coordinates on a Leaflet map
- Timestamps parsed from filenames
- Navigation buttons: previous, next, refresh, discard
- Zoom and pan tools for each image
- Real-time notifications when new detections arrive
- Authentication via Supabase Auth (email + password)

All images are loaded from Supabase through signed URLs, refreshed hourly to avoid expiration.

---

## Requirements

Install dependencies:
pip install flask supabase python-dotenv ultralytics opencv-python numpy

Environment variables (.env):

SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...

SUPABASE_PHOTOS_BUCKET=photos_post
SUPABASE_PHOTOS_PRE_BUCKET=photos_pre
SUPABASE_GPS_BUCKET=gps

MODELS_DIR=path/to/models
CIG_WEIGHTS=cigarette_best.pt
VETO_WEIGHTS=yolo12m.pt

CIG_IMGSZ=1536
CIG_CONF=0.45
CIG_IOU=0.45
CIG_CLASS_ID=0

VETO_IMGSZ=640
VETO_CONF=0.35

FLASK_SECRET_KEY=some-secret

Models must be placed in the directory specified by MODELS_DIR.

---

## Running the PC Server

python app.py

The server runs at:
http://0.0.0.0:8080

Make sure the Raspberry Pi points its upload requests to this machine.

---

## Notes

- Detections and GPS files remain in photos_post until manually deleted.
- photos_pre bucket is automatically cleaned hourly.
- Two YOLO models are used: cigarette detector and cup/bottle veto model.
- Green-box cropping improves accuracy and reduces false positives.
