import os
from pathlib import Path
import pdf2image
import pytesseract
import platform
import subprocess
import sys
import re

class ResumeProcessor:
    def __init__(self, input_dir: str = "resumes", output_dir: str = "tobeprocessed"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # Create directories if they don't exist
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        # Check and set up dependencies
        self._check_dependencies()
        
        # Configure paths based on environment
        self.poppler_path = self._configure_poppler_path()
    
    def _check_dependencies(self):
        """Check if required system dependencies are installed"""
        system = platform.system().lower()
        
        if system == "linux":
            # Check for poppler-utils and tesseract on Linux
            try:
                subprocess.run(['pdfinfo', '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except FileNotFoundError:
                print("Error: poppler-utils not found. Install using:")
                print("sudo apt-get update && sudo apt-get install -y poppler-utils")
                sys.exit(1)
                
            try:
                subprocess.run(['tesseract', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except FileNotFoundError:
                print("Error: tesseract not found. Install using:")
                print("sudo apt-get update && sudo apt-get install -y tesseract-ocr")
                sys.exit(1)
                
        elif system == "darwin":  # macOS
            # Check for Homebrew installations
            if not os.path.exists("/opt/homebrew/bin/pdfinfo"):
                print("Error: poppler not found. Install using:")
                print("brew install poppler")
                sys.exit(1)
            
            if not os.path.exists("/opt/homebrew/bin/tesseract"):
                print("Error: tesseract not found. Install using:")
                print("brew install tesseract")
                sys.exit(1)
    
    def _configure_poppler_path(self):
        """Configure poppler path based on the operating system"""
        system = platform.system().lower()
        
        if system == "darwin":  # macOS
            return "/opt/homebrew/bin"
        elif system == "linux":  # Linux (including EC2)
            return None  # Linux typically has poppler in PATH
        else:
            print(f"Warning: Unsupported operating system: {system}")
            return None
    
    def process_all_resumes(self):
        """Process all PDF files in the input directory"""
        pdf_files = list(self.input_dir.glob("*.pdf"))
        if not pdf_files:
            print("No PDF files found in the resumes directory.")
            return
            
        print(f"Found {len(pdf_files)} PDF files to process...")
        for pdf_file in pdf_files:
            self.process_single_resume(pdf_file)
    
    def _clean_text(self, text: str) -> str:
        """Clean the OCR output text"""
        # Replace common bullet point OCR errors
        text = re.sub(r'(?m)^[e]\s+', '• ', text)  # Replace 'e ' at start of lines with bullet
        text = re.sub(r'(?m)^[o]\s+', '• ', text)  # Replace 'o ' at start of lines with bullet
        text = re.sub(r'(?m)^[-]\s+', '• ', text)  # Replace '- ' at start of lines with bullet
        
        # Remove multiple consecutive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def process_single_resume(self, pdf_path: Path):
        """
        Convert a single PDF resume to text and save it
        """
        try:
            print(f"Processing {pdf_path.name}...")
            
            # Convert PDF to images
            images = pdf2image.convert_from_path(
                str(pdf_path),
                poppler_path=self.poppler_path if hasattr(self, 'poppler_path') else None
            )
            
            # Extract text using OCR
            extracted_text = ""
            for i, image in enumerate(images, 1):
                print(f"  OCR processing page {i}/{len(images)}...")
                text = pytesseract.image_to_string(image)
                extracted_text += text + "\n"
            
            # Clean the extracted text
            cleaned_text = self._clean_text(extracted_text)
            
            # Save the extracted text
            output_file = self.output_dir / f"{pdf_path.stem}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)
                
            print(f"✓ Successfully processed: {pdf_path.name}")
            print(f"  Saved to: {output_file}")
            
        except Exception as e:
            print(f"✗ Error processing {pdf_path.name}: {str(e)}")

if __name__ == "__main__":
    processor = ResumeProcessor()
    processor.process_all_resumes() 