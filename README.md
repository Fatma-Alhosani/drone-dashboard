Smart Drones and Computer Vision for Smoking Detection

Overview
This project by Senior Design Project Group 6 (AUS, Spring 2025) builds an autonomous drone system that detects smoking in areas using AI and computer vision.
It combines a Raspberry Pi, Flask server, Supabase cloud, and a web dashboard to capture, process, and visualize detections with GPS data.

System Components
1. Drone (Raspberry Pi)
Detects humans using a TensorFlow Lite model.


Captures frames, attaches GPS data (via MAVLink), and uploads to the Flask server.


2. Flask Server
Receives images and GPS data at /api/uploads.


Runs YOLO-based cigarette detection.


Uploads to Supabase Storage under:


photos_pre – initial detections.


photos_post – confirmed cigarette detections.


3. Web Dashboard
Built with HTML, CSS, and JS (Leaflet Map).


Displays detections and GPS locations.


Allows refresh, navigation, and deletion of records.


4. Supabase Cloud
Stores images, GPS text files, and documentation.


Secure access using environment variables in .env.



Data Flow
Drone → Flask Server → Supabase → Dashboard



Run Instructions
Flask Server
pip install flask supabase python-dotenv requests ultralytics opencv-python
python app.py

Raspberry Pi
Place detect.tflite beside Full_Mission.py.


Update PC_UPLOAD_URL_API with the Flask server IP.


Run: python3 Full_Mission.py

Dashboard
Access via browser: http://<server-ip>:8080

Team
Group 6 – American University of Sharjah
Turki Alzahrani


Wajeeh Dalbah


Fatima Alhosani


Riya Garissa


 Advisors: Prof. Taha Landolsi, Prof. Gheith Abandah



License
Academic submission for COE 491 – Senior Design Project II.
For research and educational use only.


