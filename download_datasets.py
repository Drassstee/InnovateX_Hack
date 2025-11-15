"""
Helper script to download and prepare datasets from various sources.

This script helps you download datasets and convert them to YOLO format.
"""

import os
import sys
import zipfile
import requests
from pathlib import Path
import shutil


def download_file(url, output_path, description="file"):
    """
    Downloads a file from URL to output_path.
    """
    print(f"Downloading {description}...")
    print(f"URL: {url}")
    print(f"Save to: {output_path}")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.1f}%", end='', flush=True)
        
        print(f"\n✓ Downloaded: {output_path}")
        return True
        
    except Exception as e:
        print(f"\n❌ Error downloading: {e}")
        return False


def extract_zip(zip_path, extract_to):
    """
    Extracts a zip file to the specified directory.
    """
    print(f"Extracting {zip_path} to {extract_to}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"✓ Extracted to: {extract_to}")
        return True
    except Exception as e:
        print(f"❌ Error extracting: {e}")
        return False


def print_dataset_sources():
    """
    Prints available dataset sources with download instructions.
    """
    sources = """
╔════════════════════════════════════════════════════════════════╗
║           AVAILABLE DATASET SOURCES                            ║
╚════════════════════════════════════════════════════════════════╝

1. ROBOFLOW UNIVERSE (⭐ RECOMMENDED - Easiest)
   URL: https://universe.roboflow.com
   
   Steps:
   a) Go to https://universe.roboflow.com
   b) Search for "signature detection", "stamp detection", or "qr code"
   c) Click on a dataset
   d) Click "Download" → "YOLO v8"
   e) Extract the zip file
   f) The dataset will be in YOLO format already!

2. SIGNVEROD DATASET (Signatures)
   URL: https://datasetninja.com/signver-od
   - 2,576 images with 7,103 annotations
   - Already annotated
   - Requires registration

3. QR CODE DATASET V2
   URL: https://figshare.com/articles/dataset/QR_Code_Dataset_V2/28424213
   - Free download
   - Various QR code images

4. KAGGLE
   URL: https://www.kaggle.com/datasets
   - Search: "signature detection", "stamp", "qr code"
   - Many free datasets
   - Requires Kaggle account

5. HUGGING FACE
   URL: https://huggingface.co/datasets
   - Search for your dataset
   - Can download with Python

6. CREATE YOUR OWN
   - Collect real images
   - Use QR code generator for QR codes
   - Annotate with LabelImg

════════════════════════════════════════════════════════════════

QUICK START:
1. Go to https://universe.roboflow.com
2. Search and download datasets in YOLO format
3. Extract to your dataset/ folder
4. Run: python prepare_dataset.py check
5. Train: python train_yolo.py

For detailed instructions, see: DATASET_SOURCES.md
"""
    print(sources)


def help_roboflow_setup():
    """
    Provides step-by-step instructions for Roboflow.
    """
    instructions = """
╔════════════════════════════════════════════════════════════════╗
║           ROBOFLOW UNIVERSE SETUP GUIDE                        ║
╚════════════════════════════════════════════════════════════════╝

STEP 1: Go to Roboflow Universe
   https://universe.roboflow.com

STEP 2: Search for Datasets
   Try these searches:
   - "signature detection"
   - "document signature"
   - "stamp detection"
   - "qr code detection"

STEP 3: Choose a Dataset
   - Look for datasets with good ratings
   - Check number of images
   - Verify it has the classes you need

STEP 4: Download
   - Click on the dataset
   - Click "Download" button
   - Select "YOLO v8" format
   - Click "Download" again
   - Save the zip file

STEP 5: Extract and Organize
   - Extract the zip file
   - You'll see folders: train/, valid/, test/
   - Each folder has: images/ and labels/
   
   To merge with your existing dataset:
   
   Option A: Manual
   1. Copy images from downloaded/train/images/ to dataset/images/train/
   2. Copy labels from downloaded/train/labels/ to dataset/labels/train/
   3. Repeat for valid/val and test/
   
   Option B: Use our script (if we add merge functionality)

STEP 6: Verify
   python prepare_dataset.py check

════════════════════════════════════════════════════════════════

TIPS:
- Roboflow datasets are already in YOLO format ✓
- They're already split into train/val/test ✓
- Many are free to use ✓
- You can combine multiple datasets

Need help? Check DATASET_SOURCES.md for more options.
"""
    print(instructions)


def create_qr_codes(output_dir="dataset/images/train", count=100):
    """
    Generates synthetic QR code images.
    Requires: pip install qrcode[pil]
    """
    try:
        import qrcode
        from PIL import Image, ImageDraw, ImageFont
        import random
    except ImportError:
        print("❌ Missing dependencies. Install with:")
        print("   pip install qrcode[pil]")
        return False
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating {count} QR code images...")
    
    for i in range(count):
        # Create QR code
        qr = qrcode.QRCode(
            version=random.randint(1, 5),  # Size variation
            box_size=random.randint(8, 15),
            border=random.randint(2, 5),
        )
        
        # Random data
        data = f"https://example.com/qr/{i}/{random.randint(1000,9999)}"
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create image with random colors
        fill_color = "black" if random.random() > 0.1 else "darkblue"
        back_color = "white" if random.random() > 0.1 else "lightgray"
        
        img = qr.make_image(fill_color=fill_color, back_color=back_color)
        
        # Save
        img_path = output_path / f"qr_synthetic_{i:04d}.png"
        img.save(img_path)
        
        if (i + 1) % 10 == 0:
            print(f"  Generated {i + 1}/{count}...")
    
    print(f"✓ Generated {count} QR codes in {output_path}")
    print(f"\n⚠ Note: You still need to annotate these images!")
    print(f"   Use LabelImg to create labels in dataset/labels/train/")
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Dataset Download Helper")
    parser.add_argument("command", choices=["sources", "roboflow", "generate-qr"],
                       help="Command to run")
    parser.add_argument("--count", type=int, default=100,
                       help="Number of QR codes to generate")
    parser.add_argument("--output", type=str, default="dataset/images/train",
                       help="Output directory for generated QR codes")
    
    args = parser.parse_args()
    
    if args.command == "sources":
        print_dataset_sources()
    elif args.command == "roboflow":
        help_roboflow_setup()
    elif args.command == "generate-qr":
        create_qr_codes(args.output, args.count)

