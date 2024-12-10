from pathlib import Path
import json
import os
import logging
from dotenv import load_dotenv
from openai import OpenAI
import asyncio
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

        # Define the parsing prompt
        self.base_prompt = """
        You are a resume parsing expert. Analyze the following resume text and extract key information into a structured JSON format.
        Also provide suggestions for improving each section.
        
        For each section, return both the extracted data and improvement suggestions.
        
        Resume text:
        {text}
        
        Return the response in the following JSON format:
        """

        self.json_template = """{
            "personal_info": {
                "extracted": {
                    "name": "",
                    "email": "",
                    "phone": "",
                    "location": "",
                    "linkedin": ""
                },
                "improvements": []
            },
            "education": {
                "extracted": [
                    {
                        "degree": "",
                        "institution": "",
                        "date": "",
                        "gpa": "",
                        "relevant_coursework": []
                    }
                ],
                "improvements": []
            },
            "experience": {
                "extracted": [
                    {
                        "company": "",
                        "title": "",
                        "date_range": "",
                        "location": "",
                        "achievements": []
                    }
                ],
                "improvements": []
            },
            "skills": {
                "extracted": {
                    "technical": [],
                    "soft": [],
                    "languages": [],
                    "tools": []
                },
                "improvements": []
            },
            "projects": {
                "extracted": [
                    {
                        "name": "",
                        "description": "",
                        "technologies": [],
                        "url": ""
                    }
                ],
                "improvements": []
            }
        }"""

    async def _get_llm_analysis(self, text: str) -> dict:
        """Get LLM analysis of the resume text"""
        try:
            self.logger.info("Starting LLM analysis request")
            start_time = datetime.now()

            # Combine the prompt parts
            full_prompt = self.base_prompt.format(text=text) + "\n" + self.json_template

            response = await self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://github.com/pollards/resumeBackEnd",
                    "X-Title": "Resume Parser"
                },
                model="meta-llama/llama-3.3-70b-instruct",
                messages=[
                    {"role": "system", "content": "You are a resume parsing expert."},
                    {"role": "user", "content": full_prompt}
                ]
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Log the transaction details
            self.logger.info(f"""
                API Transaction Complete:
                - Duration: {duration:.2f} seconds
                - Model: meta-llama/llama-3.3-70b-instruct
                - Response Length: {len(response.choices[0].message.content)} chars
                - Completion Tokens: {response.usage.completion_tokens if hasattr(response, 'usage') else 'N/A'}
                - Prompt Tokens: {response.usage.prompt_tokens if hasattr(response, 'usage') else 'N/A'}
            """)
            
            # Extract and parse the JSON response
            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            self.logger.error(f"Error in LLM analysis: {str(e)}", exc_info=True)
            return None

    def process_text(self, text_file: Path):
        """
        Process the text file and extract structured information using LLM
        Args:
            text_file (Path): Path to the text file to process
        """
        try:
            self.logger.info(f"Starting processing of {text_file.name}")
            
            # Read the text file
            with open(text_file, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Get LLM analysis
            parsed_data = asyncio.run(self._get_llm_analysis(text))
            
            if parsed_data:
                # Save as JSON
                output_file = self.output_dir / f"{text_file.stem}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(parsed_data, f, indent=2)
                    
                self.logger.info(f"Successfully parsed {text_file.name}")
                
                # Print improvement suggestions
                print("\nImprovement Suggestions:")
                for section, data in parsed_data.items():
                    if "improvements" in data and data["improvements"]:
                        print(f"\n{section.upper()}:")
                        for improvement in data["improvements"]:
                            print(f"- {improvement}")
            
        except Exception as e:
            self.logger.error(f"Error processing {text_file.name}: {str(e)}", exc_info=True)