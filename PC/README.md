How the System Works

1. Raspberry Pi uploads an image  
   The Pi sends:  
   The JPEG image  
   A JSON string containing GPS data  
   To: POST /api/uploads  

2. The server saves raw data  
   Uploads are stored in: photos_pre bucket  

3. Cropping stage crop_green_box() removes the green frame and returns:  
   Crop offsets  
   The cropped image  
   If cropping fails, the system falls back to the original image.  

4. Cigarette detection  
   Runs YOLO only on the cropped image.  

5. Veto detection  
   Runs a second YOLO model on the full image.  
   If a cup or bottle is found, the image is discarded (no upload to photos_post).  

6. Annotated upload  
   If cigarette detected and veto passes:  
   Full image is drawn with bounding boxes  
   The annotated JPEG is uploaded to photos_post  

7. Dashboard listing  
   A signed URL for each image is generated dynamically.  
   GPS text is loaded from the gps bucket.  

8. Cleanup thread  
   Every hour: All objects in photos_pre are deleted  
   Annotated images remain untouched  


API Endpoints  

POST /api/login  
Authenticate using Supabase Auth  

POST /api/logout  
Logout user  

GET /api/me  
Check user session  

POST /api/uploads  
Main upload endpoint for Raspberry Pi  

GET /api/list  
Returns JSON list of processed images with signed URLs and GPS  

DELETE /api/discard?file=FILENAME  
Deletes the image and its GPS file  


Running the Server  
python app.py  

Server runs on:  
http://0.0.0.0:8080  


Folder Structure Example  

pc-server/  
│  
├── app.py  
├── detect_and_crop_green_box.py  
│  
├── .env  
│  
├── models/  
│   ├── cigarette_best.pt  
│   └── yolo12m.pt  
│  
└── templates/  
    └── index.html
