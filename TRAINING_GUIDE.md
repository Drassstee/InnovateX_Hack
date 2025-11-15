# Complete YOLO Training Guide

This guide will walk you through the entire process of training a YOLO model to detect signatures, stamps, and QR codes.

## 📋 Table of Contents

1. [Installation](#installation)
2. [Dataset Preparation](#dataset-preparation)
3. [Annotation](#annotation)
4. [Training](#training)
5. [Using Your Trained Model](#using-your-trained-model)

---

## 1. Installation

### Step 1: Install Requirements

```bash
pip install -r requirements.txt
```

This will install:
- `ultralytics` (YOLOv8)
- `opencv-python`
- `torch` and `torchvision`
- All other dependencies

### Step 2: Verify Installation

```bash
python -c "from ultralytics import YOLO; print('YOLO installed successfully!')"
```

---

## 2. Dataset Preparation

### Step 1: Organize Your Images

You need images containing:
- **Signatures** (handwritten signatures on documents)
- **Stamps** (official stamps/seals)
- **QR codes** (any QR codes)

**Recommended:**
- At least **100 images per class** for good results
- More images = better accuracy
- Variety is important (different lighting, angles, sizes)

### Step 2: Create Dataset Structure

Run the helper script to create the proper directory structure:

```bash
python prepare_dataset.py create
```

This creates:
```
dataset/
  images/
    train/
    val/
    test/
  labels/
    train/
    val/
    test/
```

### Step 3: Split Your Images

If you have all images in one folder (e.g., `test_images`), split them automatically:

```bash
python prepare_dataset.py split --source test_images --output dataset
```

This will:
- Split images into 70% train, 20% validation, 10% test
- Copy images to the correct directories

**Or manually:**
- Copy your images to `dataset/images/train/`, `dataset/images/val/`, `dataset/images/test/`

---

## 3. Annotation

### Option A: Using LabelImg (Recommended)

**Install LabelImg:**
```bash
pip install labelImg
```

**Run LabelImg:**
```bash
labelImg
```

**Setup:**
1. Open LabelImg
2. Change format to **YOLO** (top menu: "Format" → "YOLO")
3. Open directory: `dataset/images/train`
4. Set save directory: `dataset/labels/train`
5. Create classes: `signature`, `stamp`, `qr_code`

**Keyboard Shortcuts:**
- `W` - Create bounding box
- `D` - Next image
- `A` - Previous image
- `0`, `1`, `2` - Select class (signature=0, stamp=1, qr_code=2)

**Annotation Tips:**
- Draw boxes tightly around objects
- Include some context but not too much
- Be consistent
- Annotate all instances in each image

### Option B: Using Roboflow (Online)

1. Go to [roboflow.com](https://roboflow.com)
2. Create a new project
3. Upload your images
4. Annotate online
5. Export in YOLO format
6. Download and extract to your `dataset/` folder

### Option C: Manual Annotation

Each image needs a `.txt` file with the same name.

**Format:** `class_id center_x center_y width height`

All values are normalized (0.0 to 1.0).

**Example:** `image001.jpg` → `image001.txt`
```
0 0.5 0.5 0.2 0.1
1 0.3 0.7 0.15 0.15
```

**Class IDs:**
- `0` = signature
- `1` = stamp
- `2` = qr_code

### Verify Annotations

Check your dataset:

```bash
python prepare_dataset.py check
```

This will show:
- Number of images per split
- Number of labels per split
- Missing labels
- Class distribution

---

## 4. Training

### Step 1: Create Training YAML

```bash
python yolo_pipeline.py --create-yaml
```

This creates `datasets/digital_inspector.yaml` with your dataset configuration.

### Step 2: Start Training

**Basic training:**
```bash
python train_yolo.py
```

**With custom parameters:**
```bash
python train_yolo.py --epochs 100 --imgsz 1024 --batch 16
```

**Parameters:**
- `--epochs`: Number of training epochs (default: 50)
- `--imgsz`: Image size (default: 1024, use 640 for faster training)
- `--batch`: Batch size (default: 16, reduce if you run out of memory)
- `--model`: Model size (yolov8n.pt=smallest, yolov8s.pt=small, yolov8m.pt=medium, yolov8l.pt=large, yolov8x.pt=largest)
- `--device`: Device ('cpu', '0' for GPU 0, or None for auto)

**Example with smaller model (faster):**
```bash
python train_yolo.py --model yolov8n.pt --epochs 50 --imgsz 640 --batch 32
```

### Step 3: Monitor Training

Training will show:
- Loss curves
- Validation metrics
- Best model saved automatically

**Output location:**
- Training results: `runs/detect/train/`
- Best model: `runs/detect/train/weights/best.pt`
- Automatically copied to: `models/unified.pt`

### Training Tips

1. **Start small:** Use `yolov8n.pt` and `imgsz=640` for faster iteration
2. **Monitor overfitting:** Watch validation loss vs training loss
3. **Early stopping:** Training stops automatically if no improvement (patience=10)
4. **GPU:** Training is much faster on GPU. Use `--device 0` if you have one
5. **Memory:** If you get OOM errors, reduce `--batch` size

---

## 5. Using Your Trained Model

Once training completes, your model is automatically saved to `models/unified.pt`.

### Run Detection

```bash
python yolo_pipeline.py your_image.jpg
```

**Output:**
- `your_image_annotated.jpg` - Image with bounding boxes
- `your_image_detections.json` - Detection results

### Example Output JSON

```json
{
  "status": "success",
  "image_path": "your_image.jpg",
  "detections": [
    {
      "class": "signature",
      "class_id": 0,
      "confidence": 0.95,
      "bbox": {
        "xmin": 100,
        "ymin": 200,
        "xmax": 300,
        "ymax": 250
      }
    }
  ]
}
```

---

## 🚀 Quick Start Summary

```bash
# 1. Install
pip install -r requirements.txt

# 2. Prepare dataset
python prepare_dataset.py create
python prepare_dataset.py split --source test_images

# 3. Annotate (use LabelImg)
labelImg

# 4. Check dataset
python prepare_dataset.py check

# 5. Create YAML
python yolo_pipeline.py --create-yaml

# 6. Train
python train_yolo.py

# 7. Use model
python yolo_pipeline.py test_image.jpg
```

---

## 📊 Expected Results

With a good dataset (100+ images per class):
- **Training time:** 1-4 hours (depending on GPU/CPU and dataset size)
- **Accuracy:** 80-95% mAP (mean Average Precision)
- **Inference speed:** 10-50 FPS (depending on hardware)

---

## ❓ Troubleshooting

### "Model file not found"
- Make sure training completed successfully
- Check `runs/detect/train/weights/best.pt` exists
- It should be automatically copied to `models/unified.pt`

### "Dataset YAML not found"
- Run: `python yolo_pipeline.py --create-yaml`

### "Out of memory" during training
- Reduce batch size: `--batch 8` or `--batch 4`
- Reduce image size: `--imgsz 640`

### "No labels found"
- Make sure you've annotated images
- Check that `.txt` files are in `dataset/labels/train/` etc.
- Run `python prepare_dataset.py check` to verify

### Training is slow
- Use GPU: `--device 0`
- Use smaller model: `--model yolov8n.pt`
- Reduce image size: `--imgsz 640`

---

## 📚 Additional Resources

- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [LabelImg GitHub](https://github.com/HumanSignal/labelImg)
- [Roboflow](https://roboflow.com) - Online annotation tool

---

**Need help?** Check the annotation guide:
```bash
python prepare_dataset.py guide
```

