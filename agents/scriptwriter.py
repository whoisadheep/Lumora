"""
Scriptwriter Agent
Generates viral short-form video scripts with Veo 3.1-ready prompts using Gemini.
"""
import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Initialize with primary key
primary_key = os.getenv("GEMINI_API_KEY")
backup_key = os.getenv("GEMINI_API_KEY_BACKUP")

def get_gemini_client(api_key):
    return genai.Client(api_key=api_key)

gemini_client = get_gemini_client(primary_key)


def generate_script():
    """Generates a single viral short-form video script using Gemini."""
    global gemini_client
    prompt = """
    You are a viral short-form video scriptwriter for YouTube Shorts and TikTok.
    
    Generate ONE unique, dopamine-optimized video script. Pick a random niche from:
    - Cute/funny animal moments
    - Mysterious unexplained events
    - Mind-blowing facts
    - Satisfying or oddly mesmerizing visuals
    - Trending internet culture moments
    
    The script MUST follow this format:
    
    TOPIC: [One-line topic title]
    NICHE: [The niche category]
    
    VEO PROMPT: [A detailed 2-3 sentence visual prompt that can be directly pasted into Google Veo 3.1 to generate the video. Describe the exact scene, camera angle, lighting, mood, and action.]
    
    VOICEOVER SCRIPT: [The narration text, 50-80 words max. Must have a shocking hook in the first line, interesting middle, and a CTA at the end.]
    
    Keep it punchy, dramatic, and impossible to scroll past.
    """

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(temperature=1.0),
            )
            script_text = response.text.strip()

            # Save to file
            os.makedirs('scripts', exist_ok=True)
            timestamp = int(time.time())
            script_path = os.path.join('scripts', f'script_{timestamp}.txt')
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_text)

            return script_text, script_path
        except Exception as e:
            error_msg = str(e)
            print(f"  [Scriptwriter] Gemini error (attempt {attempt + 1}): {error_msg}")
            
            # Switch to backup key if we hit quota or availability issues
            if ("429" in error_msg or "503" in error_msg or "RESOURCE_EXHAUSTED" in error_msg) and backup_key:
                print(f"  [Scriptwriter] Rotating to backup API key...")
                gemini_client = get_gemini_client(backup_key)
            
            # Wait longer on each attempt
            time.sleep(5 * (attempt + 1))

    return None, None
