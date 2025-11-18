import cv2
import numpy as np


def crop_green_box(image_path, pad_px=4):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot open image: {image_path}")


    h, w = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)


    # Threshold for bright green (YOLO-like box color)
    lower_green = np.array([35, 60, 60])
    upper_green = np.array([85, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)
    mask = cv2.dilate(mask, np.ones((3,3), np.uint8), iterations=2)


    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None, None, None


    best, best_area = None, 0
    for c in cnts:
        x, y, cw, ch = cv2.boundingRect(c)
        if cw < w * 0.05 or ch < h * 0.05:
            continue
        area = cw * ch
        if area > best_area:
            best_area, best = area, (x, y, cw, ch)


    if best is None:
        return None, None, None


    x, y, bw, bh = best
    x0 = max(0, x + pad_px)
    y0 = max(0, y + pad_px)
    x1 = min(w, x + bw - pad_px)
    y1 = min(h, y + bh - pad_px)


    cropped = img[y0:y1, x0:x1]
    return x0, y0, cropped


detect_and_crop_green_box.py
Green-Box Cropping Utility for the PC Detection Pipeline
This module isolates and crops the green bounding box drawn by the Raspberry Pi’s YOLO preview.
 It is used by the PC server (app.py) to extract the region-of-interest where the cigarette detection model should run.
The function returns both the cropped image and the X/Y offset so that the PC server can correctly map the detection boxes back to the original frame.

Purpose
Detect the green rectangle drawn by the Pi YOLO script


Extract only the inside region (removing green border)


Return coordinates so detections can be shifted back


Handle cases where no green box exists


This reduces computation time and increases cigarette detection accuracy by focusing only on the target region.

How It Works
Load image using OpenCV.


Convert BGR → HSV.


Threshold a specific green range:


Hue between 35–85


Sufficient saturation and brightness


Dilate mask to merge nearby edges.


Find contours corresponding to the green box.


Pick the largest valid contour.


Apply a padding offset to crop inside the box.


Return:


x_offset


y_offset


cropped_image


If no contour is found, all return values are None.

Function Reference
crop_green_box(image_path, pad_px=4)
Arguments
Parameter
Type
Description
image_path
str
Path to the input image
pad_px
int
Pixels to trim inside the bounding box (default 4)

Returns
(x_offset, y_offset, cropped_img)

or:
(None, None, None)

if no green box is detected.

Example Usage
from detect_and_crop_green_box import crop_green_box

x_off, y_off, crop = crop_green_box("frame.jpg")

if crop is not None:
    print("Crop successful:", crop.shape)
else:
    print("No green box found.")


Color Threshold Explanation
The threshold is tuned to match the Raspberry Pi’s YOLO preview rectangle color:
Hue:   35–85  (bright green)
Sat:   >= 60
Value: >= 60

This range is robust against lighting changes and works reliably outdoors.

Notes
The function assumes the Pi-generated green rectangle is thick and clear.


If multiple green regions exist, the largest one is chosen.


Padding ensures the model never sees the green border, preventing false detections.


Returning (x, y) offsets allows the PC server to shift detection boxes back correctly.

