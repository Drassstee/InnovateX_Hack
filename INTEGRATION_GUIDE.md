# Digital Inspector - JSON Integration Guide

## Overview

The Digital Inspector now fully integrates detection of **signatures**, **stamps**, and **QR codes** with JSON output generation matching the hackathon requirements.

## How It Works

### 1. Main Entry Point
Run `digital_inspector.py` - this is the main script that orchestrates everything:

```bash
python digital_inspector.py test_pdfs/
```

### 2. Processing Pipeline

The system follows these steps:

1. **PDF to Image Conversion**
   - Converts all PDFs in the input directory to PNG images
   - Each PDF gets its own folder with page images
   - Uses `pdf_to_image_converter.py`

2. **Detection Phase**
   For each page image:
   - **YOLO Detection**: Detects signatures and stamps using trained YOLO model
   - **QR Detection**: Detects QR codes using multiple detection methods (pyzbar, qreader, qrdet, opencv)
   - Collects all detections with bounding boxes

3. **JSON Generation**
   - Converts all detections to the required JSON format
   - Matches the structure of `selected_annotations.json`
   - Saves to `annotations.json` (or custom path)

### 3. JSON Output Format

The generated JSON matches this structure:

```json
{
  "pdf_filename.pdf": {
    "page_1": {
      "annotations": [
        {
          "annotation_1": {
            "category": "signature",
            "bbox": {
              "x": 510,
              "y": 146,
              "width": 250,
              "height": 98.89
            },
            "area": 24722.5
          }
        },
        {
          "annotation_2": {
            "category": "stamp",
            "bbox": {
              "x": 709,
              "y": 1184,
              "width": 208.76,
              "height": 218.11
            },
            "area": 45532.644
          }
        }
      ],
      "page_size": {
        "width": 1684,
        "height": 1190
      }
    }
  }
}
```

## Usage Examples

### Basic Usage
```bash
python digital_inspector.py test_pdfs/
```

### Custom Output Directory
```bash
python digital_inspector.py test_pdfs/ --output my_results
```

### Custom JSON Output Path
```bash
python digital_inspector.py test_pdfs/ --json-output results/annotations.json
```

### Custom YOLO Model
```bash
python digital_inspector.py test_pdfs/ --yolo-model models/custom.pt
```

### Adjust Confidence Threshold
```bash
python digital_inspector.py test_pdfs/ --conf-threshold 0.5
```

### Exhaustive QR Search (slower but more thorough)
```bash
python digital_inspector.py test_pdfs/ --no-fast
```

### High Resolution Conversion
```bash
python digital_inspector.py test_pdfs/ --dpi 300
```

## File Structure

```
InnovateX_Hack/
├── digital_inspector.py      # Main entry point
├── json_generator.py          # JSON format conversion
├── pdf_to_image_converter.py # PDF to image conversion
├── qr_detector.py            # QR code detection
├── yolo_pipeline.py          # YOLO detection utilities
└── detect_images.py          # Legacy YOLO detection script
```

## Output Structure

After running, you'll get:

```
test_pdfs_converted/
├── PDF1/
│   ├── PDF1_page1.png
│   ├── PDF1_page2.png
│   └── ...
├── PDF2/
│   └── ...
└── ...

annotations.json  # Generated JSON file
```

## Detection Methods

### Signatures & Stamps
- **Method**: YOLO object detection
- **Model**: `runs/detect/train8/weights/best.pt` (default)
- **Format**: Bounding boxes in (x, y, width, height) format
- **Categories**: "signature", "stamp"

### QR Codes
- **Methods**: Multiple detection libraries for robustness
  - pyzbar (very robust for damaged codes)
  - qreader (handles challenging scenarios)
  - qrdet (excellent for multiple QR codes)
  - OpenCV QRCodeDetector (fast baseline)
- **Format**: Quadrilateral converted to (x, y, width, height)
- **Category**: "qr"

## Coordinate System

All bounding boxes use the format:
- **x, y**: Top-left corner coordinates
- **width, height**: Box dimensions
- **area**: Calculated as width × height

This matches the format in `selected_annotations.json`.

## Notes

- Pages without any detections are **not included** in the JSON output (matching the reference format)
- Page sizes are automatically extracted from image dimensions
- Annotation IDs are sequential across all PDFs and pages
- The system handles missing YOLO models gracefully (skips YOLO detection if model not found)

## Troubleshooting

### YOLO Model Not Found
If you see warnings about YOLO model, ensure:
- Model exists at `runs/detect/train8/weights/best.pt`, or
- Specify custom path with `--yolo-model`

### No Detections Found
- Check that images were converted successfully
- Try lowering confidence threshold: `--conf-threshold 0.1`
- Try exhaustive QR search: `--no-fast`

### JSON Format Issues
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that image paths are accessible
- Verify page numbers are extracted correctly from filenames

