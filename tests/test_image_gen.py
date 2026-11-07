import os
import requests
import json
from dotenv import load_dotenv

def print_sync(msg):
    print(msg, flush=True)

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    print_sync("❌ ERROR: OPENROUTER_API_KEY missing in .env")
    exit()

print_sync(f"📡 Neural Link Verified. Key Fragment: ...{api_key[-4:]}")

def generate_test_image():
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Title": "Synapse AI Social Agent"
    }
    
    # UPDATED 2026 MODEL SLUGS
    # 'openai/dall-e-3' is often restricted to specific headers. 
    # Use 'google/gemini-2.5-flash-image' for the most reliable 2026 results.
    models_to_try = [
        "google/gemini-2.5-flash-image",  # 2026 Flagship (Nano Banana)
        "openai/gpt-5-image-mini",        # Newest high-speed OpenAI image model
        "black-forest-labs/flux-1-schnell" # Reliable high-speed alternative
    ]

    for model_id in models_to_try:
        payload = {
            "model": model_id, 
            "messages": [
                {
                    "role": "user", 
                    "content": "A high-tech cyan 'S' logo for an AI agent, glowing neon, dark background."
                }
            ],
            # CRITICAL: This parameter distinguishes image gen from text gen
            "modalities": ["image", "text"] 
        }

        try:
            print_sync(f"🚀 ATTEMPTING MODEL: {model_id}...")
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                # 2026 Standard: Images are returned in the choice message array
                message = data["choices"][0]["message"]
                if "images" in message:
                    img_data = message["images"][0]
                    # Direct URL or nested image_url object
                    img_url = img_data["image_url"]["url"] if isinstance(img_data, dict) else img_data
                    print_sync(f"✅ SUCCESS with {model_id}!")
                    print_sync(f"🔗 IMAGE URL: {img_url}")
                    return 
                else:
                    print_sync(f"📝 TEXT_ONLY RECEIVED: {message.get('content')[:100]}...")
            else:
                print_sync(f"❌ {model_id} FAILED (Status {response.status_code})")
                print_sync(f"📝 ERROR LOG: {response.text[:150]}")
                
        except Exception as e:
            print_sync(f"⚠️ {model_id} EXCEPTION: {str(e)}")

    print_sync("❌ ALL MODELS FAILED. Ensure 'Prompt Training' is enabled in your OpenRouter Privacy settings.")

if __name__ == "__main__":
    generate_test_image()
    