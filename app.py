"""
Flask Web Application for Digital Inspector
Handles PDF uploads, processing, and serving detected images.
"""

import os
import json
import shutil
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import tempfile
import traceback

# Import the main inspection function
from digital_inspector import inspect_pdfs

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['RESULTS_FOLDER'] = 'static/results'

# Create necessary directories
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
Path(app.config['RESULTS_FOLDER']).mkdir(parents=True, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}


def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_annotated_images(output_dir):
    """
    Find all annotated images in the output directory.
    Returns list of image paths relative to output_dir.
    """
    images = []
    output_path = Path(output_dir)
    
    if not output_path.exists():
        return images
    
    # Look for image files in subdirectories (each PDF gets its own folder)
    for folder in output_path.iterdir():
        if folder.is_dir():
            for img_file in folder.iterdir():
                if img_file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                    # Return relative path from output_dir
                    rel_path = img_file.relative_to(output_path)
                    images.append({
                        'path': str(rel_path).replace('\\', '/'),
                        'name': img_file.name,
                        'page': folder.name
                    })
    
    return sorted(images, key=lambda x: x['name'])


@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Handle PDF file upload and processing.
    Returns JSON with status and image URLs.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only PDF files are allowed.'}), 400
    
    # Create temporary directory for this upload
    temp_dir = tempfile.mkdtemp(prefix='pdf_inspect_')
    temp_pdf_path = None
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        temp_pdf_path = os.path.join(temp_dir, filename)
        file.save(temp_pdf_path)
        
        # Process the PDF using digital_inspector
        # digital_inspector will create output in parent directory of PDF
        # We'll move it to results folder afterwards
        print(f"Processing PDF: {temp_pdf_path}")
        print(f"File size: {os.path.getsize(temp_pdf_path) / (1024*1024):.2f} MB")
        
        try:
            result = inspect_pdfs(
                pdf_directory=str(temp_pdf_path),
                output_dir_name=None,  # Let it use default naming
                fast_mode=True,
                dpi=200,
                yolo_model_path=None,  # Use default
                conf_threshold=0.25,
                json_output_path=None,  # Don't save JSON for web
                max_workers=4
            )
        except Exception as e:
            print(f"Error in inspect_pdfs: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'error': f'Processing error: {str(e)}',
                'status': 'error'
            }), 500
        
        if result.get('status') == 'error':
            return jsonify({
                'error': result.get('message', 'Unknown error occurred'),
                'status': 'error'
            }), 500
        
        # Get the output directory from result
        output_dir = Path(result['output_directory'])
        
        # Move to results folder for serving
        pdf_name = Path(filename).stem
        output_dir_name = f"{pdf_name}_converted"
        final_output_dir = Path(app.config['RESULTS_FOLDER']) / output_dir_name
        
        # Move output directory to results folder
        if output_dir != final_output_dir:
            if output_dir.exists():
                if final_output_dir.exists():
                    shutil.rmtree(final_output_dir)
                shutil.move(str(output_dir), str(final_output_dir))
            output_dir = final_output_dir
        
        # Find annotated images
        annotated_images = get_annotated_images(str(output_dir))
        
        # Convert image paths to URLs
        image_urls = []
        for img in annotated_images:
            # Serve images from results folder
            image_urls.append({
                'url': f"/api/image/{output_dir_name}/{img['path']}",
                'name': img['name'],
                'page': img['page']
            })
        
        return jsonify({
            'status': 'success',
            'message': f'Processed {len(annotated_images)} page(s)',
            'images': image_urls,
            'summary': {
                'total_pages': result.get('conversion', {}).get('total_pages', 0),
                'total_annotations': result.get('detection', {}).get('total_annotations', 0),
                'pdfs_processed': result.get('detection', {}).get('pdfs_processed', 0)
            }
        })
    
    except RequestEntityTooLarge:
        return jsonify({'error': 'File too large. Maximum size is 50MB.'}), 413
    
    except Exception as e:
        error_msg = str(e)
        print(f"Error processing PDF: {error_msg}")
        print(traceback.format_exc())
        return jsonify({
            'error': f'Error processing PDF: {error_msg}',
            'status': 'error'
        }), 500
    
    finally:
        # Clean up temporary files
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            try:
                os.remove(temp_pdf_path)
            except:
                pass
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except:
                pass


@app.route('/api/image/<path:image_path>')
def serve_image(image_path):
    """
    Serve annotated images from results folder.
    """
    try:
        # Security: ensure path is within results folder
        # Handle Windows paths by normalizing separators
        image_path = image_path.replace('\\', '/')
        full_path = Path(app.config['RESULTS_FOLDER']) / image_path
        full_path = full_path.resolve()
        results_path = Path(app.config['RESULTS_FOLDER']).resolve()
        
        # Check path is within results folder (security)
        try:
            full_path.relative_to(results_path)
        except ValueError:
            return jsonify({'error': 'Invalid path'}), 403
        
        if not full_path.exists():
            return jsonify({'error': 'Image not found'}), 404
        
        if not full_path.is_file():
            return jsonify({'error': 'Not a file'}), 404
        
        return send_from_directory(
            str(full_path.parent),
            full_path.name
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'message': 'Digital Inspector API is running'})


if __name__ == '__main__':
    print("=" * 60)
    print("Digital Inspector Web Application")
    print("=" * 60)
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"Results folder: {app.config['RESULTS_FOLDER']}")
    print(f"Max file size: {app.config['MAX_CONTENT_LENGTH'] / (1024*1024)}MB")
    print("=" * 60)
    print("\nStarting server...")
    print("Open http://localhost:5000 in your browser")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)

