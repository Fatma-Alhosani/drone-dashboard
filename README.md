# Smart Drones and Computer Vision for Smoking Detection
**Senior Design Project – American University of Sharjah**

This repository contains the full implementation of our drone-based smoking-violation detection system.
The project combines autonomous drone missions, real-time image capture, computer vision processing, Supabase storage, and a full web dashboard for monitoring detected smoking events.

---

## System Components

### Raspberry Pi (on the drone)
Runs YOLO detection, captures frames during missions, sends images and GPS data to the PC server.

### PC Server (Flask + YOLO)
Receives images, runs high-resolution cigarette detection, verifies frames using veto logic, uploads annotated results to Supabase, and powers the dashboard backend.

### Web Dashboard
Displays detected violations, GPS coordinates, timestamps, and allows operators to browse, zoom, and delete results.

---

## Repository Structure

```


root/
|
|-- README.md                      <- This file (overview of entire project)
|
|-- pc/                            <- PC server processing pipeline
|   |-- README.md                  <- Detailed PC-side documentation
|   |-- app.py                     <- Flask server + cigarette detection
|   |-- detect_and_crop_green_box.py
|   `-- templates/
|       `-- index.html             <- Web dashboard UI
|
`-- rpi/                           <- Raspberry Pi flight-side code
    |-- README.md                  <- RPi-specific documentation (already done)
    `-- mission.py                 <- Captures frames + YOLO + uploads to PC
```


## System Summary

### • Drone (Raspberry Pi + Pixhawk)
- Executes autonomous missions using Pixhawk Mission Planner
- Captures live images via the Pi camera
- Performs preliminary detection to draw a green bounding box
- Sends every frame + GPS JSON to the PC server
- Designed for stable outdoor low-altitude missions

### • PC Server (Flask backend)
- Receives uploads from drone
- Crops the green-box region for efficient cigarette detection
- Runs two YOLO models:
  - Cigarette model
  - Veto model (cup/bottle detector)
- Annotates detections and uploads them to Supabase
- Deletes non-useful raw images via a cleanup thread
- Provides the dashboard API (list, login, delete)

### • Dashboard (index.html)
- Displays all detected images
- Shows GPS location on a live map (Leaflet)
- Provides zooming, panning, previous/next navigation
- Allows deleting detections
- Auto-refreshes signed URLs every hour
- Can notify the operator of new detections

---

## Technologies Used
- Python (Flask, OpenCV, NumPy)
- YOLO (Ultralytics: cigarette + veto models)
- Supabase Storage + Auth
- Leaflet.js mapping
- Autonomous drone control (Pixhawk + Mission Planner)
- Raspberry Pi camera + multithreaded frame pipeline

---

## How to Run the System End-to-End

### 1. Start PC server:
cd pc
python app.py

### 2. Start Raspberry Pi flight code:
cd rpi
python mission.py

### 3. Open Dashboard:
http://<pc-ip>:8080

---

## Authors
- Turki Alzahrani
- Wajeeh Dalbah
- Fatima Alhosani
- Riya Garissa

**Advisors:** Prof. Gheith Abandah & Prof. Taha Landolsi 

**Department of Computer Science and Engineering**  
**American University of Sharjah**
