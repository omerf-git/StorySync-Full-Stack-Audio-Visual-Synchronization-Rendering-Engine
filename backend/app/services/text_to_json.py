import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

def setup_gemini_api():
    """
    Retrieves the API key from environment variables.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Please set the GEMINI_API_KEY environment variable.")

def generate_json_from_text(system_prompt_path, text):
    # 1. Read system prompt
    with open(system_prompt_path, "r", encoding="utf-8") as f:
        system_instruction = f.read()

    # Fallback list of models (user requested list)
    fallback_models = [
        # 1. Most up-to-date and capable Flash models (may give temporary errors during peak times, but preferred)
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        # 2. Dynamic "Latest" models (always points to the latest stable version)
        "gemini-flash-latest",
        # 3. High-speed / Lightweight models (very fast and effective for JSON extraction)
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-3.1-flash-lite-preview",
        "gemini-flash-lite-latest",
        # 4. Basic Preview and Open Weight Alternatives (absolute fallback if needed)
        "gemini-3-flash-preview",
        # "gemma-4-31b-it",  # Powerful open model backup
        # "gemma-4-26b-a4b-it",
    ]
    
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    last_exception = None
    
    for model_name in fallback_models:
        print(f"Trying model: {model_name}...")
        try:
            # 2. Configure generation settings
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1,  
                top_p=0.8,        
                top_k=40,
                response_mime_type="application/json",
            )

            # 3. Send text to model 
            response = client.models.generate_content(
                model=model_name,
                contents=text,
                config=config
            )
            
            # 4. Parse and return response
            output_data = json.loads(response.text)
            print(f"Success with model {model_name}! Total segments generated: {len(output_data)}")
            return output_data
            
        except Exception as e:
            print(f"Model {model_name} failed: {e}")
            last_exception = e
            continue
            
    print("All models tried but failed.")
    if last_exception:
        raise last_exception
    else:
        raise Exception("Model generation failed.")

def process_documentary_text(system_prompt_path, input_text, output_json_path):
    output_data = generate_json_from_text(system_prompt_path, input_text)
    if output_data:
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
            
        print(f"Output saved to '{output_json_path}'.")

if __name__ == "__main__":
    # Initialize API
    setup_gemini_api()
    
    # File paths
    PROMPT_FILE = "system_prompt.txt"
    INPUT_FILE = "input_text.txt"
    OUTPUT_FILE = "output.json"
    
    # Read text from file
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        document_text = f.read()
    
    # Trigger processing
    process_documentary_text(PROMPT_FILE, document_text, OUTPUT_FILE)