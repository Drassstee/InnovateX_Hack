# Unified YOLO Pipeline for Signatures, Stamps, and QR Codes
# This script provides a single YOLO model to detect all three classes

import sys
import json
import cv2
import warnings
from pathlib import Path
from ultralytics import YOLO

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Model path
MODEL_PATH = "models/unified.pt"

# Class names mapping
CLASS_NAMES = {
    0: "signature",
    1: "stamp",
    2: "qr_code"
}


def load_model(model_path=MODEL_PATH):
    """
    Loads the unified YOLO model.
    If the model doesn't exist, it will try to use a base YOLOv8 model as fallback.
    """
    model_file = Path(model_path)
    
    if not model_file.exists():
        print(f"Warning: Model file {model_path} not found!")
        print("Attempting to use base YOLOv8s model (will need training for your classes)...")
        print("To train your model, use:")
        print("  yolo detect train data=datasets/digital_inspector.yaml model=yolov8s.pt imgsz=1024 epochs=50")
        # Try to load base model as fallback
        try:
            model = YOLO("yolov8s.pt")
            print("Loaded base YOLOv8s model (not trained for signatures/stamps/QR codes)")
            return model
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Please train a model first or download unified.pt to models/")
            sys.exit(1)
    
    try:
        model = YOLO(str(model_path))
        print(f"Loaded unified YOLO model from {model_path}")
        return model
    except Exception as e:
        print(f"Error loading model from {model_path}: {e}")
        sys.exit(1)


def detect_unified(image_path, output_image_path=None, conf=0.25):
    """
    Detects signatures, stamps, and QR codes using unified YOLO model.
    
    Args:
        image_path: Path to input image
        output_image_path: Optional path for annotated output image
        conf: Confidence threshold (default: 0.25)
    
    Returns:
        tuple: (annotated_image_path, json_metadata_path)
    """
    # Load model
    model = load_model()
    
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot load image: {image_path}")
    
    # Run inference
    print(f"Running YOLO detection on {image_path}...")
    results = model(image_path, conf=conf)
    
    # Process results
    detections = {
        "status": "success",
        "image_path": image_path,
        "detections": []
    }
    
    annotated_img = img.copy()
    
    for result in results:
        boxes = result.boxes
        for box in boxes:
            # Get box coordinates
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            confidence = float(box.conf[0].cpu().numpy())
            class_id = int(box.cls[0].cpu().numpy())
            class_name = CLASS_NAMES.get(class_id, f"class_{class_id}")
            
            # Add to detections
            detections["detections"].append({
                "class": class_name,
                "class_id": class_id,
                "confidence": round(confidence, 4),
                "bbox": {
                    "xmin": int(x1),
                    "ymin": int(y1),
                    "xmax": int(x2),
                    "ymax": int(y2)
                }
            })
            
            # Draw on image
            cv2.rectangle(annotated_img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            label = f"{class_name} {confidence:.2f}"
            cv2.putText(annotated_img, label, (int(x1), int(y1) - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    print(f"Found {len(detections['detections'])} detections")
    
    # Generate output paths
    input_path = Path(image_path)
    if output_image_path is None:
        out_img = str(input_path.parent / f"{input_path.stem}_annotated{input_path.suffix}")
    else:
        out_img = output_image_path
    
    out_json = str(Path(out_img).with_suffix('.json'))
    
    # Save outputs
    cv2.imwrite(out_img, annotated_img)
    
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(detections, f, indent=2)
    
    return out_img, out_json


# ---------------------------------------------------------------------------
# Training configuration (YAML) for YOLOv8
# ---------------------------------------------------------------------------
# Save this YAML to: datasets/digital_inspector.yaml
# Then train with:
#
#   yolo detect train data=datasets/digital_inspector.yaml model=yolov8s.pt imgsz=1024 epochs=50
#

TRAINING_YAML = """# digital_inspector.yaml
# Unified dataset for signatures, stamps, QR codes

path: {dataset_path}  # root dataset folder (absolute or relative to this YAML)
train: images/train
val: images/val
test: images/test

names:
  0: signature
  1: stamp
  2: qr_code
"""


def save_training_yaml(path="datasets/digital_inspector.yaml", dataset_path=None):
    """
    Saves the training YAML configuration file.
    
    Args:
        path: Path where to save the YAML file
        dataset_path: Path to dataset directory (default: ../dataset relative to YAML)
    
    Returns:
        str: Path to saved YAML file
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    
    # Determine dataset path
    if dataset_path is None:
        # Relative path from YAML location to dataset
        dataset_path = str(Path(p.parent.parent / "dataset").resolve())
    
    yaml_content = TRAINING_YAML.format(dataset_path=dataset_path)
    p.write_text(yaml_content, encoding="utf-8")
    print(f"Training YAML saved to: {p}")
    print(f"Dataset path: {dataset_path}")
    return str(p)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python yolo_pipeline.py <image> [output_image]")
        print("\nExample:")
        print("  python yolo_pipeline.py my_image.jpg")
        print("  python yolo_pipeline.py my_image.jpg output.jpg")
        print("\nTo create training YAML:")
        print("  python yolo_pipeline.py --create-yaml")
        sys.exit(1)
    
    # Check if user wants to create YAML
    if sys.argv[1] == "--create-yaml":
        yaml_path = save_training_yaml()
        print(f"\nTraining YAML created at: {yaml_path}")
        print("\nTo train your model, run:")
        print("  yolo detect train data=datasets/digital_inspector.yaml model=yolov8s.pt imgsz=1024 epochs=50")
        sys.exit(0)
    
    img_path = sys.argv[1]
    out_img = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        annotated, metadata = detect_unified(img_path, out_img, conf=0.25)
        print(f"\nAnnotated image saved to: {annotated}")
        print(f"JSON metadata saved to: {metadata}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

