from pathlib import Path
import json
import os
import logging
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime

class TextProcessor:
    def __init__(self, input_dir: str = "tobeprocessed", output_dir: str = "parsed", log_dir: str = "logs"):
        # Set up logging
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        log_file = self.log_dir / f"api_transactions_{datetime.now().strftime('%Y%m%d')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Set up directories
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

        # Load environment variables
        load_dotenv()
        
        # Initialize OpenAI client
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )

        # Define the analysis prompt
        self.analysis_prompt = """
        Analyze this resume and extract key information in the following format:

        PERSONAL INFORMATION
        - Extract: Full name, email, phone number, location, and LinkedIn profile if available
        

        EDUCATION
        - Extract: List each degree, institution, dates, GPA, and relevant coursework
        

        EXPERIENCE
        - Extract: For each position, list company, title, dates, location, and key achievements
        

        SKILLS
        - Extract: Technical skills, soft skills, languages, and tools
        

        PROJECTS
        - Extract: Project names, descriptions, technologies used, and URLs if available
       

        Resume text:
        {text}

        Please analyze thoroughly and provide clear, structured information for each section. 
        """

    def _get_llm_analysis(self, text: str) -> dict:
        """Get LLM analysis of the resume text"""
        try:
            self.logger.info("Starting LLM analysis request")
            start_time = datetime.now()

            response = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://github.com/pollards/resumeBackEnd",
                    "X-Title": "Resume Parser"
                },
                model="amazon/nova-micro-v1",
                messages=[
                    {"role": "system", "content": "You are a resume analysis expert."},
                    {"role": "user", "content": self.analysis_prompt.format(text=text)}
                ]
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Get the raw response content
            raw_content = response.choices[0].message.content
            
            # Save raw LLM output to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            raw_output_dir = Path("raw_outputs")
            raw_output_dir.mkdir(exist_ok=True)
            raw_output_file = raw_output_dir / f"llm_output_{timestamp}.txt"
            
            with open(raw_output_file, 'w', encoding='utf-8') as f:
                f.write(f"Duration: {duration:.2f} seconds\n")
                f.write(f"Model: amazon/nova-micro-v1\n")
                f.write(f"Completion Tokens: {response.usage.completion_tokens if hasattr(response, 'usage') else 'N/A'}\n")
                f.write(f"Prompt Tokens: {response.usage.prompt_tokens if hasattr(response, 'usage') else 'N/A'}\n")
                f.write("\nRAW LLM RESPONSE:\n")
                f.write("="*50 + "\n")
                f.write(raw_content)
                f.write("\n" + "="*50)
            
            # Log the transaction details
            self.logger.info(f"""
                API Transaction Complete:
                - Duration: {duration:.2f} seconds
                - Model: amazon/nova-micro-v1
                - Response Length: {len(raw_content)} chars
                - Completion Tokens: {response.usage.completion_tokens if hasattr(response, 'usage') else 'N/A'}
                - Prompt Tokens: {response.usage.prompt_tokens if hasattr(response, 'usage') else 'N/A'}
                - Raw output saved to: {raw_output_file}
            """)
            
            return self._parse_llm_response(raw_content)

        except Exception as e:
            self.logger.error(f"Error in LLM analysis: {str(e)}", exc_info=True)
            return None

    def _parse_llm_response(self, content: str) -> dict:
        """Parse the LLM's response into structured JSON"""
        try:
            # Initialize empty structure
            parsed_data = {
                "personal_info": {},
                "education": [],
                "experience": [],
                "skills": {},
                "projects": []
            }

            # Split content into sections
            current_section = None
            current_data = []
            
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Check for main section headers
                if line.startswith('###'):
                    # Save previous section if it exists
                    if current_section and current_data:
                        parsed_data[current_section.lower()] = self._parse_section(current_section, current_data)
                    
                    # Start new section
                    current_section = line.strip('#').strip().lower()
                    if "personal" in current_section:
                        current_section = "personal_info"
                    current_data = []
                else:
                    current_data.append(line)

            # Save the last section
            if current_section and current_data:
                parsed_data[current_section.lower()] = self._parse_section(current_section, current_data)

            return parsed_data

        except Exception as e:
            self.logger.error(f"Error parsing LLM response: {str(e)}", exc_info=True)
            return None

    def _parse_section(self, section_name: str, lines: list) -> dict or list:
        """Parse a section based on its name"""
        section_name = section_name.lower()
        
        if "personal" in section_name:
            return self._parse_section_items(lines)
        elif "education" in section_name:
            return self._parse_section_items(lines)
        elif "experience" in section_name:
            return self._parse_section_items(lines)
        elif "skills" in section_name:
            return self._parse_section_items(lines)
        elif "projects" in section_name:
            return self._parse_section_items(lines)
        else:
            # Handle any additional sections
            return self._parse_section_items(lines)

    def _parse_section_items(self, lines: list) -> dict or list:
        """Parse items within a section"""
        items = {}
        current_key = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line is a key-value pair
            if line.startswith('- **') or line.startswith('**'):
                # Remove markdown formatting
                line = line.replace('- **', '').replace('**', '')
                
                # Split into key-value if possible
                if ':' in line:
                    key, value = line.split(':', 1)
                    items[key.strip().lower()] = value.strip()
                    current_key = key.strip().lower()
                else:
                    # Handle cases where the line is just a key
                    current_key = line.strip().lower()
                    items[current_key] = []
            elif line.startswith('- '):
                # Handle bullet points
                if current_key and isinstance(items[current_key], list):
                    items[current_key].append(line.replace('- ', '').strip())
                else:
                    # If no current key, add to generic list
                    if 'items' not in items:
                        items['items'] = []
                    items['items'].append(line.replace('- ', '').strip())
            elif current_key:
                # Append to current key if it exists
                if isinstance(items[current_key], list):
                    items[current_key].append(line)
                else:
                    items[current_key] = items[current_key] + " " + line
        
        return items

    def process_text(self, text_file: Path):
        """Process the text file and extract structured information"""
        try:
            self.logger.info(f"Starting processing of {text_file.name}")
            
            # Read the text file
            with open(text_file, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Get LLM analysis
            parsed_data = self._get_llm_analysis(text)
            
            if parsed_data:
                # Save as JSON
                output_file = self.output_dir / f"{text_file.stem}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(parsed_data, f, indent=2)
                    
                self.logger.info(f"Successfully parsed {text_file.name}")
                
            
        except Exception as e:
            self.logger.error(f"Error processing {text_file.name}: {str(e)}", exc_info=True)