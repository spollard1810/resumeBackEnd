# Resume Processing Backend

A Python-based system for processing and parsing resumes using OCR and Large Language Models.

## Workflow

1. **PDF Processing & OCR**
   - Input: PDF resume
   - Process: Convert PDF to images and perform OCR using Tesseract
   - Output: Extracted text

2. **Resume Parsing using LLM**
   - Input: Extracted text from OCR
   - Process: Use OpenRouter API (Amazon Nova Micro) to analyze and structure resume content
   - Output: Structured JSON with the following sections:
     - Personal Information
       - Name
       - Email
       - Phone
       - Location
       - LinkedIn
     - Education
       - Institution
       - Degree
       - Dates
       - Certifications
     - Experience
       - Company
       - Title
       - Dates
       - Location
       - Achievements
     - Skills
       - Technical
       - Soft
       - Languages
       - Tools
     - Projects
       - Name
       - Description
       - Technologies
       - URLs

3. **File Management**
   - Organized directory structure for:
     - Input resumes (PDF)
     - Processing directory
     - Extracted text
     - Parsed JSON output
     - Raw LLM outputs (for debugging)
     - Processing logs

## Technologies
- Python 3.x
- Tesseract: OCR engine
- pdf2image: PDF to image conversion
- OpenRouter API: Access to advanced LLMs
- Amazon Nova Micro: Primary LLM for resume parsing

## Key Features
- Robust PDF text extraction
- Structured information parsing
- Detailed logging and debugging capabilities
- Error handling and recovery
- Raw LLM response storage for analysis

## Setup
1. Install requirements:
   bash
   pip install -r requirements.txt
   

2. Install system dependencies:
   - Tesseract OCR
   - Poppler (for pdf2image)

3. Set up environment variables:
  
   OPENROUTER_API_KEY=your_api_key_here
   

## Usage
python
from resume_processor.main import ResumeOrchestrator
orchestrator = ResumeOrchestrator()
orchestrator.run()
Place PDF resumes in the `resumes` directory and the system will automatically:
1. Process them using OCR
2. Extract structured information using LLM
3. Save results as JSON in the `parsed` directory
## Directory Structure
├── resumes/ # Input PDF files
├── processing/ # Temporary processing directory
├── tobeprocessed/ # Extracted text files
├── parsed/ # Output JSON files
├── raw_outputs/ # Raw LLM responses
├── logs/ # Processing logs
└── resume_processor/ # Source code
## Future Enhancements
- Support for additional LLM models
- Multi-language support
- Resume scoring and ranking
- API endpoint integration
- Enhanced error recovery
- Batch processing capabilities