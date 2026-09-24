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
        # 1. En Güncel ve En Yetenekli Flash Modelleri (Yoğunluk anında geçici hata verebilir ama ilk tercihler)
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash",  # Testinizde direkt çalıştı
        "gemini-3.5-flash",  # Testinizde direkt çalıştı
        # 2. Dinamik "Latest" Modelleri (Google tarafında en güncel kararlı sürüme yönlendirir)
        "gemini-flash-latest",
        # 3. Yüksek Hızlı / Hafif Modeller (JSON çıkarma işlerinde çok hızlı ve etkilidir)
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",  # Testinizde direkt çalıştı
        "gemini-3.1-flash-lite-preview",
        "gemini-flash-lite-latest",
        # 4. Temel Önizleme ve Açık Ağırlıklı Alternatifler (Gerekirse en son fallback)
        "gemini-3-flash-preview",  # Testinizde direkt çalıştı (Adı preview olarak güncellendi)
        # "gemma-4-31b-it",  # Güçlü açık model yedeği
        # "gemma-4-26b-a4b-it",  # Testinizde direkt çalıştı
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
            
    print("Tüm modeller denendi fakat başarılı olunamadı.")
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