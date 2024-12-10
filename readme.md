# Backend to support resume processing
A Django-based system for processing and parsing resumes.

## Workflow
1. **PDF Processing & OCR**
   - Input: PDF resume
   - Process: Convert PDF to images and perform OCR using Tesseract
   - Output: Extracted text

2. **Resume Parsing using NLP**
   - Input: Extracted text from OCR
   - Process: Use DistilBERT for Named Entity Recognition (NER) and text classification
   - Output: Structured JSON with following information:
     - Personal Information (name, email, phone)
     - Education
     - Work Experience
     - Skills
     - Projects
     - Certifications

3. **Data Validation & Storage**
   - Validate extracted information
   - Store in structured format
   - Provide API endpoints for retrieval

## Technologies
- Django: Backend framework
- Tesseract: OCR engine
- DistilBERT: NLP model for information extraction
- pdf2image: PDF to image conversion
- PostgreSQL: Database storage

## Future Enhancements
- LLM Integration: Use Llama 2 for enhanced parsing and understanding
- Multi-language support
- Resume scoring and ranking

