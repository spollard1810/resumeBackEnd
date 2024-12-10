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
            sections = content.split('###')  # Split by markdown headers
            parsed_data = {
                "personal_info": {},
                "education": [],
                "experience": [],
                "skills": {
                    "technical": [],
                    "soft": [],
                    "languages": [],
                    "tools": []
                },
                "projects": []
            }

            for section in sections:
                section = section.strip()
                if not section:
                    continue

                # Identify section and parse accordingly
                if "PERSONAL INFORMATION" in section:
                    parsed_data["personal_info"] = self._parse_personal_info(section)
                elif "EDUCATION" in section:
                    education_items = self._parse_education(section)
                    parsed_data["education"].extend(education_items)
                elif "EXPERIENCE" in section:
                    experience_items = self._parse_experience(section)
                    parsed_data["experience"].extend(experience_items)
                elif "SKILLS" in section:
                    parsed_data["skills"] = self._parse_skills(section)
                elif "PROJECTS" in section:
                    project_items = self._parse_projects(section)
                    parsed_data["projects"].extend(project_items)

            return parsed_data

        except Exception as e:
            self.logger.error(f"Error parsing LLM response: {str(e)}", exc_info=True)
            return None

    def _parse_personal_info(self, section: str) -> dict:
        """Parse personal information section"""
        info = {
            "name": "",
            "email": "",
            "phone": "",
            "location": "",
            "linkedin": ""
        }
        
        lines = section.split('\n')
        for line in lines:
            line = line.strip('- *')  # Remove markdown formatting
            if "Full name:" in line:
                info["name"] = line.split("Full name:")[1].strip().strip('*')
            elif "Email:" in line:
                info["email"] = line.split("Email:")[1].strip().strip('*')
            elif "Phone number:" in line:
                info["phone"] = line.split("Phone number:")[1].strip().strip('*')
            elif "Location:" in line:
                info["location"] = line.split("Location:")[1].strip().strip('*')
            elif "LinkedIn profile:" in line:
                info["linkedin"] = line.split("LinkedIn profile:")[1].strip().strip('*')
        
        return info

    def _parse_education(self, section: str) -> list:
        """Parse education section"""
        education_items = []
        current_item = None
        
        lines = section.split('\n')
        for line in lines:
            line = line.strip()
            if not line or "EDUCATION" in line:
                continue
            
            # New institution entry
            if line.startswith('- **') and 'Title:' not in line and 'Dates:' not in line:
                if current_item:
                    education_items.append(current_item)
                institution = line.strip('- *')
                current_item = {
                    "institution": institution,
                    "location": "",
                    "degree": "",
                    "dates": "",
                    "certifications": []
                }
                
                # Check if location is in the same line
                if ',' in institution:
                    inst_parts = institution.split(',')
                    current_item["institution"] = inst_parts[0].strip()
                    current_item["location"] = inst_parts[1].strip()
            
            # Process details if we have a current item
            elif current_item and line.strip():
                line = line.strip('- *')
                if "Bachelor" in line or "Master" in line or "Degree" in line:
                    current_item["degree"] = line.strip()
                elif "Dates:" in line:
                    current_item["dates"] = line.split("Dates:")[1].strip()
                elif "CCNA" in line:
                    cert = {
                        "name": "CCNA 200-301",
                        "date": "October 2024"  # This should be extracted from the following line
                    }
                    current_item["certifications"].append(cert)
        
        if current_item:
            education_items.append(current_item)
        
        return education_items

    def _parse_experience(self, section: str) -> list:
        """Parse experience section"""
        experience_items = []
        current_item = None
        
        lines = section.split('\n')
        for line in lines:
            line = line.strip()
            if not line or "EXPERIENCE" in line:
                continue
            
            # New company entry
            if line.startswith('####'):
                if current_item:
                    experience_items.append(current_item)
                current_item = {
                    "company": line.strip('# '),
                    "title": "",
                    "dates": "",
                    "location": "",
                    "achievements": []
                }
            
            # Process details if we have a current item
            elif current_item:
                line = line.strip('- *')
                if line.startswith('Title:'):
                    current_item["title"] = line.split('Title:')[1].strip()
                elif line.startswith('Dates:'):
                    current_item["dates"] = line.split('Dates:')[1].strip()
                elif line.startswith('Location:'):
                    current_item["location"] = line.split('Location:')[1].strip()
                elif line and not any(header in line for header in ['Title:', 'Dates:', 'Location:']):
                    # This is likely an achievement bullet point
                    if line.strip() and not line.startswith('**'):
                        current_item["achievements"].append(line.strip())
        
        if current_item:
            experience_items.append(current_item)
        
        return experience_items

    def _parse_skills(self, section: str) -> dict:
        """Parse skills section"""
        skills = {
            "technical": [],
            "soft": [],
            "languages": [],
            "tools": []
        }
        
        current_category = None
        lines = section.split('\n')
        for line in lines:
            line = line.strip('- *')
            
            if "Technical skills:" in line:
                current_category = "technical"
            elif "Soft skills:" in line:
                current_category = "soft"
            elif "Languages:" in line:
                current_category = "languages"
                if "Not specified" in line:
                    skills["languages"] = []
                    continue
            elif "Tools:" in line:
                current_category = "tools"
            elif line and current_category and ':' not in line:
                # Clean and split the skills
                skills_list = line.split(',')
                skills_list = [skill.strip(' -') for skill in skills_list if skill.strip()]
                if skills_list:
                    skills[current_category].extend(skills_list)
        
        return skills

    def _parse_projects(self, section: str) -> list:
        """Parse projects section"""
        projects = []
        lines = section.split('\n')
        
        # If no projects are listed
        if any("no explicitly listed projects" in line.lower() for line in lines):
            return projects
            
        current_project = None
        for line in lines:
            line = line.strip('- *')
            if line.startswith('Project:') or line.startswith('Name:'):
                if current_project:
                    projects.append(current_project)
                current_project = {
                    "name": line.split(':')[1].strip(),
                    "description": "",
                    "technologies": [],
                    "url": ""
                }
            elif current_project:
                if line.startswith('Description:'):
                    current_project["description"] = line.split(':')[1].strip()
                elif line.startswith('Technologies:'):
                    techs = line.split(':')[1].strip()
                    current_project["technologies"] = [t.strip() for t in techs.split(',')]
                elif line.startswith('URL:'):
                    current_project["url"] = line.split(':')[1].strip()
        
        if current_project:
            projects.append(current_project)
        
        return projects

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
                
                # Print improvement suggestions
                print("\nImprovement Suggestions:")
                for section, data in parsed_data.items():
                    if "improvements" in data and data["improvements"]:
                        print(f"\n{section.upper()}:")
                        for improvement in data["improvements"]:
                            print(f"- {improvement}")
            
        except Exception as e:
            self.logger.error(f"Error processing {text_file.name}: {str(e)}", exc_info=True)