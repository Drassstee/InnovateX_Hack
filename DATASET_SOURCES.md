# 📦 Dataset Sources for Signatures, Stamps, and QR Codes

This guide shows you where to find free datasets and how to use them for training.

## 🎯 Best Options (Ready to Use)

### 1. **SignverOD Dataset** ⭐ RECOMMENDED
- **What:** 2,576 document images with 7,103 annotations
- **Classes:** Signature, initials, redaction, date
- **Format:** Already annotated
- **Link:** https://datasetninja.com/signver-od
- **Download:** Free, requires registration
- **Use:** Perfect for signatures!

### 2. **IIIT-AR-13K Dataset**
- **What:** 13,000 annotated page images
- **Classes:** Table, figure, natural image, logo, **signature**
- **Link:** https://arxiv.org/abs/2008.02569
- **Download:** Free
- **Use:** Great for signatures in documents

### 3. **QR Code Dataset V2**
- **What:** QR codes with various distortions
- **Link:** https://figshare.com/articles/dataset/QR_Code_Dataset_V2/28424213
- **Download:** Free
- **Use:** Perfect for QR code detection

### 4. **1,000 QR Code Images Dataset**
- **What:** 1,000 high-quality QR code images
- **Link:** https://data.mendeley.com/datasets/cmhh7744sp
- **Download:** Free (Mendeley)
- **Use:** Excellent for QR codes

### 5. **Stamp Verification Dataset**
- **What:** 400 invoice images with stamps
- **Link:** https://gts.ai/dataset-download/stamp-verification-dataset/
- **Download:** Free
- **Use:** Good for stamps/seals

### 6. **Handwritten Signature Dataset**
- **What:** Signatures from 27 individuals
- **Link:** https://gts.ai/dataset-download/handwritten-signature-dataset/
- **Download:** Free
- **Use:** Additional signature data

---

## 🔍 Where to Search

### **Roboflow Universe** ⭐ BEST FOR YOLO
- **Link:** https://universe.roboflow.com
- **Search for:** "signature", "stamp", "qr code"
- **Advantages:**
  - Pre-formatted for YOLO
  - Already split into train/val/test
  - Free datasets available
  - Easy download
- **How to use:**
  1. Go to roboflow.com/universe
  2. Search "signature detection" or "stamp detection"
  3. Click on a dataset
  4. Click "Download" → "YOLO v8"
  5. Extract to your `dataset/` folder

### **Kaggle**
- **Link:** https://www.kaggle.com/datasets
- **Search terms:**
  - "signature detection"
  - "document stamp"
  - "qr code dataset"
- **Advantages:** Large community, many free datasets

### **Hugging Face Datasets**
- **Link:** https://huggingface.co/datasets
- **Search:** "signature", "stamp", "qr code"
- **Advantages:** Easy to download with Python

### **GitHub**
- **Search:** "signature dataset", "stamp dataset", "qr code dataset"
- **Example:** https://github.com/BenSouchet/barcode-datasets

---

## 🛠️ Creating Your Own Dataset

### Option 1: Collect Real Images

**For Signatures:**
- Ask friends/family to sign documents
- Scan/photograph documents with signatures
- Use different papers, pens, lighting
- Aim for variety in size and style

**For Stamps:**
- Photograph official documents with stamps
- Use different stamp types (round, square, date stamps)
- Vary lighting and angles
- Include both colored and black stamps

**For QR Codes:**
- Generate QR codes online (free QR generators)
- Print and photograph them
- Vary: distance, angle, lighting, background
- Include damaged/distorted QR codes

### Option 2: Synthetic Data Generation

**QR Code Generator Script:**
```python
import qrcode
from PIL import Image
import random

# Generate 100 QR codes
for i in range(100):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"https://example.com/{i}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(f"dataset/images/train/qr_{i}.png")
```

**Install:** `pip install qrcode[pil]`

---

## 📥 How to Download and Use Datasets

### Method 1: Roboflow (Easiest)

1. Go to https://universe.roboflow.com
2. Search for your dataset
3. Click "Download" → "YOLO v8"
4. Extract the zip file
5. The structure will be:
   ```
   dataset/
     train/
       images/
       labels/
     valid/
       images/
       labels/
     test/
       images/
       labels/
   ```
6. Rename `valid` to `val` if needed
7. Move files to match our structure

### Method 2: Manual Download

1. Download dataset from source
2. Check format (COCO, Pascal VOC, or YOLO)
3. If not YOLO, convert using tools
4. Organize into our structure

### Method 3: Using Our Helper Script

See `download_datasets.py` (if we create it) for automated downloads.

---

## 🔄 Converting Datasets to YOLO Format

If you find a dataset in COCO or Pascal VOC format, you need to convert it.

### Using Roboflow:
1. Upload dataset to roboflow.com
2. Export as YOLO format
3. Download

### Using Python Script:
See conversion tools online or use roboflow's conversion API.

---

## 📊 Recommended Dataset Sizes

**Minimum (for testing):**
- 50 images per class
- Total: 150 images

**Good (for decent results):**
- 100-200 images per class
- Total: 300-600 images

**Excellent (for production):**
- 500+ images per class
- Total: 1500+ images

**Remember:** Quality > Quantity
- Better to have 100 well-annotated images than 1000 poorly annotated ones

---

## 🎯 Quick Start Strategy

### Step 1: Get Base Dataset
- Download SignverOD for signatures
- Download QR Code Dataset V2 for QR codes
- Download Stamp Verification Dataset for stamps

### Step 2: Supplement with Your Own
- Add 20-30 of your own images per class
- This helps the model work on YOUR specific use case

### Step 3: Data Augmentation
- Use YOLO's built-in augmentation during training
- Or use tools to augment before training

### Step 4: Combine and Train
- Merge all datasets
- Use `prepare_dataset.py check` to verify
- Train with `train_yolo.py`

---

## 🔗 Direct Download Links

1. **SignverOD:** https://datasetninja.com/signver-od
2. **QR Code V2:** https://figshare.com/articles/dataset/QR_Code_Dataset_V2/28424213
3. **Roboflow Universe:** https://universe.roboflow.com
4. **Kaggle:** https://www.kaggle.com/datasets
5. **Hugging Face:** https://huggingface.co/datasets

---

## 💡 Pro Tips

1. **Start Small:** Begin with 50 images per class to test your pipeline
2. **Mix Sources:** Combine multiple datasets for better generalization
3. **Add Your Own:** Include images similar to what you'll detect in production
4. **Check Quality:** Use `python prepare_dataset.py check` before training
5. **Augment:** Use data augmentation to effectively increase dataset size

---

## ❓ Need Help?

If you can't find a dataset:
1. Check Roboflow Universe first (easiest)
2. Search Kaggle
3. Create your own (start with 50 images)
4. Use synthetic data generation for QR codes

**Remember:** You can start training with as few as 50 images per class and improve later!

