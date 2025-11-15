#!/usr/bin/env python3
"""
Annotation Drawing Module
Draws bounding boxes around detected objects on images with specified colors and styles.
"""

import cv2
from pathlib import Path
from typing import List, Dict


# Color definitions (BGR format for OpenCV)
# Pink: RGB(255, 192, 203) = BGR(203, 192, 255)
# Blue: RGB(0, 0, 255) = BGR(255, 0, 0)
# Green: RGB(0, 255, 0) = BGR(0, 255, 0)
COLORS = {
    "stamp": (203, 192, 255),      # Pink (BGR)
    "signature": (255, 0, 0),      # Blue (BGR)
    "qr": (0, 255, 0)              # Green (BGR)
}


def calculate_font_scale(text: str, box_width: int, font: int = cv2.FONT_HERSHEY_SIMPLEX) -> float:
    """
    Calculate appropriate font scale to fit text within box width.
    Uses larger base scale for better visibility.
    
    Args:
        text: Text to display
        box_width: Width of the bounding box
        font: OpenCV font type
    
    Returns:
        Font scale value
    """
    # Start with a larger base scale for better visibility
    base_scale = 1.5
    min_scale = 0.6
    max_scale = 3.0  # Increased max scale to allow larger text
    
    # Get text size (using thicker font for calculations)
    (text_width, text_height), baseline = cv2.getTextSize(text, font, base_scale, 8)
    
    # Adjust scale to fit within 85% of box width (leave some margin)
    target_width = box_width * 0.85
    
    if text_width > 0:
        scale = base_scale * (target_width / text_width)
        # Clamp scale to reasonable bounds
        scale = max(min_scale, min(max_scale, scale))
    else:
        scale = base_scale
    
    return scale


def draw_bbox_on_image(
    image_path: str,
    detections: List[Dict],
    padding: int = 20,
    thickness: int = 12,
    save_path: str = None
) -> bool:
    """
    Draw bounding boxes around detected objects on an image with labels.
    
    Args:
        image_path: Path to the input image file
        detections: List of detection dictionaries, each with:
            - category: "signature", "stamp", or "qr"
            - bbox: {"x": float, "y": float, "width": float, "height": float}
        padding: Pixels to expand the box outward (default: 20)
        thickness: Thickness of the border line (default: 12)
        save_path: Optional path to save the annotated image (default: overwrite original)
    
    Returns:
        True if image was modified and saved, False otherwise
    """
    if not detections:
        return False
    
    try:
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"  Warning: Could not load image: {image_path}")
            return False
        
        height, width = image.shape[:2]
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Draw rectangles and labels for each detection
        for detection in detections:
            category = detection.get("category", "").lower()
            bbox = detection.get("bbox", {})
            
            if not bbox or not category:
                continue
            
            # Get color for this category
            color = COLORS.get(category, (255, 255, 255))  # Default to white if unknown
            
            # Extract bounding box coordinates
            x = int(bbox.get("x", 0))
            y = int(bbox.get("y", 0))
            w = int(bbox.get("width", 0))
            h = int(bbox.get("height", 0))
            
            if w <= 0 or h <= 0:
                continue
            
            # Apply padding (expand outward)
            x_padded = max(0, x - padding)
            y_padded = max(0, y - padding)
            w_padded = min(width - x_padded, w + 2 * padding)
            h_padded = min(height - y_padded, h + 2 * padding)
            
            # Ensure coordinates are within image bounds
            x_padded = max(0, min(x_padded, width - 1))
            y_padded = max(0, min(y_padded, height - 1))
            w_padded = max(1, min(w_padded, width - x_padded))
            h_padded = max(1, min(h_padded, height - y_padded))
            
            # Prepare label text
            label_text = category
            if category == "qr":
                label_text = "qr code"
            elif category == "signature":
                label_text = "signature"
            elif category == "stamp":
                label_text = "stamp"
            
            # Calculate font scale to fit within box width (with margin)
            # Use larger scale for better visibility
            font_scale = calculate_font_scale(label_text, w_padded)
            
            # Get text size for positioning (using thicker font)
            (text_width, text_height), baseline = cv2.getTextSize(
                label_text, font, font_scale, 8  # Even thicker font
            )
            
            # Ensure text width doesn't exceed box width (with small margin)
            max_text_width = int(w_padded * 0.85)
            if text_width > max_text_width:
                # Recalculate with smaller scale
                font_scale = font_scale * (max_text_width / text_width)
                (text_width, text_height), baseline = cv2.getTextSize(
                    label_text, font, font_scale, 8  # Even thicker font
                )
            
            # Position text block ABOVE the box (outward, not inward)
            # Center horizontally within the box
            text_x = x_padded + (w_padded - text_width) // 2
            
            # Calculate text block dimensions (extending outward above the box)
            text_block_padding = 8  # Padding around text
            text_block_height = text_height + baseline + (text_block_padding * 2)
            text_block_y1 = y_padded - text_block_height  # Start above the box
            text_block_y2 = y_padded  # End at the top edge of the box
            text_block_x1 = text_x - text_block_padding
            text_block_x2 = text_x + text_width + text_block_padding
            
            # Ensure text block doesn't go outside image bounds
            text_block_x1 = max(0, min(text_block_x1, width - 1))
            text_block_x2 = max(text_block_x1 + 1, min(text_block_x2, width))
            text_block_y1 = max(0, min(text_block_y1, height - 1))
            
            # Adjust text position if block was clipped
            if text_block_y1 < 0:
                text_block_y1 = 0
                text_block_y2 = text_block_height
            
            # Position text vertically within the block (centered)
            text_y = text_block_y1 + text_block_padding + text_height
            
            # Draw rectangle (outline only, no fill) for the main box
            # Make lines 1.5x thicker (12 -> 18)
            box_thickness = int(thickness * 1.5)
            cv2.rectangle(
                image,
                (x_padded, y_padded),
                (x_padded + w_padded, y_padded + h_padded),
                color,
                box_thickness
            )
            
            # Draw text block ABOVE the box (filled rectangle extending outward)
            cv2.rectangle(
                image,
                (text_block_x1, text_block_y1),
                (text_block_x2, text_block_y2),
                color,
                -1  # Filled rectangle
            )
            
            # Draw text in white for contrast (even thicker)
            cv2.putText(
                image,
                label_text,
                (text_x, text_y),
                font,
                font_scale,
                (255, 255, 255),  # White text
                8  # Text thickness (even thicker)
            )
        
        # Save the modified image
        output_path = save_path if save_path else image_path
        success = cv2.imwrite(output_path, image)
        
        return success
        
    except Exception as e:
        print(f"  Warning: Could not draw annotations on {image_path}: {e}")
        return False


def draw_annotations_for_page(
    image_path: str,
    yolo_detections: List[Dict],
    qr_detections: List[Dict],
    padding: int = 20,
    thickness: int = 12
) -> bool:
    """
    Draw all annotations (YOLO + QR) on a single page image.
    
    Args:
        image_path: Path to the image file
        yolo_detections: List of YOLO detections (signatures, stamps)
        qr_detections: List of QR code detections
        padding: Pixels to expand boxes outward
        thickness: Line thickness
    
    Returns:
        True if annotations were drawn, False otherwise
    """
    # Combine all detections
    all_detections = []
    
    # Add YOLO detections
    for det in yolo_detections:
        # Ensure category is normalized
        category = det.get("category", "").lower()
        if category in ["signature", "stamp"]:
            all_detections.append({
                "category": category,
                "bbox": det.get("bbox", {})
            })
    
    # Add QR detections
    for det in qr_detections:
        all_detections.append({
            "category": "qr",
            "bbox": det.get("bbox", {})
        })
    
    # Draw if there are any detections
    if all_detections:
        return draw_bbox_on_image(
            image_path,
            all_detections,
            padding=padding,
            thickness=thickness
        )
    
    return False

