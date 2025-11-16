# Digital Inspector

An intelligent document analysis tool that automatically detects and annotates **stamps**, **signatures**, and **QR codes** in scanned PDF documents. Perfect for processing building/construction documentation and other structured documents.

## Features

- **Multi-Object Detection**: Detects stamps, signatures, and QR codes in PDF documents
- **PDF Processing**: Converts PDF pages to images and processes them automatically
- **YOLO-Based Detection**: Uses trained YOLO models for accurate stamp and signature detection
- **Robust QR Detection**: Multiple QR detection methods (OpenCV, pyzbar, qreader, qrdet) for maximum accuracy
- **JSON Output**: Generates structured JSON annotations matching hackathon requirements
- **Visual Annotations**: Automatically draws bounding boxes with color-coded labels on images
- **Parallel Processing**: Optimized for speed with configurable worker threads
- **Flexible Input**: Supports both single PDF files and directories of PDFs

## Quick Start

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd InnovateX_Hack
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install system dependencies**

   **macOS:**
   ```bash
   brew install poppler zbar
   ```

   **Ubuntu/Debian:**
   ```bash
   sudo apt-get install poppler-utils libzbar0
   ```

   **Windows:**
   - Download Poppler from [here](https://github.com/oschwartz10612/poppler-windows/releases)
   - Add to PATH or set `POPPLER_PATH` environment variable
   - ZBar is usually included in pyzbar wheel

### Basic Usage

**Process a directory of PDFs:**
```bash
python digital_inspector.py test_pdfs/
```

**Process a single PDF file:**
```bash
python digital_inspector.py test_pdfs/document.pdf
```

**With custom options:**
```bash
python digital_inspector.py test_pdfs/ \
  --workers 8 \
  --conf-threshold 0.1 \
  --json-output results.json \
  --no-fast
```

## Usage Examples

### Process PDFs with Default Settings
```bash
python digital_inspector.py test_pdfs/
```
- Converts PDFs to images (200 DPI)
- Detects all objects using default YOLO model
- Generates `annotations.json` in the output directory
- Draws bounding boxes on converted images

### Optimize for Speed
```bash
python digital_inspector.py test_pdfs/ --workers 8 --fast
```
- Uses 8 parallel workers (adjust based on your CPU)
- Fast QR detection mode (recommended for most cases)

### Optimize for Accuracy
```bash
python digital_inspector.py test_pdfs/ --no-fast --conf-threshold 0.1
```
- Exhaustive QR code search
- Lower confidence threshold for more detections

### Custom Output Location
```bash
python digital_inspector.py test_pdfs/ \
  --output my_results \
  --json-output custom_annotations.json
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `pdf_directory` | Path to PDF directory or single PDF file | Required |
| `--output` | Output directory name | `<input>_converted` |
| `--dpi` | Resolution for PDF conversion | 200 |
| `--workers` | Number of parallel workers | 4 |
| `--yolo-model` | Path to YOLO model file | `runs/detect/train8/weights/best.pt` |
| `--conf-threshold` | YOLO confidence threshold | 0.25 |
| `--json-output` | Path to save JSON file | `annotations.json` |
| `--fast` | Fast QR detection mode | Enabled |
| `--no-fast` | Exhaustive QR detection | Disabled |
| `--json` | Output results as JSON | False |

## Project Structure

```
InnovateX_Hack/
├── digital_inspector.py      # Main entry point
├── pdf_to_image_converter.py # PDF to image conversion
├── qr_detector.py            # QR code detection module
├── json_generator.py         # JSON output generation
├── draw_annotations.py       # Visual annotation drawing
├── yolo_pipeline.py         # YOLO detection pipeline
├── train_yolo.py            # YOLO model training
├── prepare_dataset.py       # Dataset preparation utilities
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Output Format

The tool generates JSON annotations in the following format:

```json
{
  "document.pdf": {
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

### Visual Annotations

The tool also draws bounding boxes on converted images:
- **Blue boxes** for signatures
- **Pink boxes** for stamps
- **Green boxes** for QR codes

Each box includes a label at the top edge.

## System Requirements

### Hardware
- **CPU**: Multi-core recommended (4+ cores for best performance)
- **RAM**: 8GB+ recommended
- **GPU**: Optional (speeds up YOLO detection, but not required)

### Software
- **Python**: 3.8 or higher
- **Operating System**: macOS, Linux, or Windows

### Optimal Worker Count
- **Apple M1**: 8-10 workers
- **AMD Ryzen 5 7535HS**: 12-16 workers
- **General**: Match your CPU thread count, add 20-30% for I/O overlap

See `OPTIMAL_WORKERS.md` for detailed recommendations.

## Advanced Usage

### Training Your Own YOLO Model

1. **Prepare dataset:**
   ```bash
   python prepare_dataset.py create
   python prepare_dataset.py split --source test_images
   ```

2. **Annotate images** using LabelImg (install: `pip install labelImg`)

3. **Train model:**
   ```bash
   python train_yolo.py --epochs 50 --model yolov8s.pt
   ```

4. **Use custom model:**
   ```bash
   python digital_inspector.py test_pdfs/ \
     --yolo-model runs/detect/train/weights/best.pt
   ```

See `TRAINING_GUIDE.md` for detailed instructions.

## Performance

- **Processing Speed**: ~3-8 seconds per page (CPU), ~1-3 seconds (GPU)
- **Parallelization**: Processes multiple pages simultaneously
- **Optimization**: Cached YOLO model loading, optimized image I/O

See `GPU_CPU_REQUIREMENTS.md` for performance details.

## Troubleshooting

### YOLO Model Not Found
```bash
# Use default model or specify custom path
python digital_inspector.py test_pdfs/ \
  --yolo-model yolov8s.pt
```

### No Detections Found
- Lower confidence threshold: `--conf-threshold 0.1`
- Try exhaustive search: `--no-fast`
- Check that images were converted successfully

### Poppler Not Found (PDF conversion fails)
- **macOS**: `brew install poppler`
- **Linux**: `sudo apt-get install poppler-utils`
- **Windows**: Download from [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases)

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

## Documentation

- `INTEGRATION_GUIDE.md` - Detailed integration guide
- `TRAINING_GUIDE.md` - YOLO model training instructions
- `QUICK_START.md` - Quick start guide
- `GPU_CPU_REQUIREMENTS.md` - Hardware requirements
- `OPTIMAL_WORKERS.md` - Worker count optimization
- `WINDOWS_COMPATIBILITY.md` - Windows setup guide

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Add your license here]

## Acknowledgments

- **YOLO**: Ultralytics YOLO for object detection
- **OpenCV**: Computer vision operations
- **Poppler**: PDF rendering library

---

**Made for InnovateX Hackathon**

