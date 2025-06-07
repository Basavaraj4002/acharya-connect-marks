 # backend/gemini_prompt_engine.py

import json
import httpx  # Use httpx to make web requests

PROMPT_TEMPLATE = """
You are an expert academic administration assistant. Your task is to parse a teacher's natural language description of an internal assessment scheme and convert it into a structured JSON object.

**Rules and Constraints:**
1.  The root JSON object must have a `total` key (number) and a `components` key (array of objects).
2.  Each object in the `components` array must have a `name` (string) and a `weight` (number).
3.  If a component is broken down further, it must have a `subcomponents` key, which is an array of sub-component objects. If not, the `subcomponents` array should be empty `[]`.
4.  Each sub-component object must also have a `name` (string) and a `weight` (number).
5.  **Crucially, you must perform the math:**
    *   The sum of all top-level `component` weights MUST equal the root `total`.
    *   For any component with `subcomponents`, the sum of their `weights` MUST equal the parent component's `weight`.
6.  If the user's description is ambiguous or the numbers don't add up, use your best judgment to create a logical structure. Add a `notes` key at the root level of the JSON with a string explaining any assumptions or corrections you made.
7.  **Output ONLY the raw JSON object. Do not include any explanatory text, introductions, or markdown formatting like ```json.**

**Teacher's Prompt:**
\"\"\"
{prompt}
\"\"\"

**Generated JSON:**
"""

async def generate_table_from_prompt(prompt: str, api_key: str) -> dict:
    """
    Generates a table by making a direct REST API call to Google's AI service.
    """
    if not api_key:
        raise ValueError("Google API Key is missing.")

    full_prompt = PROMPT_TEMPLATE.format(prompt=prompt)
    
    # --- THIS IS THE FINAL FIX ---
    # The URL now points to a model proven to be available for your API key.
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}]
    }
    
    headers = {'Content-Type': 'application/json'}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=60.0)
            response.raise_for_status()
            
            response_json = response.json()
            response_text = response_json['candidates'][0]['content']['parts'][0]['text']

            if response_text.strip().startswith("```json"):
                response_text = response_text.strip().removeprefix("```json").removesuffix("```")
            
            return json.loads(response_text)

        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        except (KeyError, IndexError):
            raise ValueError(f"Could not parse Google's API response structure. Raw response: {response.json()}")
        except json.JSONDecodeError:
            raise ValueError(f"Failed to decode the final JSON from the model's text. Raw text: {response_text}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred during API call: {e}")