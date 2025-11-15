#!/usr/bin/env python3
"""
Robust QR Code Detector for Scanned PDF Files
Handles poor quality scans, non-ideal backgrounds, and scanning artifacts.
Uses multiple detection methods with extensive preprocessing.
FIXED: Properly detects multiple QR codes even with same text content.
"""

import argparse
import json
import os
import sys
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import cv2
import numpy as np
from PIL import Image

# QR detector now works only with pre-converted images, no PDF conversion needed

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Try importing different QR detection libraries
try:
    from pyzbar import pyzbar
    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False

try:
    from qreader import QReader
    QREADER_AVAILABLE = True
except ImportError:
    QREADER_AVAILABLE = False

try:
    import qrdet
    QRDET_AVAILABLE = True
except ImportError:
    QRDET_AVAILABLE = False

# OpenCV QRCodeDetector is always available
OPENCV_AVAILABLE = True


def calculate_iou(box1: List, box2: List) -> float:
    """
    Calculate Intersection over Union (IoU) of two bounding boxes.
    Boxes are in format [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    """
    if box1 is None or box2 is None:
        return 0.0
    
    # Convert to rectangle format (min_x, min_y, max_x, max_y)
    def box_to_rect(box):
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        return (min(xs), min(ys), max(xs), max(ys))
    
    rect1 = box_to_rect(box1)
    rect2 = box_to_rect(box2)
    
    # Calculate intersection
    x_left = max(rect1[0], rect2[0])
    y_top = max(rect1[1], rect2[1])
    x_right = min(rect1[2], rect2[2])
    y_bottom = min(rect1[3], rect2[3])
    
    if x_right < x_left or y_bottom < y_top:
        return 0.0
    
    intersection = (x_right - x_left) * (y_bottom - y_top)
    
    # Calculate union
    area1 = (rect1[2] - rect1[0]) * (rect1[3] - rect1[1])
    area2 = (rect2[2] - rect2[0]) * (rect2[3] - rect2[1])
    union = area1 + area2 - intersection
    
    if union == 0:
        return 0.0
    
    return intersection / union


def is_duplicate_box(new_box: List, existing_boxes: List[List], iou_threshold: float = 0.5) -> bool:
    """Check if a bounding box is a duplicate of existing boxes."""
    if new_box is None:
        return False
    
    for existing_box in existing_boxes:
        if existing_box is None:
            continue
        iou = calculate_iou(new_box, existing_box)
        if iou > iou_threshold:
            return True
    return False


def draw_qr_boxes_on_image(image_path: str, qr_results: List[Dict], padding: int = 10, thickness: int = 10) -> bool:
    """
    Draw green rectangles around detected QR codes on an image.
    
    Args:
        image_path: Path to the image file
        qr_results: List of QR code detection results with 'box' field
        padding: Pixels to expand the box outward (creates gap between QR code and box)
        thickness: Thickness of the green border line
        
    Returns:
        True if image was modified and saved, False otherwise
    """
    if not qr_results:
        return False
    
    try:
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            return False
        
        height, width = image.shape[:2]
        
        # Draw rectangles for each QR code
        for qr in qr_results:
            box = qr.get('box')
            if box is None or len(box) < 4:
                continue
            
            # Expand the box outward by padding pixels
            # Calculate center of the box
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            center_x = sum(xs) / len(xs)
            center_y = sum(ys) / len(ys)
            
            # Expand each point outward from the center
            expanded_box = []
            for point in box:
                dx = point[0] - center_x
                dy = point[1] - center_y
                # Calculate distance from center
                dist = np.sqrt(dx*dx + dy*dy)
                if dist > 0:
                    # Expand outward by padding amount
                    scale = (dist + padding) / dist
                    new_x = int(center_x + dx * scale)
                    new_y = int(center_y + dy * scale)
                    # Clamp to image boundaries
                    new_x = max(0, min(width - 1, new_x))
                    new_y = max(0, min(height - 1, new_y))
                    expanded_box.append([new_x, new_y])
                else:
                    expanded_box.append(point)
            
            # Convert expanded box points to numpy array for drawing
            pts = np.array(expanded_box, dtype=np.int32)
            
            # Draw green border only (transparent filling = no fill, just outline)
            # Use polylines to draw the quadrilateral outline with increased thickness
            cv2.polylines(image, [pts], isClosed=True, color=(0, 255, 0), thickness=thickness)
        
        # Save the modified image
        cv2.imwrite(image_path, image)
        return True
        
    except Exception as e:
        print(f"  Warning: Could not draw boxes on {image_path}: {e}", file=sys.stderr)
        return False


class RobustQRDetector:
    """Robust QR code detector with multiple detection methods and preprocessing strategies."""
    
    def __init__(self):
        self.qreader = QReader() if QREADER_AVAILABLE else None
        self.opencv_detector = cv2.QRCodeDetector() if OPENCV_AVAILABLE else None
        
    def preprocess_image_fast(self, image: np.ndarray) -> List[Tuple[str, np.ndarray]]:
        """
        Fast preprocessing strategies (most common cases).
        """
        processed_images = []
        
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # Try original color first (often works best)
            processed_images.append(('original_color', image))
        else:
            gray = image.copy()
        
        # Original grayscale
        processed_images.append(('original_gray', gray))
        
        # Adaptive thresholding (fast and effective)
        adaptive_thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        processed_images.append(('adaptive_thresh', adaptive_thresh))
        
        # Adaptive thresholding with larger block
        adaptive_thresh_large = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 21, 5
        )
        processed_images.append(('adaptive_thresh_large', adaptive_thresh_large))
        
        return processed_images
    
    def preprocess_image_extended(self, image: np.ndarray) -> List[Tuple[str, np.ndarray]]:
        """
        Extended preprocessing strategies (for difficult cases).
        """
        processed_images = []
        
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Otsu thresholding
        _, otsu_thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(('otsu_thresh', otsu_thresh))
        
        # Morphological operations to fill gaps
        adaptive_thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        kernel = np.ones((3, 3), np.uint8)
        morph_closed = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
        processed_images.append(('morph_closed', morph_closed))
        
        # Inverted threshold
        inverted = cv2.bitwise_not(adaptive_thresh)
        processed_images.append(('inverted', inverted))
        
        # Denoised + adaptive (slower but sometimes needed)
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        denoised_adaptive = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        processed_images.append(('denoised_adaptive', denoised_adaptive))
        
        return processed_images
    
    def detect_with_pyzbar(self, image: np.ndarray) -> List[Dict]:
        """Detect QR codes using pyzbar (very robust for damaged codes)."""
        if not PYZBAR_AVAILABLE:
            return []
        
        results = []
        try:
            # pyzbar works with PIL Image or numpy array
            if isinstance(image, np.ndarray):
                # Convert to PIL Image
                if len(image.shape) == 3:
                    pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                else:
                    pil_image = Image.fromarray(image)
            else:
                pil_image = image
            
            decoded_objects = pyzbar.decode(pil_image)
            
            for obj in decoded_objects:
                if obj.type == 'QRCODE':
                    # Get bounding box coordinates
                    points = obj.polygon
                    if len(points) >= 4:
                        # Convert to list format
                        box = [[int(p.x), int(p.y)] for p in points[:4]]
                    else:
                        # Fallback: use rect
                        box = [
                            [int(obj.rect.left), int(obj.rect.top)],
                            [int(obj.rect.left + obj.rect.width), int(obj.rect.top)],
                            [int(obj.rect.left + obj.rect.width), int(obj.rect.top + obj.rect.height)],
                            [int(obj.rect.left), int(obj.rect.top + obj.rect.height)]
                        ]
                    
                    results.append({
                        'text': obj.data.decode('utf-8'),
                        'confidence': 1.0,
                        'box': box,
                        'method': 'pyzbar'
                    })
        except Exception as e:
            pass  # Silently fail and try next method
        
        return results
    
    def detect_with_qreader(self, image: np.ndarray) -> List[Dict]:
        """Detect QR codes using QReader (handles challenging scenarios)."""
        if not QREADER_AVAILABLE or self.qreader is None:
            return []
        
        results = []
        try:
            # QReader expects PIL Image or numpy array
            if isinstance(image, np.ndarray):
                if len(image.shape) == 3:
                    pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                else:
                    pil_image = Image.fromarray(image)
            else:
                pil_image = image
            
            # Try with bounding boxes
            try:
                decoded_qrs = self.qreader.detect_and_decode(image=pil_image, return_bboxes=True)
                if decoded_qrs:
                    for bbox, text in decoded_qrs:
                        if text and text.strip():
                            # Convert bbox from (x1, y1, x2, y2) to [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
                            if bbox:
                                x1, y1, x2, y2 = bbox
                                box = [[int(x1), int(y1)], [int(x2), int(y1)], 
                                       [int(x2), int(y2)], [int(x1), int(y2)]]
                            else:
                                box = None
                            
                            results.append({
                                'text': text,
                                'confidence': 1.0,
                                'box': box,
                                'method': 'qreader'
                            })
            except:
                # Fallback: try without bboxes
                decoded_texts = self.qreader.detect_and_decode(image=pil_image)
                if decoded_texts:
                    for text in decoded_texts:
                        if text and text.strip():
                            results.append({
                                'text': text,
                                'confidence': 1.0,
                                'box': None,
                                'method': 'qreader'
                            })
        except Exception as e:
            pass  # Silently fail and try next method
        
        return results
    
    def detect_with_qrdet(self, image: np.ndarray) -> List[Dict]:
        """Detect QR codes using qrdet (excellent for multiple QR codes)."""
        if not QRDET_AVAILABLE:
            return []
        
        results = []
        try:
            # qrdet expects numpy array
            if isinstance(image, np.ndarray):
                if len(image.shape) == 3:
                    # Convert BGR to RGB
                    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                else:
                    # Convert grayscale to RGB
                    rgb_image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            else:
                rgb_image = np.array(image)
            
            # Detect QR codes - qrdet.detect returns list of detections
            detections = qrdet.detect(rgb_image)
            
            # Handle different return formats
            if isinstance(detections, list):
                for det in detections:
                    # Handle dict format
                    if isinstance(det, dict):
                        data = det.get('data') or det.get('text') or det.get('value')
                        if data:
                            # Get bounding box
                            bbox = det.get('bbox') or det.get('box') or det.get('quad')
                            box = None
                            
                            if bbox is not None:
                                # Handle different bbox formats
                                if isinstance(bbox, (list, tuple, np.ndarray)):
                                    if len(bbox) == 4:
                                        # Could be [x1, y1, x2, y2] or [[x1,y1], [x2,y2], ...]
                                        if isinstance(bbox[0], (list, tuple, np.ndarray)):
                                            # Already in point format
                                            box = [[int(p[0]), int(p[1])] for p in bbox[:4]]
                                        else:
                                            # [x1, y1, x2, y2] format
                                            x1, y1, x2, y2 = bbox
                                            box = [[int(x1), int(y1)], [int(x2), int(y1)], 
                                                   [int(x2), int(y2)], [int(x1), int(y2)]]
                            
                            results.append({
                                'text': str(data),
                                'confidence': det.get('confidence', det.get('score', 1.0)),
                                'box': box,
                                'method': 'qrdet'
                            })
                    # Handle string format (just decoded text)
                    elif isinstance(det, str) and det:
                        results.append({
                            'text': det,
                            'confidence': 1.0,
                            'box': None,
                            'method': 'qrdet'
                        })
        except Exception as e:
            # Try alternative qrdet API if available
            try:
                # Some versions might use different API
                if hasattr(qrdet, 'QRDetector'):
                    detector = qrdet.QRDetector()
                    if isinstance(image, np.ndarray):
                        if len(image.shape) == 3:
                            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                        else:
                            rgb_image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
                    else:
                        rgb_image = np.array(image)
                    detections = detector.detect(rgb_image)
                    # Process similar to above
            except:
                pass  # Silently fail
        
        return results
    
    def detect_with_opencv(self, image: np.ndarray) -> List[Dict]:
        """Detect QR codes using OpenCV QRCodeDetector."""
        if not OPENCV_AVAILABLE or self.opencv_detector is None:
            return []
        
        results = []
        try:
            # Try detectAndDecodeMulti for multiple QR codes
            ret, decoded_info, points, _ = self.opencv_detector.detectAndDecodeMulti(image)
            
            if ret and decoded_info is not None:
                for i, text in enumerate(decoded_info):
                    if text and text.strip():  # Non-empty decoded text
                        if points is not None and i < len(points):
                            # Convert points to list format
                            box = [[int(p[0]), int(p[1])] for p in points[i]]
                        else:
                            box = None
                        
                        results.append({
                            'text': text,
                            'confidence': 1.0,
                            'box': box,
                            'method': 'opencv'
                        })
        except Exception as e:
            pass  # Silently fail and try next method
        
        return results
    
    def detect_qr_codes_from_pil(self, pil_image: Image.Image, fast_mode: bool = True) -> Dict:
        """
        Detect QR codes directly from a PIL Image (faster, no file I/O).
        
        Args:
            pil_image: PIL Image object
            fast_mode: If True, prioritize speed over exhaustive search
            
        Returns:
            Dictionary with detection results
        """
        # Convert PIL Image to OpenCV format (BGR)
        image_array = np.array(pil_image)
        if len(image_array.shape) == 3:
            if image_array.shape[2] == 4:  # RGBA
                image = cv2.cvtColor(image_array, cv2.COLOR_RGBA2BGR)
            else:  # RGB
                image = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        else:  # Grayscale
            image = image_array
        
        return self._detect_qr_codes_from_cv_image(image, fast_mode)
    
    def detect_qr_codes(self, image_path: str, fast_mode: bool = True) -> Dict:
        """
        Optimized detection function with early exit and smart strategy selection.
        FIXED: Uses bounding box IoU for deduplication, not just text content.
        OPTIMIZED: Fast mode tries quick methods first, only uses expensive preprocessing if needed.
        
        Args:
            image_path: Path to the image file
            fast_mode: If True, prioritize speed over exhaustive search
            
        Returns:
            Dictionary with detection results
        """
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            return {
                "status": "error",
                "message": f"Could not load image: {image_path}"
            }
        
        return self._detect_qr_codes_from_cv_image(image, fast_mode)
    
    def _detect_qr_codes_from_cv_image(self, image: np.ndarray, fast_mode: bool = True) -> Dict:
        """
        Optimized internal method to detect QR codes from OpenCV image array.
        OPTIMIZED: Early exits, parallel detection, cached preprocessing.
        
        Args:
            image: OpenCV image (BGR format)
            fast_mode: If True, prioritize speed over exhaustive search
            
        Returns:
            Dictionary with detection results
        """
        all_results = []
        seen_boxes = []  # Track bounding boxes for deduplication
        
        def add_results(results: List[Dict], strategy_name: str, scale: float = 1.0):
            """Helper to add results with deduplication."""
            for result in results:
                # Scale boxes if needed
                if scale != 1.0 and result.get('box'):
                    result['box'] = [[int(p[0]/scale), int(p[1]/scale)] for p in result['box']]
                
                if not is_duplicate_box(result.get('box'), seen_boxes, iou_threshold=0.3):
                    result['preprocessing'] = strategy_name
                    all_results.append(result)
                    if result.get('box'):
                        seen_boxes.append(result['box'])
        
        def try_detection_methods(processed_img: np.ndarray, strategy_name: str, skip_parallel: bool = False) -> List[Dict]:
            """Try all detection methods in parallel for a preprocessed image.
            
            Args:
                processed_img: Preprocessed image to detect on
                strategy_name: Name of preprocessing strategy
                skip_parallel: If True, only try OpenCV (for very fast early checks)
            """
            results = []
            
            # Run detection methods in parallel for speed
            def run_opencv():
                if OPENCV_AVAILABLE:
                    return self.detect_with_opencv(processed_img)
                return []
            
            def run_pyzbar():
                if PYZBAR_AVAILABLE:
                    return self.detect_with_pyzbar(processed_img)
                return []
            
            def run_qrdet():
                if QRDET_AVAILABLE:
                    return self.detect_with_qrdet(processed_img)
                return []
            
            # Always try OpenCV first (fastest)
            if OPENCV_AVAILABLE:
                opencv_results = run_opencv()
                if opencv_results:
                    results.extend(opencv_results)
            
            # Try other methods in parallel (different methods can find different codes!)
            # Only skip if explicitly requested (for very early checks)
            if not skip_parallel:
                with ThreadPoolExecutor(max_workers=2) as executor:
                    futures = []
                    if PYZBAR_AVAILABLE:
                        futures.append(executor.submit(run_pyzbar))
                    if QRDET_AVAILABLE:
                        futures.append(executor.submit(run_qrdet))
                    
                    for future in as_completed(futures):
                        try:
                            method_results = future.result()
                            if method_results:
                                results.extend(method_results)
                        except:
                            pass
            
            return results
        
        # Cache grayscale conversion (used multiple times)
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Get all preprocessing strategies (restore original logic)
        processed_fast = self.preprocess_image_fast(image)
        processed_extended = self.preprocess_image_extended(image)
        
        # PHASE 1: Try all fast preprocessing strategies
        for strategy_name, processed_img in processed_fast:
            results = try_detection_methods(processed_img, strategy_name)
            if results:
                add_results(results, strategy_name)
        
        # PHASE 2: Try extended preprocessing strategies
        # Always try extended preprocessing - some QR codes need it (pages 2, 5, 8)
        for strategy_name, processed_img in processed_extended:
            results = try_detection_methods(processed_img, strategy_name)
            if results:
                add_results(results, strategy_name)
        
        # PHASE 3: Multi-scale detection (only if no results found)
        if not all_results:
            for scale in [1.5, 0.75, 2.0]:
                scaled = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                processed_scaled = self.preprocess_image_fast(scaled)
                
                # Try first 2 fast strategies at each scale
                for strategy_name, processed_img in processed_scaled[:2]:
                    results = try_detection_methods(processed_img, f"{strategy_name}_scale{scale}")
                    if results:
                        # Scale boxes back to original size
                        for r in results:
                            if r.get('box'):
                                r['box'] = [[int(p[0]/scale), int(p[1]/scale)] for p in r['box']]
                        add_results(results, f"{strategy_name}_scale{scale}")
                    
                    # Early exit if we found codes
                    if all_results:
                        break
                
                if all_results:
                    break
        
        return {
            "status": "success",
            "data": all_results,
            "count": len(all_results)
        }


def detect_qr_codes_from_image(image_path: str, fast_mode: bool = True) -> Dict:
    """
    Convenience function to detect QR codes from an image file.
    
    Args:
        image_path: Path to the image file
        fast_mode: If True, prioritize speed over exhaustive search
        
    Returns:
        Dictionary with detection results
    """
    detector = RobustQRDetector()
    return detector.detect_qr_codes(image_path, fast_mode=fast_mode)


def process_image_directory(directory_path: str, fast_mode: bool = True, max_workers: int = 4) -> Dict:
    """
    Process all image folders in a directory and detect QR codes.
    OPTIMIZED: Parallel processing of images for speed.
    Expects directory structure: directory_path/folder_name/page_images.png
    
    Args:
        directory_path: Path to directory containing folders with converted page images
        fast_mode: If True, prioritize speed over exhaustive search
        max_workers: Number of parallel workers for image processing
        
    Returns:
        Dictionary with aggregated results from all folders
    """
    directory = Path(directory_path)
    if not directory.exists() or not directory.is_dir():
        return {
            "status": "error",
            "message": f"Directory not found: {directory_path}"
        }
    
    # Find all subdirectories (each represents a converted PDF)
    image_folders = sorted([f for f in directory.iterdir() if f.is_dir()])
    
    if not image_folders:
        return {
            "status": "error",
            "message": f"No folders found in directory: {directory_path}"
        }
    
    print(f"Found {len(image_folders)} folder(s) in {directory_path}")
    
    detector = RobustQRDetector()
    all_results = []
    # Track seen boxes per page to avoid cross-page deduplication
    seen_boxes_per_page = {}  # {(folder_name, page_num): [boxes]}
    
    def add_results(results: List[Dict], folder_name: str, page_num: int):
        """Helper to add results with deduplication (per page only)."""
        # Get seen boxes for this specific page
        page_key = (folder_name, page_num)
        if page_key not in seen_boxes_per_page:
            seen_boxes_per_page[page_key] = []
        
        seen_boxes = seen_boxes_per_page[page_key]
        
        for result in results:
            # Only deduplicate within the same page
            if not is_duplicate_box(result.get('box'), seen_boxes, iou_threshold=0.3):
                result['pdf_file'] = folder_name  # Using folder name as identifier
                result['page'] = page_num
                all_results.append(result)
                if result.get('box'):
                    seen_boxes.append(result['box'])
    
    def process_single_image(image_file: Path, folder_name: str) -> Tuple[str, int, Dict, str]:
        """Process a single image and return results.
        
        Returns:
            Tuple of (folder_name, page_num, result_dict, image_path)
        """
        try:
            # Extract page number from filename
            page_num = 1
            filename = image_file.stem
            if '_page' in filename:
                try:
                    page_num = int(filename.split('_page')[-1])
                except:
                    pass
            elif filename.replace(folder_name, '').strip():
                try:
                    page_num = int(''.join(filter(str.isdigit, filename.split('_')[-1])))
                except:
                    pass
            
            # Detect QR codes
            result = detector.detect_qr_codes(str(image_file), fast_mode=fast_mode)
            
            # If no results found, always try extended search (even in fast mode)
            # This ensures we don't miss difficult QR codes
            if result["status"] == "success" and not result["data"]:
                result = detector.detect_qr_codes(str(image_file), fast_mode=False)
            
            return (folder_name, page_num, result, str(image_file))
        except Exception as e:
            return (folder_name, 0, {"status": "error", "message": str(e)}, str(image_file))
    
    # Process each folder (each folder contains pages from one PDF)
    for folder in image_folders:
        print(f"\nProcessing: {folder.name}")
        
        # Find all PNG images in the folder
        image_files = sorted([f for f in folder.iterdir() 
                             if f.is_file() and f.suffix.lower() in ['.png', '.jpg', '.jpeg']])
        
        if not image_files:
            print(f"  No image files found in {folder.name}")
            continue
        
        print(f"  Found {len(image_files)} page image(s)")
        
        # Process images in parallel for speed
        with ThreadPoolExecutor(max_workers=min(max_workers, len(image_files))) as executor:
            futures = {executor.submit(process_single_image, img, folder.name): img 
                      for img in image_files}
            
            for future in as_completed(futures):
                folder_name, page_num, result, image_path = future.result()
                
                if result["status"] == "success" and result["data"]:
                    print(f"  Page {page_num}: Found {result['count']} QR code(s)")
                    add_results(result["data"], folder_name, page_num)
                    
                    # Draw green boxes around QR codes on the image
                    if draw_qr_boxes_on_image(image_path, result["data"]):
                        print(f"    → Annotated QR codes on image")
                elif result["status"] == "error":
                    print(f"  Page {page_num}: Error - {result.get('message', 'Unknown')}", file=sys.stderr)
                else:
                    print(f"  Page {page_num}: No QR codes found")
    
    return {
        "status": "success",
        "directory": str(directory_path),
        "folders_processed": len(image_folders),
        "data": all_results,
        "count": len(all_results)
    }


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Robust QR Code Detector for pre-converted image directories and single images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all image folders in a directory (each folder contains page images)
  python qr_detector.py converted_images/
  
  # Process a single image file
  python qr_detector.py --image test_images/qr1.webp
  
  # Output as JSON
  python qr_detector.py converted_images/ --json
        """
    )
    
    parser.add_argument(
        'directory',
        type=str,
        nargs='?',
        default=None,
        help='Path to directory containing folders with converted page images (or use --image for single image)'
    )
    
    parser.add_argument(
        '--image',
        type=str,
        default=None,
        help='Path to a single image file to analyze (alternative to directory)'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    
    parser.add_argument(
        '--fast',
        action='store_true',
        default=True,
        help='Use fast mode (default: True). Set --no-fast for exhaustive search'
    )
    
    parser.add_argument(
        '--no-fast',
        dest='fast',
        action='store_false',
        help='Disable fast mode for exhaustive search'
    )
    
    args = parser.parse_args()
    
    # Determine if processing directory or single image
    if args.image:
        # Single image mode
        if not Path(args.image).exists():
            print(f"Error: File not found: {args.image}", file=sys.stderr)
            sys.exit(1)
        
        detector = RobustQRDetector()
        result = detector.detect_qr_codes(args.image, fast_mode=args.fast)
        
        # Output results
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result["status"] == "success":
                print(f"Found {result['count']} QR code(s):")
                for i, qr in enumerate(result["data"], 1):
                    print(f"\nQR Code {i}:")
                    print(f"  Text: {qr['text']}")
                    print(f"  Method: {qr['method']}")
                    print(f"  Preprocessing: {qr.get('preprocessing', 'N/A')}")
                    if qr.get('box'):
                        print(f"  Box: {qr['box']}")
            else:
                print(f"Error: {result.get('message', 'Unknown error')}", file=sys.stderr)
                sys.exit(1)
    
    elif args.directory:
        # Directory mode - process all image folders
        result = process_image_directory(args.directory, fast_mode=args.fast)
        
        # Output results
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result["status"] == "success":
                print(f"\n{'='*60}")
                print(f"Summary:")
                print(f"  Folders processed: {result['folders_processed']}")
                print(f"  Total QR codes found: {result['count']}")
                print(f"{'='*60}")
                
                if result["data"]:
                    print(f"\nQR Codes by PDF and Page:")
                    current_pdf = None
                    current_page = None
                    
                    for i, qr in enumerate(result["data"], 1):
                        pdf_name = qr.get('pdf_file', 'Unknown')
                        page_num = qr.get('page', 0)
                        
                        if pdf_name != current_pdf or page_num != current_page:
                            if current_pdf is not None:
                                print()
                            print(f"\n  {pdf_name} - Page {page_num}:")
                            current_pdf = pdf_name
                            current_page = page_num
                        
                        print(f"    QR Code: {qr['text']}")
                        print(f"      Method: {qr['method']}, Preprocessing: {qr.get('preprocessing', 'N/A')}")
            else:
                print(f"Error: {result.get('message', 'Unknown error')}", file=sys.stderr)
                sys.exit(1)
    
    else:
        parser.print_help()
        print("\nError: Please provide either a directory path or --image argument", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
