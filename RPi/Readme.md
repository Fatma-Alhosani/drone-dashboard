# Raspberry Pi – Flight & Detection Pipeline
Autonomous Image Capture + YOLO Preview + GPS Logging + Upload Pipeline

This directory contains the full Raspberry Pi–side pipeline responsible for capturing video frames, detecting humans (preview-only), saving images, attaching GPS coordinates, and uploading results to the PC server during drone missions.

The Raspberry Pi acts as the on-drone edge processor, handling camera capture, basic detection, and communication with Pixhawk via MAVLink.

---

## Contents
```
rpi/
│
├── README.md                 ← This file
└── Full_Mission.py           ← Main Raspberry Pi mission script (camera + GPS + upload)
```
---

## Full_Mission.py (Main RPi Script)

This script runs on the Raspberry Pi during autonomous missions.  
It performs:

---

## 1. Camera Initialization & Video Capture

- Uses /dev/video0 as the camera source
- Configures the Pi camera using v4l2-ctl
- Captures 4K frames (3840×2160)
- Converts camera output from UYVY → BGR
- Maintains a frame interval of 0.5s to control processing load

---

## 2. Human Detection (Preview Only)

Uses a TensorFlow Lite SSD model:

- Loads detect.tflite
- Resizes frames to model input shape
- Runs inference on each frame
- Extracts:
  - bounding boxes  
  - class IDs  
  - detection scores  

### Filtering
- Keeps only detections with:
  - class_id == 0 (person)
  - confidence ≥ 0.6

### Box Consolidation
- Merges overlapping bounding boxes
- Removes small duplicate boxes using IOU + area rules
- Draws green bounding boxes on the frame (preview only)

---

## 3. GPS Listener (MAVLink)

A separate thread listens to Pixhawk via MAVLink:

- Connects to udp:127.0.0.1:14551
- Receives GLOBAL_POSITION_INT messages
- Extracts:
  - lat  
  - lon  
  - alt  
  - timestamp  

GPS values are attached to every captured frame.

---

## 4. Saving Images Locally

For every detected frame:

- Generates timestamp-based filenames
- Saves the annotated JPEG image
- Writes a matching .txt file containing:
  - capture time  
  - GPS time  
  - latitude  
  - longitude  
  - altitude  
- Uses a background worker thread for non-blocking saves

---

## 5. Uploading to the PC Server

Uploads occur asynchronously via a second worker thread.

Each upload contains:

- The JPEG image
- The metadata text file
- A JSON object with GPS data

Sent to the PC endpoint:

http://<pc-ip>:8080/api/uploads

Includes retry logic and error handling.

---

## 6. Main Loop Overview

1. Capture frame  
2. Apply TFLite detection  
3. Merge boxes  
4. Draw box overlays  
5. Save image + metadata  
6. Queue upload job  

Runs continuously until interrupted.

---

## Configuration Variables (From Script Top)

MODEL_PATH = "detect.tflite"  
SAVE_DIR = ~/Desktop  
DEVICE = "/dev/video0"  
FRAME_INTERVAL = 0.5  
CONF_THRESH = 0.6  
PC_UPLOAD_URL_API = "http://<pc-ip>:8080/api/uploads"  
MAVLINK_UDP = "udp:127.0.0.1:14551"

---

## Requirements

### Install packages:

pip install numpy requests opencv-python pillow  
pip install tflite-runtime  
sudo apt install v4l-utils

### Hardware / Software Needed

- Raspberry Pi 4 (recommended)
- Pixhawk flight controller with MAVProxy sending GPS to Pi
- Camera module supporting UYVY format
- Working WiFi or LTE connection to reach the PC server

---

## Running the Mission Script

python3 Full_Mission.py

Ensure:

- The camera is connected  
- MAVProxy is streaming GPS to the Pi  
- The PC server is running  

---

## Notes

- On-board detection is preview-only. Final cigarette detection is done on the PC.
- Upload worker prevents network issues from blocking image capture.
- GPS listener ensures correct location tagging for each frame.
- Script is optimized for real-time 4K capture with low latency.
