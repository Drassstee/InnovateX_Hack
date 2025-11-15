#!/usr/bin/env python3
"""
Digital Inspector
Main entry point for scanning PDF documents to find and mark stamps, signatures, and QR codes.
Generates JSON output in the format required by the hackathon.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import cv2
import numpy as np
import warnings

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Import converter and detector functions
from pdf_to_image_converter import convert_pdf_to_images, process_directory
from qr_detector import RobustQRDetector
from json_generator import (
    convert_xyxy_to_xywh,
    convert_quad_to_xywh,
    generate_annotations_json,
    normalize_category
)
from draw_annotations import draw_annotations_for_page

# Try importing YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Warning: ultralytics not available. YOLO detection will be skipped.", file=sys.stderr)


# Default YOLO model path
DEFAULT_YOLO_MODEL = "runs/detect/train8/weights/best.pt"
FALLBACK_YOLO_MODEL = "yolov8s.pt"

# YOLO class names mapping
YOLO_CLASS_NAMES = {
    0: "signature",
    1: "stamp",
    2: "qr_code"
}

# Global model cache to avoid reloading
_yolo_model_cache = {}


def get_yolo_model(model_path: str = None):
    """
    Get YOLO model instance, using cache to avoid reloading.
    OPTIMIZATION: Model is loaded once and cached for all images.
    
    Args:
        model_path: Path to YOLO model file (default: DEFAULT_YOLO_MODEL)
    
    Returns:
        YOLO model instance or None if unavailable
    """
    if not YOLO_AVAILABLE:
        return None
    
    if model_path is None:
        model_path = DEFAULT_YOLO_MODEL
    
    model_file = Path(model_path)
    
    # Try default model, fallback to base model
    if not model_file.exists():
        if Path(FALLBACK_YOLO_MODEL).exists():
            model_path = FALLBACK_YOLO_MODEL
        else:
            return None
    
    # Use cache to avoid reloading model (MAJOR OPTIMIZATION)
    cache_key = str(Path(model_path).resolve())
    if cache_key not in _yolo_model_cache:
        try:
            _yolo_model_cache[cache_key] = YOLO(str(model_path))
        except Exception as e:
            print(f"  Warning: Failed to load YOLO model: {e}", file=sys.stderr)
            return None
    
    return _yolo_model_cache[cache_key]


def detect_with_yolo_cached(image: np.ndarray, model, conf_threshold: float = 0.25) -> List[Dict]:
    """
    Detect signatures and stamps using YOLO model on pre-loaded image.
    OPTIMIZED: Uses pre-loaded image and cached model (no file I/O).
    
    Args:
        image: OpenCV image (BGR format) - already loaded
        model: YOLO model instance (cached)
        conf_threshold: Confidence threshold for detections
    
    Returns:
        List of detection dictionaries with category and bbox
    """
    if model is None:
        return []
    
    try:
        # Run inference on pre-loaded image (no file I/O)
        results = model(image, conf=conf_threshold, verbose=False)
        
        detections = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Get box coordinates (xyxy format)
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0].cpu().numpy())
                class_id = int(box.cls[0].cpu().numpy())
                class_name = YOLO_CLASS_NAMES.get(class_id, f"class_{class_id}")
                
                # Convert to required format (x, y, width, height)
                bbox = convert_xyxy_to_xywh(x1, y1, x2, y2)
                
                # Only include signatures and stamps (not QR codes from YOLO)
                if class_name in ["signature", "stamp"]:
                    detections.append({
                        "category": class_name,
                        "bbox": bbox,
                        "confidence": confidence
                    })
        
        return detections
        
    except Exception as e:
        print(f"  Warning: YOLO detection error: {e}", file=sys.stderr)
        return []


def detect_qr_codes_from_image(image: np.ndarray, qr_detector: RobustQRDetector, fast_mode: bool = True) -> List[Dict]:
    """
    Detect QR codes in a pre-loaded image.
    OPTIMIZED: Uses pre-loaded image instead of loading from disk.
    
    Args:
        image: OpenCV image (BGR format) - already loaded
        qr_detector: RobustQRDetector instance
        fast_mode: Use fast detection mode
    
    Returns:
        List of detection dictionaries with category and bbox
    """
    try:
        # Use internal method that accepts OpenCV image directly (no file I/O)
        result = qr_detector._detect_qr_codes_from_cv_image(image, fast_mode=fast_mode)
        
        if result["status"] != "success" or not result["data"]:
            return []
        
        detections = []
        
        for qr in result["data"]:
            box = qr.get("box")
            
            if box:
                # Convert quadrilateral to (x, y, width, height)
                bbox = convert_quad_to_xywh(box)
            else:
                continue
            
            detections.append({
                "category": "qr",
                "bbox": bbox,
                "confidence": qr.get("confidence", 1.0)
            })
        
        return detections
        
    except Exception as e:
        print(f"  Warning: QR detection error: {e}", file=sys.stderr)
        return []


def process_single_page(
    img_file: Path,
    yolo_model,
    qr_detector: RobustQRDetector,
    fast_mode: bool,
    conf_threshold: float
) -> Tuple[str, List[Dict], str, int]:
    """
    Process a single page image.
    OPTIMIZED: Loads image once, runs all detections, returns results.
    
    Args:
        img_file: Path to image file
        yolo_model: Cached YOLO model instance
        qr_detector: RobustQRDetector instance
        fast_mode: Use fast QR detection mode
        conf_threshold: YOLO confidence threshold
    
    Returns:
        Tuple of (page_key, page_detections, image_path, page_num)
    """
    # Extract page number from filename
    page_num = 1
    filename = img_file.stem
    
    # Try to extract page number from filename
    if '_page' in filename:
        try:
            page_num = int(filename.split('_page')[-1])
        except:
            pass
    else:
        try:
            parts = filename.split('_')
            if parts:
                last_part = parts[-1]
                if last_part.isdigit():
                    page_num = int(last_part)
        except:
            pass
    
    page_key = f"page_{page_num}"
    image_path = str(img_file)
    
    # Load image ONCE for all detections (OPTIMIZATION)
    image = cv2.imread(image_path)
    if image is None:
        return (page_key, [], image_path, page_num)
    
    # Collect all detections for this page
    page_detections = []
    
    # Detect with YOLO (signatures and stamps) - uses pre-loaded image
    if yolo_model is not None:
        yolo_detections = detect_with_yolo_cached(image, yolo_model, conf_threshold)
        page_detections.extend(yolo_detections)
    
    # Detect QR codes - uses pre-loaded image
    if qr_detector:
        qr_detections = detect_qr_codes_from_image(image, qr_detector, fast_mode)
        page_detections.extend(qr_detections)
    
    # Add image_path to each detection for JSON generator
    for det in page_detections:
        det["image_path"] = image_path
    
    return (page_key, page_detections, image_path, page_num)


def process_pdf_pages(
    pdf_name: str,
    image_folder: Path,
    yolo_model_path: str = None,
    qr_detector: RobustQRDetector = None,
    fast_mode: bool = True,
    conf_threshold: float = 0.25,
    max_workers: int = 4
) -> Dict[str, List[Dict]]:
    """
    Process all page images for a single PDF with parallelization.
    OPTIMIZED: Processes pages in parallel, uses cached model, loads images once.
    
    Args:
        pdf_name: Name of the PDF file (without extension)
        image_folder: Path to folder containing page images
        yolo_model_path: Path to YOLO model (used to get cached model)
        qr_detector: RobustQRDetector instance
        fast_mode: Use fast QR detection mode
        conf_threshold: YOLO confidence threshold
        max_workers: Number of parallel workers
    
    Returns:
        Dictionary mapping page keys to lists of detections
    """
    pages_data = {}
    
    # Find all image files in the folder
    image_files = sorted([
        f for f in image_folder.iterdir()
        if f.is_file() and f.suffix.lower() in ['.png', '.jpg', '.jpeg']
    ])
    
    if not image_files:
        return pages_data
    
    print(f"  Processing {len(image_files)} page(s)...")
    
    # Get cached YOLO model (load once, reuse for all pages) - already loaded in inspect_pdfs
    # This is just for backward compatibility, model should be passed in
    yolo_model = None
    if YOLO_AVAILABLE:
        yolo_model = get_yolo_model(yolo_model_path)
    
    # Process pages in parallel (MAJOR OPTIMIZATION)
    with ThreadPoolExecutor(max_workers=min(max_workers, len(image_files))) as executor:
        # Submit all tasks
        futures = {
            executor.submit(
                process_single_page,
                img_file,
                yolo_model,
                qr_detector,
                fast_mode,
                conf_threshold
            ): img_file
            for img_file in image_files
        }
        
        # Collect results as they complete
        for future in as_completed(futures):
            try:
                page_key, page_detections, image_path, page_num = future.result()
                
                # Draw annotations on the image if there are any detections
                if page_detections:
                    print(f"    Page {page_num}: Found {len(page_detections)} detection(s)")
                    
                    # Separate YOLO and QR detections for drawing
                    yolo_detections = [d for d in page_detections if d.get("category") in ["signature", "stamp"]]
                    qr_detections = [d for d in page_detections if d.get("category") == "qr"]
                    
                    # Draw annotations on the image
                    if draw_annotations_for_page(image_path, yolo_detections, qr_detections, padding=20, thickness=12):
                        print(f"      → Annotated image with bounding boxes")
                    
                    pages_data[page_key] = page_detections
                else:
                    # Still add page with image path for page_size (even if no detections)
                    pages_data[page_key] = [{"image_path": image_path}]
                    
            except Exception as e:
                img_file = futures[future]
                print(f"  Warning: Error processing {img_file.name}: {e}", file=sys.stderr)
                # Add placeholder for failed page
                pages_data[f"page_unknown"] = [{"image_path": str(img_file)}]
    
    return pages_data


def inspect_pdfs(
    pdf_directory: str,
    output_dir_name: str = None,
    fast_mode: bool = True,
    dpi: int = 200,
    yolo_model_path: str = None,
    conf_threshold: float = 0.25,
    json_output_path: str = None,
    max_workers: int = 4
) -> dict:
    """
    Main inspection function: converts PDFs to images, detects all elements, and generates JSON.
    
    Args:
        pdf_directory: Path to directory containing PDF files
        output_dir_name: Name for the output directory (default: pdf_directory + '_converted')
        fast_mode: Use fast QR detection mode
        dpi: Resolution for image conversion
        yolo_model_path: Path to YOLO model file
        conf_threshold: Confidence threshold for YOLO detections
        json_output_path: Path to save JSON output file (default: annotations.json in output directory)
        
    Returns:
        Dictionary with inspection results
    """
    pdf_dir = Path(pdf_directory)
    if not pdf_dir.exists() or not pdf_dir.is_dir():
        return {
            "status": "error",
            "message": f"PDF directory not found: {pdf_directory}"
        }
    
    # Determine output directory path (same level as input directory)
    parent_dir = pdf_dir.parent
    if output_dir_name is None:
        output_dir_name = f"{pdf_dir.name}_converted"
    output_dir = parent_dir / output_dir_name
    
    print(f"{'='*60}")
    print(f"Digital Inspector")
    print(f"{'='*60}")
    print(f"Input directory: {pdf_dir}")
    print(f"Output directory: {output_dir}")
    print(f"{'='*60}\n")
    
    # STEP 1: Convert PDFs to images
    print("STEP 1: Converting PDFs to images...")
    print("-" * 60)
    
    try:
        # Create output directory if it doesn't exist
        output_dir.mkdir(exist_ok=True)
        
        # Process all PDFs in the directory, save to output directory
        conversion_summary = process_directory(
            str(pdf_dir),
            output_format='PNG',
            dpi=dpi,
            output_base_dir=str(output_dir)
        )
        
        print(f"\n✓ Conversion complete!")
        print(f"  PDFs processed: {conversion_summary['total_pdfs']}")
        print(f"  Successful: {conversion_summary['successful']}")
        print(f"  Failed: {conversion_summary['failed']}")
        print(f"  Total pages: {conversion_summary['total_pages']}")
        
        if conversion_summary['failed'] > 0:
            print(f"\n⚠ Warning: {conversion_summary['failed']} PDF(s) failed to convert")
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error during PDF conversion: {str(e)}"
        }
    
    # STEP 2: Detect all elements (signatures, stamps, QR codes)
    print(f"\n{'='*60}")
    print("STEP 2: Detecting signatures, stamps, and QR codes...")
    print("-" * 60)
    
    try:
        # Initialize QR detector
        qr_detector = RobustQRDetector()
        
        # Load YOLO model ONCE (cached for all pages) - MAJOR OPTIMIZATION
        if YOLO_AVAILABLE:
            yolo_model = get_yolo_model(yolo_model_path)
            if yolo_model:
                print(f"✓ YOLO model loaded and cached (will be reused for all pages)")
            else:
                print(f"⚠ YOLO model not available, skipping YOLO detection")
        else:
            yolo_model = None
        
        # Find all image folders (each represents a converted PDF)
        image_folders = sorted([f for f in output_dir.iterdir() if f.is_dir()])
        
        if not image_folders:
            return {
                "status": "error",
                "message": f"No image folders found in {output_dir}"
            }
        
        print(f"Found {len(image_folders)} PDF folder(s) to process\n")
        
        # Collect all detections organized by PDF
        detections_by_pdf = {}
        
        for folder in image_folders:
            pdf_name = f"{folder.name}.pdf"  # Add .pdf extension for JSON output
            print(f"Processing: {pdf_name}")
            
            # Process all pages in this PDF (OPTIMIZED: parallel processing)
            pages_data = process_pdf_pages(
                folder.name,
                folder,
                yolo_model_path,
                qr_detector,
                fast_mode,
                conf_threshold,
                max_workers
            )
            
            if pages_data:
                detections_by_pdf[pdf_name] = pages_data
                total_detections = sum(len(dets) for dets in pages_data.values())
                print(f"  ✓ Found {total_detections} total detection(s) across {len(pages_data)} page(s)\n")
            else:
                print(f"  ⚠ No detections found\n")
        
        # STEP 3: Generate JSON output
        print(f"{'='*60}")
        print("STEP 3: Generating JSON annotations...")
        print("-" * 60)
        
        # Determine JSON output path
        if json_output_path is None:
            json_output_path = str(output_dir.parent / "annotations.json")
        
        # Generate JSON
        json_result = generate_annotations_json(detections_by_pdf, json_output_path)
        
        # Count total detections
        total_detections = sum(
            len(annotations)
            for pdf_data in json_result.values()
            for page_data in pdf_data.values()
            for annotations in [page_data.get("annotations", [])]
        )
        
        print(f"✓ JSON generation complete!")
        print(f"  Total annotations: {total_detections}")
        print(f"  PDFs processed: {len(json_result)}")
        
        # Return comprehensive results
        return {
            "status": "success",
            "input_directory": str(pdf_dir),
            "output_directory": str(output_dir),
            "json_output": json_output_path,
            "conversion": conversion_summary,
            "detection": {
                "pdfs_processed": len(detections_by_pdf),
                "total_annotations": total_detections,
                "annotations_by_pdf": {
                    pdf: sum(len(pages_data[page]) for page in pages_data)
                    for pdf, pages_data in detections_by_pdf.items()
                }
            }
        }
    
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": f"Error during detection: {str(e)}",
            "traceback": traceback.format_exc()
        }


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Digital Inspector: Scan PDFs to find and mark stamps, signatures, and QR codes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all PDFs in a directory
  python digital_inspector.py test_pdfs/
  
  # Specify custom output directory name
  python digital_inspector.py test_pdfs/ --output converted_pages
  
  # Use exhaustive search mode (slower but more thorough)
  python digital_inspector.py test_pdfs/ --no-fast
  
  # Custom DPI for conversion
  python digital_inspector.py test_pdfs/ --dpi 300
  
  # Custom YOLO model path
  python digital_inspector.py test_pdfs/ --yolo-model models/custom.pt
  
  # Custom JSON output path
  python digital_inspector.py test_pdfs/ --json-output results.json
        """
    )
    
    parser.add_argument(
        'pdf_directory',
        type=str,
        help='Path to directory containing PDF files'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Name for output directory (default: <input_directory>_converted)'
    )
    
    parser.add_argument(
        '--dpi',
        type=int,
        default=200,
        help='Resolution (DPI) for image conversion (default: 200)'
    )
    
    parser.add_argument(
        '--fast',
        action='store_true',
        default=True,
        help='Use fast QR detection mode (default: True)'
    )
    
    parser.add_argument(
        '--no-fast',
        dest='fast',
        action='store_false',
        help='Disable fast mode for exhaustive QR code search'
    )
    
    parser.add_argument(
        '--yolo-model',
        type=str,
        default=None,
        help=f'Path to YOLO model file (default: {DEFAULT_YOLO_MODEL})'
    )
    
    parser.add_argument(
        '--conf-threshold',
        type=float,
        default=0.25,
        help='Confidence threshold for YOLO detections (default: 0.25)'
    )
    
    parser.add_argument(
        '--json-output',
        type=str,
        default=None,
        help='Path to save JSON annotations file (default: annotations.json in parent of output directory)'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        default=4,
        help='Number of parallel workers for page processing (default: 4)'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results summary as JSON'
    )
    
    args = parser.parse_args()
    
    # Run inspection
    result = inspect_pdfs(
        args.pdf_directory,
        output_dir_name=args.output,
        fast_mode=args.fast,
        dpi=args.dpi,
        yolo_model_path=args.yolo_model,
        conf_threshold=args.conf_threshold,
        json_output_path=args.json_output,
        max_workers=args.workers
    )
    
    # Output results
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["status"] == "success":
            print(f"\n{'='*60}")
            print("FINAL SUMMARY")
            print(f"{'='*60}")
            print(f"Input: {result['input_directory']}")
            print(f"Output: {result['output_directory']}")
            print(f"JSON: {result['json_output']}")
            print(f"\nConversion:")
            print(f"  PDFs: {result['conversion']['total_pdfs']}")
            print(f"  Pages: {result['conversion']['total_pages']}")
            print(f"\nDetection:")
            print(f"  PDFs processed: {result['detection']['pdfs_processed']}")
            print(f"  Total annotations: {result['detection']['total_annotations']}")
            print(f"{'='*60}")
        else:
            print(f"Error: {result.get('message', 'Unknown error')}", file=sys.stderr)
            if 'traceback' in result:
                print(result['traceback'], file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
