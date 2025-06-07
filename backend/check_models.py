# backend/check_models.py

import os
import httpx
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

def check_available_models():
    """
    Connects to Google's API and lists all available models for the provided API key.
    """
    if not API_KEY:
        print("🔴 FATAL ERROR: GOOGLE_API_KEY not found in your .env file.")
        return

    print("--- Checking available Google AI Models ---")
    print(f"Using API Key ending in: ...{API_KEY[-4:]}")

    # The official URL to list models
    url = f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}"
    
    try:
        response = httpx.get(url, timeout=30.0)
        response.raise_for_status()  # Raise an error for bad status codes (4xx or 5xx)
        
        data = response.json()
        
        print("\n✅ Successfully retrieved model list. Models that support 'generateContent':")
        
        found_model = False
        for model in data.get('models', []):
            # We only care about models that can generate text content
            if 'generateContent' in model.get('supportedGenerationMethods', []):
                found_model = True
                print(f"\n  - Model Name: {model['name']}")
                print(f"    Display Name: {model['displayName']}")
                print(f"    Description: {model['description']}")

        if not found_model:
            print("\n❌ No models supporting 'generateContent' were found for your API key.")
            print("This might be an issue with your Google AI project permissions.")
        else:
            print("\n-----------------------------------------------------")
            print("Please use one of the 'Model Name' values from the list above in your code.")
            print("The most common one is 'models/gemini-pro'.")
            print("-----------------------------------------------------")


    except httpx.HTTPStatusError as e:
        print(f"\n🔴 HTTP ERROR: Could not connect to Google API.")
        print(f"Status Code: {e.response.status_code}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"\n🔴 An unexpected error occurred: {e}")

# --- Run the function ---
if __name__ == "__main__":
    check_available_models()