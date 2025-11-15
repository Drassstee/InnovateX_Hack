"""
Dataset Preparation Helper Script for YOLO Training

This script helps you organize your images and create the proper directory structure
for YOLO training. It also provides utilities to split your dataset into train/val/test.
"""

import os
import shutil
import json
import random
from pathlib import Path
from typing import List, Tuple


def create_dataset_structure(base_path: str = "dataset"):
    """
    Creates the YOLO dataset directory structure.
    
    Structure:
    dataset/
      images/
        train/
        val/
        test/
      labels/
        train/
        val/
        test/
    """
    base = Path(base_path)
    
    # Create directories
    dirs = [
        base / "images" / "train",
        base / "images" / "val",
        base / "images" / "test",
        base / "labels" / "train",
        base / "labels" / "val",
        base / "labels" / "test",
    ]
    
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {dir_path}")
    
    print(f"\n✓ Dataset structure created at: {base.absolute()}")
    return base


def split_dataset(
    source_images_dir: str,
    output_dataset_dir: str = "dataset",
    train_ratio: float = 0.7,
    val_ratio: float = 0.2,
    test_ratio: float = 0.1,
    seed: int = 42
):
    """
    Splits images from source directory into train/val/test sets.
    
    Args:
        source_images_dir: Directory containing your images
        output_dataset_dir: Where to create the dataset structure
        train_ratio: Proportion for training (default: 0.7)
        val_ratio: Proportion for validation (default: 0.2)
        test_ratio: Proportion for testing (default: 0.1)
        seed: Random seed for reproducibility
    """
    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 0.01:
        raise ValueError("Ratios must sum to 1.0")
    
    # Create dataset structure
    dataset_base = create_dataset_structure(output_dataset_dir)
    
    # Get all image files
    source = Path(source_images_dir)
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    images = [f for f in source.iterdir() 
              if f.suffix.lower() in image_extensions and f.is_file()]
    
    if not images:
        print(f"⚠ No images found in {source_images_dir}")
        return
    
    print(f"\nFound {len(images)} images")
    
    # Shuffle with seed
    random.seed(seed)
    random.shuffle(images)
    
    # Calculate split indices
    n_total = len(images)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)
    
    # Split
    train_images = images[:n_train]
    val_images = images[n_train:n_train + n_val]
    test_images = images[n_train + n_val:]
    
    print(f"Split: {len(train_images)} train, {len(val_images)} val, {len(test_images)} test")
    
    # Copy images
    def copy_images(img_list, split_name):
        for img in img_list:
            dest = dataset_base / "images" / split_name / img.name
            shutil.copy2(img, dest)
            print(f"  Copied {img.name} -> images/{split_name}/")
    
    print("\nCopying training images...")
    copy_images(train_images, "train")
    
    print("\nCopying validation images...")
    copy_images(val_images, "val")
    
    print("\nCopying test images...")
    copy_images(test_images, "test")
    
    print(f"\n✓ Dataset split complete!")
    print(f"\nNext steps:")
    print(f"1. Annotate your images using LabelImg or another tool")
    print(f"2. Save annotations in YOLO format to dataset/labels/")
    print(f"3. Run: python train_yolo.py")


def check_dataset(dataset_dir: str = "dataset"):
    """
    Checks if your dataset is properly formatted and shows statistics.
    """
    dataset = Path(dataset_dir)
    
    if not dataset.exists():
        print(f"❌ Dataset directory not found: {dataset_dir}")
        return False
    
    splits = ["train", "val", "test"]
    issues = []
    stats = {}
    
    for split in splits:
        img_dir = dataset / "images" / split
        label_dir = dataset / "labels" / split
        
        if not img_dir.exists():
            issues.append(f"Missing: images/{split}/")
            continue
        
        images = list(img_dir.glob("*.*"))
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        images = [img for img in images if img.suffix.lower() in image_extensions]
        
        labels = []
        if label_dir.exists():
            labels = list(label_dir.glob("*.txt"))
        
        stats[split] = {
            "images": len(images),
            "labels": len(labels),
            "missing_labels": []
        }
        
        # Check for missing labels
        for img in images:
            label_file = label_dir / f"{img.stem}.txt"
            if not label_file.exists():
                stats[split]["missing_labels"].append(img.name)
    
    # Print statistics
    print("\n" + "="*60)
    print("DATASET STATISTICS")
    print("="*60)
    
    for split in splits:
        if split in stats:
            s = stats[split]
            print(f"\n{split.upper()}:")
            print(f"  Images: {s['images']}")
            print(f"  Labels: {s['labels']}")
            if s['missing_labels']:
                print(f"  ⚠ Missing labels: {len(s['missing_labels'])}")
                if len(s['missing_labels']) <= 5:
                    for missing in s['missing_labels']:
                        print(f"    - {missing}")
                else:
                    print(f"    - {s['missing_labels'][0]} ... and {len(s['missing_labels'])-1} more")
    
    # Check class distribution
    print("\n" + "="*60)
    print("CLASS DISTRIBUTION")
    print("="*60)
    
    class_names = {0: "signature", 1: "stamp", 2: "qr_code"}
    class_counts = {0: 0, 1: 0, 2: 0}
    
    for split in splits:
        label_dir = dataset / "labels" / split
        if label_dir.exists():
            for label_file in label_dir.glob("*.txt"):
                try:
                    with open(label_file, 'r') as f:
                        for line in f:
                            parts = line.strip().split()
                            if parts:
                                class_id = int(parts[0])
                                if class_id in class_counts:
                                    class_counts[class_id] += 1
                except Exception as e:
                    issues.append(f"Error reading {label_file}: {e}")
    
    for class_id, count in class_counts.items():
        print(f"  {class_names[class_id]}: {count} instances")
    
    if issues:
        print("\n⚠ ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("\n✓ Dataset looks good!")
        return True


def print_annotation_guide():
    """
    Prints a guide on how to annotate images for YOLO.
    """
    guide = """
╔════════════════════════════════════════════════════════════════╗
║           YOLO ANNOTATION GUIDE                                ║
╚════════════════════════════════════════════════════════════════╝

1. INSTALL LABELIMG (Recommended):
   pip install labelImg
   labelImg

2. ANNOTATION FORMAT (YOLO):
   Each image needs a .txt file with the same name.
   Format: class_id center_x center_y width height
   - All coordinates are normalized (0.0 to 1.0)
   - center_x, center_y: center of bounding box
   - width, height: size of bounding box

3. CLASS MAPPING:
   0 = signature
   1 = stamp
   2 = qr_code

4. EXAMPLE ANNOTATION (image001.jpg -> image001.txt):
   0 0.5 0.5 0.2 0.1
   (signature at center, 20% width, 10% height)

5. ANNOTATION TOOLS:
   - LabelImg (GUI): pip install labelImg
   - Roboflow (Online): https://roboflow.com
   - CVAT (Advanced): https://cvat.org

6. QUICK START WITH LABELIMG:
   a) Open LabelImg
   b) Change format to YOLO (top menu)
   c) Open directory: dataset/images/train
   d) Set save directory: dataset/labels/train
   e) Use keyboard shortcuts:
      - W: Create box
      - D: Next image
      - A: Previous image
      - 0, 1, 2: Select class (signature, stamp, qr_code)

7. TIPS:
   - Annotate tightly around objects
   - Include some context but not too much
   - Be consistent with your annotations
   - Aim for at least 100 images per class for good results
"""
    print(guide)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="YOLO Dataset Preparation Helper")
    parser.add_argument("command", choices=["create", "split", "check", "guide"],
                       help="Command to run")
    parser.add_argument("--source", type=str, default="test_images",
                       help="Source directory for images (for split command)")
    parser.add_argument("--output", type=str, default="dataset",
                       help="Output dataset directory")
    parser.add_argument("--train-ratio", type=float, default=0.7,
                       help="Training set ratio (default: 0.7)")
    parser.add_argument("--val-ratio", type=float, default=0.2,
                       help="Validation set ratio (default: 0.2)")
    parser.add_argument("--test-ratio", type=float, default=0.1,
                       help="Test set ratio (default: 0.1)")
    
    args = parser.parse_args()
    
    if args.command == "create":
        create_dataset_structure(args.output)
        print("\n✓ Use 'split' command to organize your images")
        
    elif args.command == "split":
        split_dataset(
            args.source,
            args.output,
            args.train_ratio,
            args.val_ratio,
            args.test_ratio
        )
        
    elif args.command == "check":
        check_dataset(args.output)
        
    elif args.command == "guide":
        print_annotation_guide()

