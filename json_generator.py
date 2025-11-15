#!/usr/bin/env python3
"""
JSON Generator for Digital Inspector
Converts detection results to the required JSON format matching selected_annotations.json
"""

import json
from pathlib import Path
from typing import Dict, List, Any
import cv2


def convert_xyxy_to_xywh(x1: float, y1: float, x2: float, y2: float) -> Dict[str, float]:
    """
    Convert bounding box from (x1, y1, x2, y2) format to (x, y, width, height) format.
    
    Args:
        x1, y1: Top-left corner
        x2, y2: Bottom-right corner
    
    Returns:
        Dictionary with x, y, width, height
    """
    x = float(x1)
    y = float(y1)
    width = float(x2 - x1)
    height = float(y2 - y1)
    
    return {
        "x": x,
        "y": y,
        "width": width,
        "height": height
    }


def convert_quad_to_xywh(box: List[List[int]]) -> Dict[str, float]:
    """
    Convert quadrilateral bounding box (4 points) to (x, y, width, height) format.
    
    Args:
        box: List of 4 points [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    
    Returns:
        Dictionary with x, y, width, height
    """
    if not box or len(box) < 4:
        return {"x": 0, "y": 0, "width": 0, "height": 0}
    
    # Get min/max coordinates
    xs = [p[0] for p in box]
    ys = [p[1] for p in box]
    
    x = float(min(xs))
    y = float(min(ys))
    width = float(max(xs) - min(xs))
    height = float(max(ys) - min(ys))
    
    return {
        "x": x,
        "y": y,
        "width": width,
        "height": height
    }


def calculate_area(bbox: Dict[str, float]) -> float:
    """Calculate area from bounding box."""
    return bbox["width"] * bbox["height"]


def get_image_size(image_path: str) -> Dict[str, int]:
    """
    Get image dimensions.
    
    Args:
        image_path: Path to image file
    
    Returns:
        Dictionary with width and height
    """
    try:
        img = cv2.imread(image_path)
        if img is not None:
            height, width = img.shape[:2]
            return {"width": int(width), "height": int(height)}
    except Exception:
        pass
    
    # Fallback: try with PIL
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            width, height = img.size
            return {"width": int(width), "height": int(height)}
    except Exception:
        pass
    
    # Default fallback
    return {"width": 0, "height": 0}


def normalize_category(category: str) -> str:
    """
    Normalize category name to match required format.
    
    Args:
        category: Category from detection (e.g., "qr_code", "signature", "stamp")
    
    Returns:
        Normalized category ("qr", "signature", "stamp")
    """
    category_lower = category.lower()
    
    # Map variations to standard format
    if "qr" in category_lower or category_lower == "qr_code":
        return "qr"
    elif "signature" in category_lower:
        return "signature"
    elif "stamp" in category_lower:
        return "stamp"
    
    return category_lower


def generate_annotations_json(
    detections_by_pdf: Dict[str, Dict[str, List[Dict]]],
    output_path: str = None
) -> Dict[str, Any]:
    """
    Generate JSON in the format matching selected_annotations.json.
    
    Args:
        detections_by_pdf: Dictionary structure:
            {
                "pdf_name.pdf": {
                    "page_1": [
                        {
                            "category": "signature",
                            "bbox": {"x": 510, "y": 146, "width": 250, "height": 98.89},
                            "image_path": "/path/to/image.png"
                        },
                        ...
                    ],
                    ...
                },
                ...
            }
        output_path: Optional path to save JSON file
    
    Returns:
        Dictionary in the required JSON format
    """
    result = {}
    annotation_counter = 1  # Global counter for annotation IDs
    
    for pdf_name, pages in detections_by_pdf.items():
        result[pdf_name] = {}
        
        # Sort pages by page number
        sorted_pages = sorted(pages.items(), key=lambda x: int(x[0].split('_')[1]) if '_' in x[0] else 0)
        
        for page_key, annotations in sorted_pages:
            page_data = {
                "annotations": [],
                "page_size": {"width": 0, "height": 0}
            }
            
            # Get page size from first annotation's image path (or any annotation)
            image_path_for_size = None
            if annotations:
                # Find first annotation with image_path
                for ann in annotations:
                    if ann.get("image_path"):
                        image_path_for_size = ann["image_path"]
                        break
            
            if image_path_for_size:
                page_data["page_size"] = get_image_size(image_path_for_size)
            
            # Process each annotation (skip placeholders that only have image_path)
            valid_annotations = [ann for ann in annotations if ann.get("category") and ann.get("bbox")]
            
            # Only include pages with actual annotations
            if not valid_annotations:
                continue
            
            # Process each valid annotation
            for annotation in valid_annotations:
                category = normalize_category(annotation.get("category", "unknown"))
                bbox = annotation.get("bbox", {})
                
                # Calculate area
                area = calculate_area(bbox) if bbox else 0.0
                
                # Create annotation entry
                annotation_id = f"annotation_{annotation_counter}"
                annotation_entry = {
                    annotation_id: {
                        "category": category,
                        "bbox": bbox,
                        "area": round(area, 3)
                    }
                }
                
                page_data["annotations"].append(annotation_entry)
                annotation_counter += 1
            
            result[pdf_name][page_key] = page_data
    
    # Save to file if output path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ JSON annotations saved to: {output_path}")
    
    return result

