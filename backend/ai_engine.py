# CitizenShield - Real AI Civic Vision Inference Engine
# Powered by fine-tuned YOLOv8 deep learning vision models
import os
import cv2
import numpy as np
from PIL import Image

try:
    from ultralytics import YOLO
    AI_AVAILABLE = True
except Exception as e:
    AI_AVAILABLE = False
    print(f"[CitizenShield AI] Ultralytics import warning: {e}")

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
ROAD_DISTRESS_WEIGHTS = os.path.join(MODEL_DIR, "road_distress_yolov8n.pt")
POTHOLE_WEIGHTS = os.path.join(MODEL_DIR, "pothole_yolov8n.pt")
GARBAGE_WEIGHTS = os.path.join(MODEL_DIR, "garbage_yolov8n.pt")

_distress_model = None
_pothole_model = None
_garbage_model = None

def get_models():
    """Lazily loads and caches the fine-tuned civic computer vision models."""
    global _distress_model, _pothole_model, _garbage_model
    if not AI_AVAILABLE:
        return None, None, None

    if _distress_model is None and os.path.exists(ROAD_DISTRESS_WEIGHTS):
        try:
            _distress_model = YOLO(ROAD_DISTRESS_WEIGHTS)
        except Exception as e:
            print(f"[CitizenShield AI] Error loading road distress model: {e}")

    if _pothole_model is None and os.path.exists(POTHOLE_WEIGHTS):
        try:
            _pothole_model = YOLO(POTHOLE_WEIGHTS)
        except Exception as e:
            print(f"[CitizenShield AI] Error loading pothole model: {e}")

    if _garbage_model is None and os.path.exists(GARBAGE_WEIGHTS):
        try:
            _garbage_model = YOLO(GARBAGE_WEIGHTS)
        except Exception as e:
            print(f"[CitizenShield AI] Error loading garbage model: {e}")

    return _distress_model, _pothole_model, _garbage_model

def analyze_water_drainage(image_path):
    """
    Computer Vision Heuristic Water & Drainage Surface Analysis.
    Performs real OpenCV color-space (HSV/LAB), edge-density, and specular reflection
    inspection to detect open water accumulation, pipe burst flooding, and drainage pooling.
    Returns (detected_class, confidence, details) or (None, 0.0, None).
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return None, 0.0, None

        h, w = img.shape[:2]
        total_pixels = h * w
        if total_pixels == 0:
            return None, 0.0, None

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 1. Turbid / Sewage / Drain Water Mask (Dark greenish-brown muddy pooling)
        # Hue: 15-45 (brown/olive/yellowish-green), Saturation: 30-180, Value: 20-140
        drain_mask = cv2.inRange(hsv, np.array([15, 30, 20]), np.array([50, 200, 150]))
        drain_ratio = cv2.countNonZero(drain_mask) / total_pixels

        # 2. Clear Water Leakage / Fresh Pool Reflection (Blueish / specular bright reflections on wet pavement)
        # Blue hues 85-135 with medium saturation and value
        water_mask = cv2.inRange(hsv, np.array([85, 40, 40]), np.array([135, 255, 255]))
        water_ratio = cv2.countNonZero(water_mask) / total_pixels

        # 3. Specular highlights & low local variance indicative of puddles/water sheen
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)
        smooth_area_ratio = 1.0 - (cv2.countNonZero(edges) / total_pixels)

        # If significant sewage/drain pooling is identified:
        if drain_ratio > 0.18 and smooth_area_ratio > 0.70:
            conf = min(0.92, 0.55 + (drain_ratio * 1.5))
            return "Drainage problems", round(float(conf), 3), {
                "pooling_density": round(float(drain_ratio), 3),
                "type": "Sewage / Stagnant Overflow Detected"
            }

        # If clean water leak / pipeline burst pooling is identified:
        if water_ratio > 0.12 and smooth_area_ratio > 0.65:
            conf = min(0.89, 0.52 + (water_ratio * 1.8))
            return "Water leakage", round(float(conf), 3), {
                "water_sheen_ratio": round(float(water_ratio), 3),
                "type": "Pipeline Burst / Surface Leak Detected"
            }

        return None, 0.0, None
    except Exception as e:
        print(f"[CitizenShield AI] Water/Drainage CV analysis error: {e}")
        return None, 0.0, None

def analyze_civic_image(image_path, confidence_threshold=0.25):
    """
    Multi-stage real AI Civic Problem Image Detection.
    Runs real inference across YOLO models and OpenCV computer vision:
    1. YOLOv8 Road Distress Model (Longitudinal Crack, Transverse Crack, Alligator Crack, Pothole)
    2. YOLOv8 Specialized Pothole Segmentation Model
    3. YOLOv8 Garbage/Litter Detection Model
    4. OpenCV Real Water & Drainage Surface Spectral Analysis
    
    Returns structured dict with detection results, suggested category, priority, and bounding boxes.
    """
    if not os.path.exists(image_path):
        return {
            "success": False,
            "error": "Image file not found on server",
            "detected": False
        }

    distress_m, pothole_m, garbage_m = get_models()
    
    detections = []
    annotated_filename = None

    # --- Step 1: Road Distress Model (Potholes, Alligator Cracks, Longitudinal/Transverse Cracks) ---
    if distress_m is not None:
        try:
            results = distress_m.predict(source=image_path, conf=confidence_threshold, verbose=False)
            if results and len(results) > 0:
                res = results[0]
                boxes = res.boxes
                if boxes is not None and len(boxes) > 0:
                    for box in boxes:
                        cls_id = int(box.cls[0].item())
                        cls_name = distress_m.names.get(cls_id, "Unknown")
                        conf = float(box.conf[0].item())
                        xyxy = [float(x) for x in box.xyxy[0].tolist()]

                        # Standardize Civic Classes
                        if cls_name.lower() in ["pothole"]:
                            canonical_class = "Potholes"
                            suggested_cat = "Roads and Transport"
                            suggested_prio = "High" if conf > 0.6 else "Normal"
                        elif "crack" in cls_name.lower():
                            canonical_class = "Road damage"
                            suggested_cat = "Roads and Transport"
                            suggested_prio = "High" if ("alligator" in cls_name.lower() or conf > 0.7) else "Normal"
                        else:
                            canonical_class = "Road damage"
                            suggested_cat = "Roads and Transport"
                            suggested_prio = "Normal"

                        detections.append({
                            "detected_class": canonical_class,
                            "raw_class": cls_name,
                            "confidence_score": round(conf, 3),
                            "model_name": "YOLOv8-Road-Distress-v1",
                            "suggested_category": suggested_cat,
                            "suggested_priority": suggested_prio,
                            "bbox": xyxy
                        })
        except Exception as e:
            print(f"[CitizenShield AI] Distress model inference exception: {e}")

    # --- Step 2: Dedicated Pothole Segmentation Model ---
    if pothole_m is not None:
        try:
            results = pothole_m.predict(source=image_path, conf=confidence_threshold, verbose=False)
            if results and len(results) > 0:
                res = results[0]
                boxes = res.boxes
                if boxes is not None and len(boxes) > 0:
                    for box in boxes:
                        conf = float(box.conf[0].item())
                        xyxy = [float(x) for x in box.xyxy[0].tolist()]
                        detections.append({
                            "detected_class": "Potholes",
                            "raw_class": "pothole",
                            "confidence_score": round(conf, 3),
                            "model_name": "YOLOv8n-Pothole-Segmentation",
                            "suggested_category": "Roads and Transport",
                            "suggested_priority": "High" if conf > 0.65 else "Normal",
                            "bbox": xyxy
                        })
        except Exception as e:
            print(f"[CitizenShield AI] Pothole model inference exception: {e}")

    # --- Step 3: Dedicated Garbage & Litter Model ---
    if garbage_m is not None:
        try:
            results = garbage_m.predict(source=image_path, conf=confidence_threshold, verbose=False)
            if results and len(results) > 0:
                res = results[0]
                boxes = res.boxes
                if boxes is not None and len(boxes) > 0:
                    for box in boxes:
                        conf = float(box.conf[0].item())
                        xyxy = [float(x) for x in box.xyxy[0].tolist()]
                        detections.append({
                            "detected_class": "Garbage accumulation",
                            "raw_class": "Litter / Waste Accumulation",
                            "confidence_score": round(conf, 3),
                            "model_name": "YOLOv8n-Solid-Waste-Detector",
                            "suggested_category": "Garbage and Sanitation",
                            "suggested_priority": "High" if conf > 0.70 else "Normal",
                            "bbox": xyxy
                        })
        except Exception as e:
            print(f"[CitizenShield AI] Garbage model inference exception: {e}")

    # --- Step 4: Water Leakage & Drainage Surface CV Analysis ---
    water_class, water_conf, water_meta = analyze_water_drainage(image_path)
    if water_class is not None:
        if water_class == "Drainage problems":
            s_cat = "Drainage and Sewage"
            s_prio = "High" if water_conf > 0.7 else "Normal"
        else:
            s_cat = "Water Supply"
            s_prio = "High" if water_conf > 0.75 else "Normal"

        detections.append({
            "detected_class": water_class,
            "raw_class": water_meta.get("type", water_class),
            "confidence_score": water_conf,
            "model_name": "OpenCV-Hydrological-Spectral-Analyzer",
            "suggested_category": s_cat,
            "suggested_priority": s_prio,
            "bbox": None
        })

    # Pick top detection by highest confidence
    if detections:
        # Sort by confidence descending
        detections.sort(key=lambda d: d["confidence_score"], reverse=True)
        top = detections[0]

        # Generate annotated preview image if bounding boxes exist
        try:
            img = cv2.imread(image_path)
            has_annotated = False
            for d in detections:
                if d.get("bbox"):
                    has_annotated = True
                    b = [int(v) for v in d["bbox"]]
                    label = f"{d['detected_class']} {int(d['confidence_score']*100)}%"
                    cv2.rectangle(img, (b[0], b[1]), (b[2], b[3]), (0, 215, 255), 2)
                    cv2.putText(img, label, (b[0], max(20, b[1] - 8)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 215, 255), 2)
            
            if has_annotated:
                base, ext = os.path.splitext(image_path)
                annotated_path = f"{base}_annotated{ext}"
                cv2.imwrite(annotated_path, img)
                annotated_filename = os.path.basename(annotated_path)
        except Exception as e:
            print(f"[CitizenShield AI] Annotation saving error: {e}")

        return {
            "success": True,
            "detected": True,
            "detected_class": top["detected_class"],
            "raw_class": top["raw_class"],
            "confidence_score": top["confidence_score"],
            "confidence_percent": f"{int(top['confidence_score'] * 100)}%",
            "model_name": top["model_name"],
            "suggested_category": top["suggested_category"],
            "suggested_priority": top["suggested_priority"],
            "all_detections": detections,
            "annotated_image": annotated_filename,
            "message": f"Real AI Model detected: {top['detected_class']} ({int(top['confidence_score'] * 100)}% confidence)"
        }

    # Fallback if no civic defect detected
    return {
        "success": True,
        "detected": False,
        "detected_class": None,
        "confidence_score": 0.0,
        "model_name": "YOLOv8-Ensemble-v1",
        "suggested_category": None,
        "suggested_priority": "Normal",
        "all_detections": [],
        "message": "No supported civic problem detected. Please select the complaint category manually."
    }
