#!/usr/bin/env python3
"""
Digital Inspector
Combines PDF to image conversion and QR code detection.
Takes a directory of PDFs, converts them to images, and detects QR codes.
"""

import argparse
import os
import sys
from pathlib import Path

# Import converter and detector functions
from pdf_to_image_converter import convert_pdf_to_images, process_directory
from qr_detector import process_image_directory, RobustQRDetector


def inspect_pdfs(pdf_directory: str, output_dir_name: str = None, fast_mode: bool = True, dpi: int = 200) -> dict:
    """
    Main inspection function: converts PDFs to images and detects QR codes.
    
    Args:
        pdf_directory: Path to directory containing PDF files
        output_dir_name: Name for the output directory (default: pdf_directory + '_converted')
        fast_mode: Use fast QR detection mode
        dpi: Resolution for image conversion
        
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
    
    # STEP 2: Detect QR codes in converted images
    print(f"\n{'='*60}")
    print("STEP 2: Detecting QR codes in converted images...")
    print("-" * 60)
    
    try:
        # Process all image folders in the output directory
        detection_result = process_image_directory(
            str(output_dir),
            fast_mode=fast_mode
        )
        
        if detection_result["status"] != "success":
            return {
                "status": "error",
                "message": f"Error during QR detection: {detection_result.get('message', 'Unknown error')}"
            }
        
        print(f"\n✓ QR Detection complete!")
        
        # Combine results
        return {
            "status": "success",
            "input_directory": str(pdf_dir),
            "output_directory": str(output_dir),
            "conversion": conversion_summary,
            "detection": {
                "folders_processed": detection_result["folders_processed"],
                "qr_codes_found": detection_result["count"],
                "data": detection_result["data"]
            }
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error during QR detection: {str(e)}"
        }


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Digital Inspector: Convert PDFs to images and detect QR codes",
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
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    
    args = parser.parse_args()
    
    # Run inspection
    result = inspect_pdfs(
        args.pdf_directory,
        output_dir_name=args.output,
        fast_mode=args.fast,
        dpi=args.dpi
    )
    
    # Output results
    if args.json:
        import json
        print(json.dumps(result, indent=2))
    else:
        if result["status"] == "success":
            print(f"\n{'='*60}")
            print("FINAL SUMMARY")
            print(f"{'='*60}")
            print(f"Input: {result['input_directory']}")
            print(f"Output: {result['output_directory']}")
            print(f"\nConversion:")
            print(f"  PDFs: {result['conversion']['total_pdfs']}")
            print(f"  Pages: {result['conversion']['total_pages']}")
            print(f"\nQR Detection:")
            print(f"  Folders: {result['detection']['folders_processed']}")
            print(f"  QR Codes found: {result['detection']['qr_codes_found']}")
            print(f"{'='*60}")
            
            # Show QR codes by document and page
            if result['detection']['data']:
                print(f"\nQR Codes by Document and Page:")
                current_doc = None
                current_page = None
                
                for qr in result['detection']['data']:
                    doc_name = qr.get('pdf_file', 'Unknown')
                    page_num = qr.get('page', 0)
                    
                    if doc_name != current_doc or page_num != current_page:
                        if current_doc is not None:
                            print()
                        print(f"\n  {doc_name} - Page {page_num}:")
                        current_doc = doc_name
                        current_page = page_num
                    
                    print(f"    • {qr['text']}")
                    print(f"      Method: {qr['method']}, Preprocessing: {qr.get('preprocessing', 'N/A')}")
        else:
            print(f"Error: {result.get('message', 'Unknown error')}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()

