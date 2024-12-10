import time
import os
from pathlib import Path
from workflow import ResumeProcessor
import shutil
from text_processor import TextProcessor

class ResumeOrchestrator:
    def __init__(self, 
                 input_dir: str = "resumes",
                 processing_dir: str = "processing",
                 text_output_dir: str = "tobeprocessed",
                 processed_dir: str = "processed",
                 check_interval: int = 5):
        
        # Initialize directories
        self.input_dir = Path(input_dir)
        self.processing_dir = Path(processing_dir)
        self.text_output_dir = Path(text_output_dir)
        self.processed_dir = Path(processed_dir)
        
        # Create all required directories
        for directory in [self.input_dir, self.processing_dir, 
                         self.text_output_dir, self.processed_dir]:
            directory.mkdir(exist_ok=True)
            
        self.check_interval = check_interval
        self.resume_processor = ResumeProcessor(
            input_dir=str(self.processing_dir),
            output_dir=str(self.text_output_dir)
        )
        self.text_processor = TextProcessor()
        
    def _move_file(self, file_path: Path, destination_dir: Path) -> Path:
        """Safely move a file to a destination directory"""
        destination = destination_dir / file_path.name
        
        # If file already exists in destination, add a timestamp
        if destination.exists():
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            destination = destination_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
            
        return Path(shutil.move(str(file_path), str(destination)))
    
    def process_pending_resumes(self):
        """Process any PDF files in the input directory"""
        for pdf_file in self.input_dir.glob("*.pdf"):
            try:
                # Move to processing directory
                print(f"Moving {pdf_file.name} to processing directory...")
                processing_file = self._move_file(pdf_file, self.processing_dir)
                
                # Process the file
                self.resume_processor.process_single_resume(processing_file)
                
                # Move to processed directory
                print(f"Moving {processing_file.name} to processed directory...")
                self._move_file(processing_file, self.processed_dir)
                
            except Exception as e:
                print(f"Error processing {pdf_file.name}: {str(e)}")
                # Could implement error handling/retry logic here
    
    def process_pending_texts(self):
        """Process any text files in the tobeprocessed directory"""
        for text_file in self.text_output_dir.glob("*.txt"):
            try:
                self.text_processor.process_text(text_file)
                # Move or delete processed text file
            except Exception as e:
                print(f"Error processing text file {text_file.name}: {str(e)}")
    
    def run(self):
        """Main loop to continuously check for new files"""
        print(f"Starting resume processing service...")
        print(f"Monitoring directory: {self.input_dir}")
        print(f"Checking every {self.check_interval} seconds")
        
        while True:
            try:
                # Process PDFs
                self.process_pending_resumes()
                
                # Process extracted text
                self.process_pending_texts()
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                print("\nShutting down resume processing service...")
                break
            except Exception as e:
                print(f"Error in main loop: {str(e)}")
                # Could implement retry logic or alerting here
                time.sleep(self.check_interval)

if __name__ == "__main__":
    orchestrator = ResumeOrchestrator()
    orchestrator.run() 