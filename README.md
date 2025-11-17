Smart Drones and Computer Vision for Smoking Detection
Senior Design Project – American University of Sharjah
This repository contains the full implementation of our drone-based smoking-violation detection system.
The project combines:
autonomous drone missions
real-time image capture
computer vision processing
Supabase storage
a full web dashboard for monitoring smoking events
The system runs in three major components:
1. Raspberry Pi (on the drone)
Runs YOLO detection
Captures frames during missions
Sends images + GPS JSON to the PC server
2. PC Server (Flask + YOLO)
Receives images
Runs high-resolution cigarette detection
Applies veto logic
Uploads annotated results to Supabase
Powers the dashboard backend
3. Web Dashboard
Displays detected violations
Shows GPS coordinates + timestamps
Allows zooming, panning, next/previous navigation
Allows deleting results
Provides new-detection notifications
Repository Structure
root/
│
├── README.md                 ← Main project overview
│
├── pc/                       ← PC server processing pipeline
│   ├── README.md             ← Detailed PC-side documentation
│   ├── app.py                ← Flask server + cigarette detection
│   ├── detect_and_crop_green_box.py
│   └── templates/
│       └── index.html        ← Web dashboard UI
│
└── rpi/                      ← Raspberry Pi drone-side code
    ├── README.md             ← RPi documentation
    └── mission.py            ← Captures frames + YOLO + uploads to PC
System Summary
Drone (Raspberry Pi + Pixhawk)
Executes autonomous missions using Pixhawk Mission Planner
Captures live images via the Pi camera
Performs preliminary detection to draw a green bounding box
Sends every frame + GPS JSON to the PC server
Designed for stable outdoor low-altitude missions
PC Server (Flask backend)
Receives uploads from the drone
Crops the green-box region
Runs two YOLO models:
Cigarette model
Veto model (cup/bottle detector)
Annotates detections and uploads them to Supabase
Deletes non-useful raw images via cleanup thread
Provides dashboard API (/list, /login, /delete)
Dashboard (index.html)
Displays processed images
Shows GPS location on Leaflet map
Supports zooming, panning, and next/previous browsing
Allows deleting detections
Auto-refreshes signed URLs every hour
Can notify operator of new detections
Technologies Used
Python (Flask, OpenCV, NumPy)
YOLO (Ultralytics – cigarette + veto models)
Supabase Storage & Authentication
Leaflet.js
Pixhawk + Mission Planner
Raspberry Pi camera
How to Run the System End-to-End
1. Start the PC server
cd pc
python app.py
2. Start Raspberry Pi flight code
cd rpi
python mission.py
3. Open the dashboard
http://<pc-ip>:8080
Authors
Turki Alzahrani
Wajeeh Dalbah
Fatima Alhosani
Riya Garissa
Advisors: Prof. Taha Landolsi & Prof. Gheith Abandah
Department of Computer Science and Engineering
American University of Sharjah
