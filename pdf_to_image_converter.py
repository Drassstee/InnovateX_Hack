#!/usr/bin/env python3
"""
PDF to Image Converter
Converts a PDF file to image(s) and saves them in a new directory named after the PDF file.
"""

import argparse
import os
import sys
from pathlib import Path
from pdf2image import convert_from_path

# ============================================================================
# POPPLER PATH CONFIGURATION FOR WINDOWS
# ============================================================================
# If poppler cannot be installed system-wide, you can hardcode the path here.
# 
# For Windows users:
# 1. Download poppler from: https://github.com/oschwartz10612/poppler-windows/releases
# 2. Extract to a folder (e.g., C:\poppler)
# 3. Set the path below to point to the 'bin' folder inside poppler
#
# Example Windows paths:
# POPPLER_PATH = r"C:\poppler\Library\bin"
# POPPLER_PATH = r"D:\tools\poppler\bin"
# POPPLER_PATH = r"C:\Users\YourName\poppler\bin"
#
# Leave as None to use system PATH or POPPLER_PATH environment variable
POPPLER_PATH = None  # Set to your poppler bin path if needed (e.g., r"C:\poppler\Library\bin")
# ============================================================================


def get_poppler_path():
    """
    Get poppler path from hardcoded value, environment variable, or None.
    Priority: hardcoded POPPLER_PATH > POPPLER_PATH env var > None (use system PATH)
    """
    # First check hardcoded path
    if POPPLER_PATH and os.path.exists(POPPLER_PATH):
        return POPPLER_PATH
    
    # Check environment variable
    env_path = os.environ.get('POPPLER_PATH')
    if env_path and os.path.exists(env_path):
        return env_path
    
    # Return None to use system PATH
    return None


def convert_pdf_to_images_in_memory(pdf_path, dpi=200):
    """
    Convert a PDF file to PIL Images in memory (without saving to disk).
    
    Args:
        pdf_path (str): Path to the PDF file
        dpi (int): Resolution for the output images (default: 200)
    
    Returns:
        list: List of PIL.Image objects
    """
    # Validate PDF file exists
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if not pdf_path.lower().endswith('.pdf'):
        raise ValueError(f"File is not a PDF: {pdf_path}")
    
    try:
        # Get poppler path (hardcoded, env var, or None)
        poppler_path = get_poppler_path()
        
        # Convert PDF to images (returns PIL Images)
        # poppler_path parameter allows hardcoding the path for Windows users
        if poppler_path:
            images = convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path)
        else:
            images = convert_from_path(pdf_path, dpi=dpi)
        
        if not images:
            raise ValueError("No pages found in PDF")
        
        return images
        
    except Exception as e:
        raise RuntimeError(f"Error converting PDF to images: {str(e)}")


def convert_pdf_to_images(pdf_path, output_format='PNG', dpi=200, output_base_dir=None):
    """
    Convert a PDF file to images and save them to disk.
    
    Args:
        pdf_path (str): Path to the PDF file
        output_format (str): Output image format (PNG, JPEG, etc.)
        dpi (int): Resolution for the output images (default: 200)
        output_base_dir (str, optional): Base directory for output. If None, uses PDF's directory.
    
    Returns:
        list: List of paths to saved image files
    """
    # Get the directory and base name of the PDF
    pdf_dir = os.path.dirname(os.path.abspath(pdf_path))
    pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # Create output directory named after the PDF file
    if output_base_dir:
        output_dir = os.path.join(output_base_dir, pdf_basename)
    else:
        output_dir = os.path.join(pdf_dir, pdf_basename)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Converting PDF: {pdf_path}")
    print(f"Output directory: {output_dir}")
    
    try:
        # Convert PDF to images using the in-memory function
        images = convert_pdf_to_images_in_memory(pdf_path, dpi=dpi)
        
        saved_files = []
        
        # Save each page as a separate image
        for i, image in enumerate(images, start=1):
            # Generate output filename
            if len(images) == 1:
                # Single page: use base name without page number
                output_filename = f"{pdf_basename}.{output_format.lower()}"
            else:
                # Multiple pages: add page number
                output_filename = f"{pdf_basename}_page{i}.{output_format.lower()}"
            
            output_path = os.path.join(output_dir, output_filename)
            
            # Save the image
            image.save(output_path, output_format)
            saved_files.append(output_path)
            print(f"Saved: {output_path}")
        
        print(f"\nSuccessfully converted {len(images)} page(s) to {len(saved_files)} image(s)")
        return saved_files
        
    except Exception as e:
        raise RuntimeError(f"Error converting PDF to images: {str(e)}")


def process_directory(directory_path, output_format='PNG', dpi=200, output_base_dir=None):
    """
    Process all PDF files in a directory.
    
    Args:
        directory_path (str): Path to directory containing PDF files
        output_format (str): Output image format (PNG, JPEG, etc.)
        dpi (int): Resolution for the output images (default: 200)
        output_base_dir (str, optional): Base directory for output folders. If None, uses PDF's directory.
    
    Returns:
        dict: Summary of processed files
    """
    directory = Path(directory_path)
    if not directory.exists() or not directory.is_dir():
        raise ValueError(f"Directory not found: {directory_path}")
    
    # Find all PDF files
    pdf_files = sorted([f for f in directory.iterdir() 
                       if f.is_file() and f.suffix.lower() == '.pdf'])
    
    if not pdf_files:
        raise ValueError(f"No PDF files found in directory: {directory_path}")
    
    print(f"Found {len(pdf_files)} PDF file(s) in {directory_path}\n")
    
    total_pages = 0
    successful = 0
    failed = 0
    
    for pdf_file in pdf_files:
        try:
            saved_files = convert_pdf_to_images(
                str(pdf_file),
                output_format=output_format,
                dpi=dpi,
                output_base_dir=output_base_dir
            )
            total_pages += len(saved_files)
            successful += 1
            print()  # Empty line between PDFs
        except Exception as e:
            print(f"Error processing {pdf_file.name}: {e}", file=sys.stderr)
            failed += 1
            continue
    
    return {
        "total_pdfs": len(pdf_files),
        "successful": successful,
        "failed": failed,
        "total_pages": total_pages
    }


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Convert PDF file(s) to image(s) and save in directories named after each PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a single PDF file
  python pdf_to_image_converter.py document.pdf
  
  # Convert all PDFs in a directory
  python pdf_to_image_converter.py test_pdfs/
  
  # Convert with custom format and DPI
  python pdf_to_image_converter.py document.pdf --format JPEG --dpi 300
        """
    )
    
    parser.add_argument(
        'input_path',
        type=str,
        help='Path to a PDF file or directory containing PDF files'
    )
    
    parser.add_argument(
        '--format',
        type=str,
        default='PNG',
        choices=['PNG', 'JPEG', 'JPG'],
        help='Output image format (default: PNG)'
    )
    
    parser.add_argument(
        '--dpi',
        type=int,
        default=200,
        help='Resolution (DPI) for the output images (default: 200)'
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input_path)
    
    try:
        # Check if input is a directory or a file
        if input_path.is_dir():
            # Process all PDFs in directory
            summary = process_directory(
                str(input_path),
                output_format=args.format,
                dpi=args.dpi
            )
            print(f"\n{'='*60}")
            print(f"Summary:")
            print(f"  PDFs processed: {summary['total_pdfs']}")
            print(f"  Successful: {summary['successful']}")
            print(f"  Failed: {summary['failed']}")
            print(f"  Total pages converted: {summary['total_pages']}")
            print(f"{'='*60}")
            sys.exit(0)
        
        elif input_path.is_file():
            # Process single PDF file
            if not str(input_path).lower().endswith('.pdf'):
                print(f"Error: File is not a PDF: {args.input_path}", file=sys.stderr)
                sys.exit(1)
            
            saved_files = convert_pdf_to_images(
                str(input_path),
                output_format=args.format,
                dpi=args.dpi
            )
            sys.exit(0)
        
        else:
            print(f"Error: Path not found: {args.input_path}", file=sys.stderr)
            sys.exit(1)
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
        
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nNote: Make sure 'poppler' is installed on your system.", file=sys.stderr)
        print("  macOS: brew install poppler", file=sys.stderr)
        print("  Ubuntu/Debian: sudo apt-get install poppler-utils", file=sys.stderr)
        print("  Windows: Download from https://github.com/oschwartz10612/poppler-windows/releases", file=sys.stderr)
        print("\n  Windows users can also hardcode the path in pdf_to_image_converter.py:", file=sys.stderr)
        print("    1. Download and extract poppler to a folder (e.g., C:\\poppler)", file=sys.stderr)
        print("    2. Edit pdf_to_image_converter.py and set:", file=sys.stderr)
        print("       POPPLER_PATH = r\"C:\\poppler\\Library\\bin\"", file=sys.stderr)
        print("    3. Make sure the path points to the 'bin' folder containing pdftoppm.exe", file=sys.stderr)
        sys.exit(1)
        
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

