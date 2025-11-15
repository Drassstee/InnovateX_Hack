# 🎯 Where to Get 100+ Images for Training

## ⭐ EASIEST OPTION: Roboflow Universe

**Best for beginners!** Pre-formatted for YOLO, already annotated.

1. **Go to:** https://universe.roboflow.com
2. **Search for:**
   - "signature detection"
   - "stamp detection" 
   - "qr code detection"
3. **Download:** Click dataset → Download → YOLO v8
4. **Extract:** Unzip and use!

**Why Roboflow?**
- ✅ Already in YOLO format
- ✅ Already split (train/val/test)
- ✅ Free datasets available
- ✅ No conversion needed

**Get help:**
```bash
python download_datasets.py roboflow
```

---

## 📦 Free Dataset Sources

### For Signatures:
1. **SignverOD** - 2,576 images
   - https://datasetninja.com/signver-od
   - Already annotated!

2. **IIIT-AR-13K** - 13,000 images (includes signatures)
   - https://arxiv.org/abs/2008.02569

### For QR Codes:
1. **QR Code Dataset V2**
   - https://figshare.com/articles/dataset/QR_Code_Dataset_V2/28424213

2. **1,000 QR Code Images**
   - https://data.mendeley.com/datasets/cmhh7744sp

3. **Generate Your Own** (easiest for QR codes!)
   ```bash
   pip install qrcode[pil]
   python download_datasets.py generate-qr --count 100
   ```

### For Stamps:
1. **Stamp Verification Dataset** - 400 images
   - https://gts.ai/dataset-download/stamp-verification-dataset/

---

## 🚀 Quick Start (3 Steps)

### Step 1: Get Datasets from Roboflow
```bash
# See instructions
python download_datasets.py roboflow
```
Then go to https://universe.roboflow.com and download datasets

### Step 2: Generate QR Codes (Optional)
```bash
pip install qrcode[pil]
python download_datasets.py generate-qr --count 100
```

### Step 3: Organize Your Dataset
```bash
# Create structure
python prepare_dataset.py create

# Check what you have
python prepare_dataset.py check
```

---

## 💡 Recommended Strategy

**Option A: Quick Start (Roboflow)**
1. Download 3 datasets from Roboflow (one for each class)
2. Extract to your dataset folder
3. Annotate if needed
4. Train!

**Option B: Mix Sources**
1. Get SignverOD for signatures
2. Generate 100 QR codes (synthetic)
3. Download stamp dataset
4. Add 20-30 of your own images
5. Combine and train

**Option C: Create Your Own**
- Collect real images
- Use LabelImg to annotate
- Start with 50 per class, expand later

---

## 📊 Minimum Requirements

**To start training:**
- 50 images per class = 150 total (minimum)
- 100 images per class = 300 total (recommended)
- 200+ images per class = 600+ total (best)

**Remember:** You can start small and add more data later!

---

## 🛠️ Helper Commands

```bash
# See all dataset sources
python download_datasets.py sources

# Get Roboflow setup guide
python download_datasets.py roboflow

# Generate synthetic QR codes
python download_datasets.py generate-qr --count 100

# Check your dataset
python prepare_dataset.py check
```

---

## 📚 Full Guide

For detailed information, see: **DATASET_SOURCES.md**

---

**TL;DR:** Go to https://universe.roboflow.com, search and download datasets in YOLO format! 🎯

