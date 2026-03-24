from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import PyPDF2
import google.generativeai as genai
from dotenv import load_dotenv
import os
from typing import Dict, List
from pathlib import Path

class DocumentProcessor:
    """Process PDFs and images to extract text and structured data."""
    
    def __init__(self):
        load_dotenv()
        self.gemini_api = os.getenv("GEMINI_API_KEY")
        server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.public_dir = os.path.join(server_dir, "public")
        self.public2_dir = os.path.join(server_dir, "public2")
        
        # Create directories if they don't exist
        os.makedirs(self.public_dir, exist_ok=True)
        os.makedirs(self.public2_dir, exist_ok=True)
        
        genai.configure(api_key=self.gemini_api)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def _filter_not_found(self, text: str) -> str:
        """Remove lines that contain 'Not found'."""
        lines = text.split('\n')
        filtered_lines = []
        for line in lines:
            # Keep section headers and lines that don't have "Not found"
            if 'Not found' not in line or line.strip().startswith('-') or line.strip() == '':
                filtered_lines.append(line)
        return '\n'.join(filtered_lines)
    
    def _merge_data(self, all_data: List[str]) -> str:
        """Merge data from multiple documents, removing duplicates and 'Not found' entries."""
        merged = {}
        
        for data in all_data:
            lines = data.split('\n')
            for line in lines:
                if ':' in line and 'Not found' not in line:
                    key = line.split(':', 1)[0].strip()
                    value = line.split(':', 1)[1].strip()
                    if value and value != 'Not found':
                        if key not in merged or not merged[key]:
                            merged[key] = value
        
        # Reconstruct the formatted output
        output = []
        output.append("---------------------------------------")
        output.append("PERSONAL INFORMATION SUMMARY")
        output.append("")
        
        personal_fields = ['Name', 'Date of Birth', 'Age', 'Gender', 'Nationality', 'Religion', 
                          'Caste / Community', 'Marital Status', 'Blood Group', 
                          "Father's Name", "Mother's Name"]
        for field in personal_fields:
            if field in merged:
                output.append(f"{field}: {merged[field]}")
        
        output.append("")
        output.append("IDENTITY DETAILS")
        output.append("")
        
        identity_fields = ['Aadhaar Number', 'PAN Card Number', 'Passport Number', 
                          'Voter ID', 'Driving License Number']
        for field in identity_fields:
            if field in merged:
                output.append(f"{field}: {merged[field]}")
        
        output.append("")
        output.append("CONTACT & ADDRESS DETAILS")
        output.append("")
        
        contact_fields = ['Mobile Number', 'Email Address', 'Permanent Address', 
                         'Current Address', 'District', 'State', 'Pincode']
        for field in contact_fields:
            if field in merged:
                output.append(f"{field}: {merged[field]}")
        
        output.append("")
        output.append("PROFESSIONAL & FINANCIAL DETAILS")
        output.append("")
        
        professional_fields = ['Educational Qualification', 'Institution / University', 
                              'Occupation', 'Annual Income', 'Bank Account Number', 'IFSC Code']
        for field in professional_fields:
            if field in merged:
                output.append(f"{field}: {merged[field]}")
        
        output.append("")
        output.append("EMERGENCY CONTACT DETAILS")
        output.append("")
        
        emergency_fields = ['Name', 'Relationship', 'Contact Number']
        for field in emergency_fields:
            emergency_key = f"Emergency {field}" if field != 'Relationship' else field
            if emergency_key in merged:
                output.append(f"{field}: {merged[emergency_key]}")
            elif field == 'Name' and 'Emergency Contact Name' in merged:
                output.append(f"{field}: {merged['Emergency Contact Name']}")
            elif field == 'Contact Number' and 'Emergency Contact Number' in merged:
                output.append(f"{field}: {merged['Emergency Contact Number']}")
        
        output.append("---------------------------------------")
        
        return '\n'.join(output)
    
    def _process_image_with_gemini(self, image_path: str) -> Dict[str, str]:
        """Send image directly to Gemini vision model for analysis."""
        try:
            print(f"Sending image to Gemini Vision...")
            image = Image.open(image_path)
            
            prompt = """You are a professional digital assistant designed to extract and organize personal information from documents.

                    Extract the following personal details from this image and format them exactly as shown below. If any field is not found, write "Not found".

                    Format the output exactly like this:

                    ---------------------------------------
                    PERSONAL INFORMATION SUMMARY

                    Name: [extract full name]
                    Date of Birth: [extract date of birth]
                    Age: [extract age]
                    Gender: [extract gender]
                    Nationality: [extract nationality]
                    Religion: [extract religion]
                    Caste / Community: [extract caste/community]
                    Marital Status: [extract marital status]
                    Blood Group: [extract blood group]
                    Father's Name: [extract father's name]
                    Mother's Name: [extract mother's name]

                    IDENTITY DETAILS

                    Aadhaar Number: [extract Aadhaar number]
                    PAN Card Number: [extract PAN card number]
                    Passport Number: [extract passport number]
                    Voter ID: [extract voter ID]
                    Driving License Number: [extract driving license number]

                    CONTACT & ADDRESS DETAILS

                    Mobile Number: [extract mobile number]
                    Email Address: [extract email address]
                    Permanent Address: [extract permanent address]
                    Current Address: [extract current address]
                    District: [extract district]
                    State: [extract state]
                    Pincode: [extract pincode]

                    PROFESSIONAL & FINANCIAL DETAILS

                    Educational Qualification: [extract educational qualification]
                    Institution / University: [extract institution/university]
                    Occupation: [extract occupation]
                    Annual Income: [extract annual income]
                    Bank Account Number: [extract bank account number]
                    IFSC Code: [extract IFSC code]

                    EMERGENCY CONTACT DETAILS

                    Name: [extract emergency contact name]
                    Relationship: [extract relationship]
                    Contact Number: [extract emergency contact number]
                    ---------------------------------------
                    """
            response = self.model.generate_content([prompt, image])
            return {"result": response.text.strip()}
        except Exception as e:
            print(f"Error processing image with Gemini: {e}")
            import traceback
            traceback.print_exc()
            return {"result": f"Error: {str(e)}"}
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF."""
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            if text.strip():
                print(f"Extracted text from PDF: {os.path.basename(pdf_path)}")
                return text.strip()
            else:
                print(f"No text found in PDF, trying OCR: {os.path.basename(pdf_path)}")
                return self._extract_text_from_pdf_with_ocr(pdf_path)
        except Exception as e:
            print(f"Error extracting text from PDF {pdf_path}: {e}")
            return ""
    
    def _extract_text_from_pdf_with_ocr(self, pdf_path: str) -> str:
        """Extract text from PDF using OCR (for scanned PDFs)."""
        try:
            images = convert_from_path(pdf_path)
            text = ""
            for i, image in enumerate(images):
                page_text = pytesseract.image_to_string(image)
                text += f"Page {i+1}:\n{page_text}\n\n"
            return text.strip()
        except Exception as e:
            print(f"Error with OCR on PDF {pdf_path}: {e}")
            return ""
    
    def _process_with_gemini(self, text: str) -> Dict[str, str]:
        """Send extracted text to Gemini for structured extraction."""
        try:
            prompt = f"""You are a professional digital assistant designed to extract and organize personal information from documents.

                Extract the following personal details from the text and format them exactly as shown below. If any field is not found, write "Not found".

                Text to analyze:
                {text}

                Format the output exactly like this:

                ---------------------------------------
                PERSONAL INFORMATION SUMMARY

                Name: [extract full name]
                Date of Birth: [extract date of birth]
                Age: [extract age]
                Gender: [extract gender]
                Nationality: [extract nationality]
                Religion: [extract religion]
                Caste / Community: [extract caste/community]
                Marital Status: [extract marital status]
                Blood Group: [extract blood group]
                Father's Name: [extract father's name]
                Mother's Name: [extract mother's name]

                IDENTITY DETAILS

                Aadhaar Number: [extract Aadhaar number]
                PAN Card Number: [extract PAN card number]
                Passport Number: [extract passport number]
                Voter ID: [extract voter ID]
                Driving License Number: [extract driving license number]

                CONTACT & ADDRESS DETAILS

                Mobile Number: [extract mobile number]
                Email Address: [extract email address]
                Permanent Address: [extract permanent address]
                Current Address: [extract current address]
                District: [extract district]
                State: [extract state]
                Pincode: [extract pincode]

                PROFESSIONAL & FINANCIAL DETAILS

                Educational Qualification: [extract educational qualification]
                Institution / University: [extract institution/university]
                Occupation: [extract occupation]
                Annual Income: [extract annual income]
                Bank Account Number: [extract bank account number]
                IFSC Code: [extract IFSC code]

                EMERGENCY CONTACT DETAILS

                Name: [extract emergency contact name]
                Relationship: [extract relationship]
                Contact Number: [extract emergency contact number]
                ---------------------------------------
                """
            response = self.model.generate_content(prompt)
            return {"result": response.text.strip()}
        except Exception as e:
            print(f"Error processing with Gemini: {e}")
            return {"result": f"Error: {str(e)}"}
    
    def process_all_documents(self) -> Dict[str, str]:
        """Process all documents and combine into one file."""
        if not os.path.exists(self.public_dir):
            raise FileNotFoundError(f"Directory not found: {self.public_dir}")
        
        all_extracted_data = []
        supported_images = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif')
        
        files = sorted(os.listdir(self.public_dir))
        
        for file_name in files:
            file_path = os.path.join(self.public_dir, file_name)
            
            if not os.path.isfile(file_path):
                continue
            
            extracted_text = ""
            gemini_result = None
            
            if file_name.lower().endswith('.pdf'):
                print(f"\nProcessing PDF: {file_name}")
                extracted_text = self._extract_text_from_pdf(file_path)
                if extracted_text:
                    print(f"Sending to Gemini for analysis...")
                    gemini_result = self._process_with_gemini(extracted_text)
            
            elif file_name.lower().endswith(supported_images):
                print(f"\nProcessing Image: {file_name}")
                gemini_result = self._process_image_with_gemini(file_path)
            
            elif file_name.lower().endswith(('.txt', '.md')):
                print(f"\nProcessing Text file: {file_name}")
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    extracted_text = f.read()
                if extracted_text:
                    print(f"Sending to Gemini for analysis...")
                    gemini_result = self._process_with_gemini(extracted_text)
            
            else:
                print(f"Skipping unsupported file: {file_name}")
                continue
            
            if gemini_result:
                all_extracted_data.append(gemini_result["result"])
        
        if not all_extracted_data:
            return {"result": "No documents processed"}
        
        # Merge all data and filter out "Not found"
        merged_data = self._merge_data(all_extracted_data)
        
        # Save to public directory as user_data.txt
        output_file = os.path.join(self.public_dir, "user_data.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(merged_data)
        
        print(f"\n✓ All documents combined and saved to: {output_file}")
        
        return {
            "result": merged_data,
            "output_file": output_file,
            "files_processed": len(all_extracted_data)
        }
    
    async def process_first_document(self) -> Dict[str, str]:
        """Process only the first document found and save to public2."""
        if not os.path.exists(self.public_dir):
            raise FileNotFoundError(f"Directory not found: {self.public_dir}")
        
        supported_images = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif')
        files = sorted(os.listdir(self.public_dir))
        
        for file_name in files:
            file_path = os.path.join(self.public_dir, file_name)
            
            if not os.path.isfile(file_path):
                continue
            
            extracted_text = ""
            
            if file_name.lower().endswith('.pdf'):
                print(f"Processing PDF: {file_name}")
                extracted_text = self._extract_text_from_pdf(file_path)
            
            elif file_name.lower().endswith(supported_images):
                print(f"Processing Image: {file_name}")
                # Send image directly to Gemini
                gemini_result = self._process_image_with_gemini(file_path)
                
                # Save to public directory as user_data.txt
                output_file = os.path.join(self.public_dir, "user_data.txt")
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(gemini_result["result"])
                
                print(f"Saved to: {output_file}")
                
                return {
                    "result": gemini_result["result"],
                    "output_file": output_file
                }
            
            elif file_name.lower().endswith(('.txt', '.md')):
                print(f"Processing Text file: {file_name}")
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    extracted_text = f.read()
            
            if extracted_text:
                print("Sending to Gemini for analysis...")
                gemini_result = self._process_with_gemini(extracted_text)
                
                # Save to public directory as user_data.txt
                output_file = os.path.join(self.public_dir, "user_data.txt")
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(gemini_result["result"])
                
                print(f"Saved to: {output_file}")
                
                return {
                    "result": gemini_result["result"],
                    "output_file": output_file
                }
        
        return {"result": "No supported documents found"}

async def process_documents():
    """Process all documents in public directory."""
    processor = DocumentProcessor()
    return processor.process_all_documents()

async def process_first_doc():
    """Process only the first document."""
    processor = DocumentProcessor()
    return await processor.process_first_document()