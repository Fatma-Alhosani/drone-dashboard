# -*- coding: utf-8 -*-
import os, sys, time, cv2, threading, queue, subprocess, json, requests
import numpy as np
from datetime import datetime
from pathlib import Path
try:
    from tflite_runtime.interpreter import Interpreter
except ImportError:
    from tensorflow.lite.python.interpreter import Interpreter
from pymavlink import mavutil

# ---------------- CONFIG ----------------
MODEL_PATH = "detect.tflite"
SAVE_DIR = str(Path.home() / "Desktop")
DEVICE = "/dev/video0"
RES_W, RES_H = 3840, 2160
FRAME_INTERVAL = 0.5
CONF_THRESH = 0.6
MERGE_IOU_THRESH = 0.6  # merge threshold
AREA_INSIDE_RATIO = 0.8  # smaller inside bigger -> drop
# Upload endpoint (Supabase)
PC_UPLOAD_URL_API = "http://10.25.159.239:8080/api/uploads"
# MAVLink UDP stream (from MAVProxy)
MAVLINK_UDP = "udp:127.0.0.1:14551"
# ----------------------------------------

# ---------- Utility functions ----------
def name_map(details):
    idx = {"boxes": None, "classes": None, "scores": None, "num": None}
    for d in details:
        n = d.get("name", "").lower()
        if "boxes" in n: idx["boxes"] = d["index"]
        elif "classes" in n: idx["classes"] = d["index"]
        elif "scores" in n: idx["scores"] = d["index"]
        elif "num" in n: idx["num"] = d["index"]
    if idx["boxes"] is None or idx["classes"] is None or idx["scores"] is None:
        order = [det["index"] for det in sorted(details, key=lambda x: x["index"])]
        idx["boxes"], idx["classes"], idx["scores"] = order[:3]
        if len(order) > 3: idx["num"] = order[3]
    return idx

def iou_xyxy(a,b):
    xx1,yy1=max(a[0],b[0]),max(a[1],b[1])
    xx2,yy2=min(a[2],b[2]),min(a[3],b[3])
    w,h=max(0,xx2-xx1),max(0,yy2-yy1)
    inter=w*h
    area_a=(a[2]-a[0])*(a[3]-a[1])
    area_b=(b[2]-b[0])*(b[3]-b[1])
    return inter/(area_a+area_b-inter+1e-6)

def area_inside_ratio(a,b):
    xx1,yy1=max(a[0],b[0]),max(a[1],b[1])
    xx2,yy2=min(a[2],b[2]),min(a[3],b[3])
    w,h=max(0,xx2-xx1),max(0,yy2-yy1)
    inter=w*h
    area_a=(a[2]-a[0])*(a[3]-a[1])
    return inter/(area_a+1e-6)

def merge_and_filter(boxes, iou_t=0.6, inside_ratio=0.8):
    """Merge close boxes and drop inner duplicates."""
    if len(boxes) == 0:
        return np.array([])

    merged = []
    used = set()

    for i in range(len(boxes)):
        if i in used:
            continue
        overlaps = [i]
        for j in range(i+1, len(boxes)):
            if j in used: continue
            if iou_xyxy(boxes[i], boxes[j]) > iou_t:
                overlaps.append(j)
                used.add(j)
        used.add(i)
        group = boxes[overlaps]
        merged.append([
            np.min(group[:,0]), np.min(group[:,1]),
            np.max(group[:,2]), np.max(group[:,3])
        ])
    merged = np.array(merged, dtype=int)

    # remove boxes mostly inside others
    keep = []
    for i in range(len(merged)):
        drop = False
        for j in range(len(merged)):
            if i == j: continue
            if area_inside_ratio(merged[i], merged[j]) > inside_ratio:
                drop = True
                break
        if not drop:
            keep.append(merged[i])
    return np.array(keep, dtype=int)

# ----------------------------------------
save_q = queue.Queue()
upload_q = queue.Queue()

def save_worker():
    while True:
        item = save_q.get()
        if item is None:
            break
        fname, img = item
        cv2.imwrite(fname, img, [cv2.IMWRITE_JPEG_QUALITY, 100])
        save_q.task_done()

# ---------- Upload worker ----------
def upload_worker():
    while True:
        job = upload_q.get()
        if job is None:
            break
        img_path, txt_path, gps = job
        try:
            gps_json = json.dumps(gps)
            with open(img_path, "rb") as fh:
                requests.post(
                    PC_UPLOAD_URL_API,
                    files={"file": (os.path.basename(img_path), fh)},
                    data={"gps": gps_json},
                    timeout=20
                ).raise_for_status()
            print(f"Uploading {os.path.basename(img_path)} and {os.path.basename(txt_path)}")
            # wait 0.2 second before next upload
            time.sleep(0.2)
        except Exception as e:
            print(f"[UPLOAD ERROR] {e}")
            time.sleep(1.0)
        upload_q.task_done()

# ---------- GPS listener ----------
latest_gps = {"lat": None, "lon": None, "alt": None, "time": None}

def gps_listener():
    global latest_gps
    print("Connecting to MAVLink UDP for GPS...")
    mav = mavutil.mavlink_connection(MAVLINK_UDP, source_system=255)
    while True:
        msg = mav.recv_match(type="GLOBAL_POSITION_INT", blocking=True, timeout=3)
        if msg:
            latest_gps = {
                "lat": msg.lat / 1e7,
                "lon": msg.lon / 1e7,
                "alt": msg.relative_alt / 1000.0,
                "time": time.time()
            }

# ---------- MAIN ----------
def main():
    print("starting GPS listener")
    threading.Thread(target=gps_listener, daemon=True).start()

    print("starting camera")
    os.system(f"sudo v4l2-ctl --device={DEVICE} "
              f"--set-fmt-video=width={RES_W},height={RES_H},pixelformat=UYVY")
    cap = cv2.VideoCapture(DEVICE, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, RES_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RES_H)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'UYVY'))
    cap.set(cv2.CAP_PROP_FPS, 15)
    if not cap.isOpened():
        print("ERROR: Cannot open camera.")
        return

    print("starting SSD model")
    intr = Interpreter(model_path=MODEL_PATH)
    intr.allocate_tensors()
    inp = intr.get_input_details()[0]
    outs = intr.get_output_details()
    out_idx = name_map(outs)
    ih, iw = inp["shape"][1:3]
    in_dtype = inp["dtype"]

    print("starting upload connection")
    threading.Thread(target=save_worker, daemon=True).start()
    threading.Thread(target=upload_worker, daemon=True).start()

    last_time = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        if frame.ndim == 2 or frame.shape[2] != 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_UYVY)

        now = time.time()
        if now - last_time < FRAME_INTERVAL:
            continue
        last_time = now

        resized = cv2.resize(frame, (iw, ih))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        x = np.expand_dims(rgb, 0)
        x = x.astype(np.uint8) if in_dtype == np.uint8 else (x.astype(np.float32)/255.0)
        intr.set_tensor(inp["index"], x)
        intr.invoke()

        boxes = intr.get_tensor(out_idx["boxes"])[0]
        clses = intr.get_tensor(out_idx["classes"])[0]
        scores = intr.get_tensor(out_idx["scores"])[0]
        n = min(int(intr.get_tensor(out_idx["num"])[0]) if out_idx["num"] else len(scores), len(scores))
        boxes, clses, scores = boxes[:n], clses[:n], scores[:n]

        mask = (scores >= CONF_THRESH) & (clses == 0)
        boxes, scores = boxes[mask], scores[mask]
        if len(boxes) == 0:
            continue

        H, W = frame.shape[:2]
        xyxy = np.column_stack([
            boxes[:,1]*W, boxes[:,0]*H,
            boxes[:,3]*W, boxes[:,2]*H
        ]).astype(int)

        filtered_boxes = merge_and_filter(xyxy, MERGE_IOU_THRESH, AREA_INSIDE_RATIO)
        if len(filtered_boxes) == 0:
            print("Skipped frame — only overlapping duplicates found.")
            continue

        for (x1, y1, x2, y2) in filtered_boxes:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
            cv2.putText(frame, "person", (x1, max(0, y1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        img_path = os.path.join(SAVE_DIR, f"{ts}.jpg")
        txt_path = os.path.join(SAVE_DIR, f"{ts}.txt")
        save_q.put((img_path, frame.copy()))
        print(f"{os.path.basename(img_path)} and location saved")

        gps = latest_gps.copy()
        with open(txt_path, "w") as f:
            f.write(f"Capture time: {ts}\n")
            if gps["lat"] is not None:
                f.write(f"GPS time: {datetime.fromtimestamp(gps['time']).strftime('%Y-%m-%d_%H-%M-%S')}\n")
                f.write(f"Latitude: {gps['lat']:.7f}\nLongitude: {gps['lon']:.7f}\nAltitude: {gps['alt']:.2f} m\n")
            else:
                f.write("GPS data not available\n")

        upload_q.put((img_path, txt_path, gps))

if __name__ == "__main__":
    main()
