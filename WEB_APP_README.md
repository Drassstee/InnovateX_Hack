# 🌐 Digital Inspector Web Application

A simple web interface for uploading PDFs and viewing detected signatures, stamps, and QR codes.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Server

```bash
python app.py
```

### 3. Open Your Browser

Navigate to: **http://localhost:5000**

## 📋 Features

- **PDF Upload**: Drag & drop or click to upload PDF files
- **Automatic Processing**: Converts PDF to images and detects:
  - Signatures
  - Stamps
  - QR Codes
- **Image Gallery**: View all detected images with bounding boxes
- **Responsive Design**: Works on desktop and mobile devices

## 🎯 How It Works

1. **Upload PDF**: Select or drag a PDF file
2. **Processing**: The server:
   - Converts PDF pages to images
   - Runs YOLO detection for signatures/stamps
   - Runs QR code detection
   - Draws bounding boxes on detected items
3. **View Results**: See all annotated images in a gallery

## 📁 Project Structure

```
.
├── app.py                 # Flask backend server
├── templates/
│   └── index.html        # Web interface
├── static/
│   ├── uploads/         # Temporary upload storage
│   └── results/         # Processed images
└── digital_inspector.py  # Main detection logic
```

## ⚙️ Configuration

### File Size Limit

Default: 50MB. To change, edit `app.py`:

```python
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
```

### Port

Default: 5000. To change:

```python
app.run(debug=True, host='0.0.0.0', port=8080)
```

### YOLO Model

The app uses the default YOLO model path. To specify a custom model, modify `app.py`:

```python
result = inspect_pdfs(
    ...
    yolo_model_path="path/to/your/model.pt",
    ...
)
```

## 🔧 API Endpoints

### `GET /`
Main web page

### `POST /api/upload`
Upload and process PDF file

**Request:**
- `file`: PDF file (multipart/form-data)

**Response:**
```json
{
  "status": "success",
  "message": "Processed 3 page(s)",
  "images": [
    {
      "url": "/api/image/document_converted/document/page_1.png",
      "name": "document_page_1.png",
      "page": "document"
    }
  ],
  "summary": {
    "total_pages": 3,
    "total_annotations": 5,
    "pdfs_processed": 1
  }
}
```

### `GET /api/image/<path>`
Serve processed images

### `GET /api/health`
Health check endpoint

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'flask'"
```bash
pip install Flask Werkzeug
```

### "Poppler not found" error
- **Windows**: Download from https://github.com/oschwartz10612/poppler-windows/releases
- Set path in `pdf_to_image_converter.py` (POPPLER_PATH)

### Images not displaying
- Check that `static/results/` directory exists
- Check browser console for errors
- Verify image URLs in network tab

### Processing takes too long
- Large PDFs take time to process
- Check server console for progress
- Consider reducing DPI in `app.py` (default: 200)

## 📝 Notes

- Processed images are stored in `static/results/`
- Temporary uploads are automatically cleaned up
- The app processes one PDF at a time
- Results persist until server restart (images in `static/results/`)

## 🔒 Security Notes

- File uploads are limited to PDF files only
- File size is limited (default 50MB)
- Path traversal protection for image serving
- Temporary files are cleaned up after processing

## 🚀 Production Deployment

For production use:

1. **Disable debug mode:**
```python
app.run(debug=False, host='0.0.0.0', port=5000)
```

2. **Use a production WSGI server:**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

3. **Set up reverse proxy** (nginx/Apache) for better performance

4. **Add authentication** if needed

5. **Configure proper file cleanup** for production

## 📞 Support

For issues or questions, check:
- `digital_inspector.py` - Main detection logic
- Server console output for error messages
- Browser developer console for frontend errors

