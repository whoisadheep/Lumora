"""
Metadata Agent
Generates viral YouTube Shorts titles, descriptions, tags, and hashtags using Gemini.
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


def generate_metadata(topic_hint):
    """Generates viral title, description, tags, and hashtags for a YouTube Short."""
    global gemini_client
    prompt = f"""
    You are a YouTube Shorts SEO expert. Generate metadata for this video:
    Topic: {topic_hint}
    
    Return EXACTLY in this format (no extra text, no emojis in TITLE):
    TITLE: [Catchy clickbait title under 70 chars, NO emojis]
    DESCRIPTION: [2-3 engaging sentences. Include call to action. No emojis.]
    TAGS: [comma-separated list of 15 relevant trending tags]
    HASHTAGS: [8-10 hashtags including #shorts #viral #trending]
    """

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.9),
            )
            text = response.text.strip()
            metadata = {}
            for line in text.split('\n'):
                line = line.strip()
                if line.startswith('TITLE:'):
                    metadata['title'] = line.replace('TITLE:', '').strip()
                elif line.startswith('DESCRIPTION:'):
                    metadata['description'] = line.replace('DESCRIPTION:', '').strip()
                elif line.startswith('TAGS:'):
                    metadata['tags'] = [t.strip() for t in line.replace('TAGS:', '').strip().split(',')]
                elif line.startswith('HASHTAGS:'):
                    metadata['hashtags'] = line.replace('HASHTAGS:', '').strip()

            if 'title' in metadata and 'description' in metadata:
                if 'hashtags' in metadata:
                    metadata['description'] += '\n\n' + metadata['hashtags']
                metadata['description'] += '\n#shorts'
                return metadata
        except Exception as e:
            error_msg = str(e)
            print(f"  [Metadata] Gemini error (attempt {attempt + 1}): {error_msg}")
            
            # Switch to backup key if we hit quota or availability issues
            if ("429" in error_msg or "503" in error_msg or "RESOURCE_EXHAUSTED" in error_msg) and backup_key:
                print(f"  [Metadata] Rotating to backup API key...")
                gemini_client = get_gemini_client(backup_key)
            
            # Wait longer on each attempt
            time.sleep(5 * (attempt + 1))

    # Fallback metadata
    return {
        'title': 'You Wont Believe What Was Caught on Camera #shorts',
        'description': 'This is INSANE! Watch till the end!\n\n#shorts #viral #trending',
        'tags': ['shorts', 'viral', 'trending', 'caught on camera']
    }
