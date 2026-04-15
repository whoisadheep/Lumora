"""
Voiceover Agent
Generates AI voiceover audio from script text using ElevenLabs API.
"""
import os
from dotenv import load_dotenv
from elevenlabs import ElevenLabs

load_dotenv()

elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
client = ElevenLabs(api_key=elevenlabs_key)

VOICEOVER_DIR = "voiceovers"
os.makedirs(VOICEOVER_DIR, exist_ok=True)


def extract_voiceover_text(script_text):
    """Extracts the VOICEOVER SCRIPT section from the generated script."""
    lines = script_text.split('\n')
    capturing = False
    voiceover_lines = []

    for line in lines:
        if line.strip().startswith('VOICEOVER SCRIPT:'):
            capturing = True
            # Grab text after the label on the same line
            text_after = line.replace('VOICEOVER SCRIPT:', '').strip()
            if text_after:
                voiceover_lines.append(text_after)
            continue
        if capturing:
            # Stop if we hit another section header
            if line.strip() and line.strip().isupper() and ':' in line:
                break
            voiceover_lines.append(line.strip())

    result = ' '.join(voiceover_lines).strip()
    return result


def generate_voiceover(text, output_filename="voiceover.mp3"):
    """Generates voiceover audio using ElevenLabs and saves it as an MP3."""
    if not elevenlabs_key:
        print("  [Voiceover] Error: ELEVENLABS_API_KEY missing in .env")
        return None

    if not text:
        print("  [Voiceover] Error: No voiceover text provided.")
        return None

    output_path = os.path.join(VOICEOVER_DIR, output_filename)
    print(f"  [Voiceover] Generating audio for: {text[:60]}...")

    try:
        # Generate audio using ElevenLabs
        # Using "Brian" voice - deep, dramatic, perfect for Shorts narration
        audio_generator = client.text_to_speech.convert(
            text=text,
            voice_id="nPczCjzI2devNBz1zQrb",  # Brian - deep dramatic male voice
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )

        # Write the audio chunks to file
        with open(output_path, 'wb') as f:
            for chunk in audio_generator:
                f.write(chunk)

        print(f"  [Voiceover] Audio saved: {output_path}")
        return output_path

    except Exception as e:
        print(f"  [Voiceover] ElevenLabs Error: {e}")
        return None
