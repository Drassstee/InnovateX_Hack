# 🚀 Quick Start Guide

Follow these steps in order to train your YOLO model.

## Step-by-Step Instructions

### 1️⃣ Install Requirements
```bash
pip install -r requirements.txt
```

### 2️⃣ Prepare Your Dataset

**Option A: Automatic (if you have images in one folder)**
```bash
# Create dataset structure
python prepare_dataset.py create

# Split your images (from test_images folder)
python prepare_dataset.py split --source test_images --output dataset
```

**Option B: Manual**
- Create folders: `dataset/images/train/`, `dataset/images/val/`, `dataset/images/test/`
- Copy your images into these folders

### 3️⃣ Annotate Your Images

**Install LabelImg:**
```bash
pip install labelImg
```

**Annotate:**
```bash
labelImg
```

1. Open LabelImg
2. Format → YOLO
3. Open: `dataset/images/train`
4. Save to: `dataset/labels/train`
5. Draw boxes and label:
   - `0` = signature
   - `1` = stamp  
   - `2` = qr_code

**Repeat for val and test folders!**

### 4️⃣ Verify Dataset
```bash
python prepare_dataset.py check
```

This shows you:
- How many images you have
- How many annotations
- Missing labels
- Class distribution

### 5️⃣ Create Training Config
```bash
python yolo_pipeline.py --create-yaml
```

### 6️⃣ Train Your Model
```bash
python train_yolo.py
```

**Training options:**
- Fast training (smaller model): `python train_yolo.py --model yolov8n.pt --imgsz 640`
- Better accuracy (larger model): `python train_yolo.py --model yolov8m.pt --epochs 100`
- Use GPU: `python train_yolo.py --device 0`

### 7️⃣ Use Your Model
```bash
python yolo_pipeline.py your_image.jpg
```

---

## 📝 What You Need

- **Images:** At least 100 images per class (signature, stamp, qr_code)
- **Time:** 1-4 hours for training (depending on dataset size and hardware)
- **Patience:** Annotation takes time but is crucial!

---

## 🆘 Need Help?

- **Annotation guide:** `python prepare_dataset.py guide`
- **Full guide:** See `TRAINING_GUIDE.md`
- **Check dataset:** `python prepare_dataset.py check`

---

## ✅ Checklist

- [ ] Installed requirements
- [ ] Created dataset structure
- [ ] Split images into train/val/test
- [ ] Annotated all images (train, val, test)
- [ ] Verified dataset with `check` command
- [ ] Created YAML config
- [ ] Trained model
- [ ] Tested on new images

Good luck! 🎯

