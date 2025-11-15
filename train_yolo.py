"""
YOLO Training Script

This script trains a unified YOLO model for detecting signatures, stamps, and QR codes.
"""

import sys
import shutil
from pathlib import Path
from ultralytics import YOLO


def train_model(
    data_yaml: str = "datasets/digital_inspector.yaml",
    model: str = "yolov8s.pt",
    epochs: int = 50,
    imgsz: int = 768,
    batch: int = 8,
    device: str = '0',
    project: str = "runs/detect",
    name: str = "train"
):
    """
    Trains a YOLO model.
    
    Args:
        data_yaml: Path to dataset YAML file
        model: Model to use (yolov8n.pt, yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt)
        epochs: Number of training epochs
        imgsz: Image size for training
        batch: Batch size
        device: Device to use (None = auto, 'cpu', '0' for GPU 0, etc.)
        project: Project directory
        name: Experiment name
    """
    # Check if YAML exists
    yaml_path = Path(data_yaml)
    if not yaml_path.exists():
        print(f"❌ Error: Dataset YAML not found: {data_yaml}")
        print("\nCreate it first:")
        print("  python yolo_pipeline.py --create-yaml")
        sys.exit(1)
    
    # Check if dataset exists
    print("Checking dataset...")
    from prepare_dataset import check_dataset
    dataset_dir = Path(data_yaml).parent.parent / "dataset"
    if not check_dataset(str(dataset_dir)):
        print("\n⚠ Warning: Dataset has issues. Continue anyway? (y/n): ", end="")
        response = input().strip().lower()
        if response != 'y':
            print("Training cancelled.")
            sys.exit(1)
    
    print(f"\n{'='*60}")
    print("STARTING YOLO TRAINING")
    print(f"{'='*60}")
    print(f"Model: {model}")
    print(f"Dataset: {data_yaml}")
    print(f"Epochs: {epochs}")
    print(f"Image size: {imgsz}")
    print(f"Batch size: {batch}")
    print(f"Device: {device if device else 'auto'}")
    print(f"{'='*60}\n")
    
    # Load model
    print(f"Loading model: {model}...")
    try:
        yolo_model = YOLO(model)
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        print("\nThe model will be downloaded automatically on first use.")
        print("Make sure you have internet connection.")
        sys.exit(1)
    
    # Train
    try:
        results = yolo_model.train(
            data=str(yaml_path),
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            device=device,
            project=project,
            name=name,
            patience=10,  # Early stopping patience
            save=True,
            plots=True,
            mosaic=0.0,
            auto_augment=None,
            workers=0
        )
        
        print(f"\n{'='*60}")
        print("TRAINING COMPLETE!")
        print(f"{'='*60}")
        
        # Find best model
        best_model = Path(project) / name / "weights" / "best.pt"
        if best_model.exists():
            print(f"\n✓ Best model saved to: {best_model}")
            
            # Copy to models directory
            models_dir = Path("models")
            models_dir.mkdir(exist_ok=True)
            unified_model = models_dir / "unified.pt"
            
            shutil.copy2(best_model, unified_model)
            print(f"✓ Copied to: {unified_model}")
            print(f"\nYou can now use the model:")
            print(f"  python yolo_pipeline.py your_image.jpg")
        else:
            print(f"\n⚠ Best model not found at expected location: {best_model}")
            print("Check the runs directory for your trained model.")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Training error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Train YOLO Model")
    parser.add_argument("--data", type=str, default="datasets/digital_inspector.yaml",
                       help="Path to dataset YAML file")
    parser.add_argument("--model", type=str, default="yolov8s.pt",
                       choices=["yolov8n.pt", "yolov8s.pt", "yolov8m.pt", "yolov8l.pt", "yolov8x.pt"],
                       help="YOLO model to use (n=nanos, s=small, m=medium, l=large, x=xlarge)")
    parser.add_argument("--epochs", type=int, default=50,
                       help="Number of training epochs")
    parser.add_argument("--imgsz", type=int, default=768,
                       help="Image size for training")
    parser.add_argument("--batch", type=int, default=8,
                       help="Batch size")
    parser.add_argument("--device", type=str, default=None,
                       help="Device to use (None=auto, 'cpu', '0' for GPU 0)")
    
    args = parser.parse_args()
    
    train_model(
        data_yaml=args.data,
        model=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device
    )

