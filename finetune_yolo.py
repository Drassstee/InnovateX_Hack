"""
YOLO Fine-Tuning Script

Fine-tunes your document model (signatures + stamps)
for higher accuracy and stability.
"""

from ultralytics import YOLO
from pathlib import Path
import sys


def finetune(
    model_path="runs/detect/train8/weights/best.pt",
    data_yaml="datasets/digital_inspector.yaml",
    epochs=80,
    imgsz=1024,
    batch=8,
    device="0"
):
    model_path = Path(model_path)

    if not model_path.exists():
        print(f"❌ ERROR: Base model not found: {model_path}")
        sys.exit(1)

    print(f"\nLoading base model for fine-tuning: {model_path}")
    model = YOLO(str(model_path))

    print("\nStarting Phase 1: Frozen Backbone (20 epochs)...")
    model.train(
        data=data_yaml,
        epochs=20,
        imgsz=imgsz,
        batch=batch,
        device=device,
        lr0=0.0005,        # lower LR than initial training
        freeze=[0, 1, 2],  # freeze early layers
        mosaic=0.1,
        hsv_v=0.3,
        perspective=0.0,
        translate=0.05,
        scale=0.3,
        shear=5,
        flipud=0.0,
        project="runs/detect",
        name="finetune_frozen",
    )

    print("\nStarting Phase 2: Full Fine-Tuning...")
    model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        lr0=0.0002,
        freeze=False,
        mosaic=0.2,
        hsv_v=0.4,
        translate=0.1,
        scale=0.5,
        shear=6,
        flipud=0.0,
        copy_paste=0.1,
        project="runs/detect",
        name="finetune_full",
    )

    print("\n✓ Fine-tuning complete!")
    print("Best model will be inside:")
    print("  runs/detect/finetune_full/weights/best.pt")


if __name__ == "__main__":
    finetune()
