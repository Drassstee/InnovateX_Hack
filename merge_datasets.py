import os
import shutil
from pathlib import Path
import yaml

# ---------------------------------------------------------
# UNIFIED CLASS MAP (final, fixed)
# ---------------------------------------------------------
UNIFIED_CLASSES = {
    "signature": 0,
    "signnature": 0,
    "seal": 1,
    "stamp": 1,
    "qr_code": 2,
    "qr": 2,
    "qr code": 2,
    "qrcode": 2
}

# ---------------------------------------------------------
# CLEAN MERGE LOGIC
# ---------------------------------------------------------
def create_structure(root: Path):
    for split in ["train", "val", "test"]:
        (root / "images" / split).mkdir(parents=True, exist_ok=True)
        (root / "labels" / split).mkdir(parents=True, exist_ok=True)


def detect_numeric_map(dataset_yaml: Path):
    """
    Extract numeric-to-name class mapping from the dataset's YAML
    and convert it into unified IDs.
    Works for both dict-style and list-style 'names' fields.
    """
    with open(dataset_yaml, "r") as f:
        data = yaml.safe_load(f)

    if "names" not in data:
        return None

    names_field = data["names"]

    # Case 1: list-style
    if isinstance(names_field, list):
        mapping = {}
        for idx, name in enumerate(names_field):
            name = str(name).strip().lower()
            mapping[idx] = UNIFIED_CLASSES.get(name, None)
        return mapping

    # Case 2: dict-style
    if isinstance(names_field, dict):
        mapping = {}
        for idx, name in names_field.items():
            name = str(name).strip().lower()
            mapping[idx] = UNIFIED_CLASSES.get(name, None)
        return mapping

    # Unknown format
    return None


def rewrite_label(label_file: Path, numeric_map):
    """
    Rewrite each line of YOLO label file to unified class ID.
    Unknown classes are removed.
    """
    new_lines = []

    with open(label_file, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 5:
                continue

            cls = parts[0]

            if not cls.isdigit():
                continue

            old_id = int(cls)
            if old_id not in numeric_map:
                continue

            new_id = numeric_map[old_id]

            if new_id is None:
                continue  # ignore unknown class

            parts[0] = str(new_id)
            new_lines.append(" ".join(parts))

    # overwrite file
    with open(label_file, "w") as f:
        f.write("\n".join(new_lines))


def copy_dataset(src_root: Path, dst_root: Path):
    """
    Copy images + labels for train/val/test from one source dataset.
    Rewrite class IDs into unified IDs.
    """

    # find dataset YAML
    yaml_path = None
    for f in src_root.iterdir():
        if f.suffix == ".yaml":
            yaml_path = f
            break

    if yaml_path is None:
        raise ValueError(f"No data.yaml found inside {src_root}")

    numeric_map = detect_numeric_map(yaml_path)

    for split in ["train", "valid", "val", "test"]:
        src_img_dir = src_root / split / "images"
        src_lbl_dir = src_root / split / "labels"

        if not src_img_dir.exists():
            continue

        final_split = "val" if split == "valid" else split

        dst_img_dir = dst_root / "images" / final_split
        dst_lbl_dir = dst_root / "labels" / final_split

        dst_img_dir.mkdir(parents=True, exist_ok=True)
        dst_lbl_dir.mkdir(parents=True, exist_ok=True)

        for img_path in src_img_dir.iterdir():
            if img_path.suffix.lower() not in [".jpg", ".png", ".jpeg", ".bmp", ".webp"]:
                continue

            # copy image
            shutil.copy2(img_path, dst_img_dir / img_path.name)

            label_path = src_lbl_dir / (img_path.stem + ".txt")
            if label_path.exists():
                new_label_path = dst_lbl_dir / label_path.name
                shutil.copy2(label_path, new_label_path)
                rewrite_label(new_label_path, numeric_map)


# ---------------------------------------------------------
# MASTER MERGE
# ---------------------------------------------------------
def merge_all(signature, stamp, qr, output="dataset"):
    output = Path(output)
    shutil.rmtree(output, ignore_errors=True)

    print(f"Creating unified dataset at: {output}")
    create_structure(output)

    print("\n=== Merging: SIGNATURES ===")
    copy_dataset(Path(signature), output)

    print("\n=== Merging: STAMPS (SEAL) ===")
    copy_dataset(Path(stamp), output)

    if qr:
        print("\n=== Merging: QR ===")
        copy_dataset(Path(qr), output)
    else:
        print("\n=== Skipping QR dataset (not provided) ===")

    print("\n✓ Merge completed successfully")
    print("✓ Run: python prepare_dataset.py check")
    print("✓ Run: python train_yolo.py")


# ---------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Merge multiple single-class YOLO datasets into a unified 3-class YOLOv8 dataset.")
    parser.add_argument("--signature", required=True, help="Path: signatures dataset")
    parser.add_argument("--stamp", required=True, help="Path: stamps/seal dataset")
    #parser.add_argument("--qr", required=True, help="Path: qr dataset")
    parser.add_argument("--qr", required=False, default=None,
                        help="Optional QR dataset folder")
    parser.add_argument("--output", required=False, default="dataset",
                        help="Output merged dataset folder")

    args = parser.parse_args()

    merge_all(
        signature=args.signature,
        stamp=args.stamp,
        qr=args.qr,
        output=args.output
    )
