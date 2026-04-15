"""
LUMORA - AI Content Pipeline
Generates viral scripts, watches for your Veo 3.1 video(s),
optionally merges multiple clips, adds AI voiceover, crops to portrait,
and auto-uploads to YouTube Shorts.

Usage: .\\venv\\Scripts\\python.exe main.py
"""
import os
import sys
import time
import glob

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from agents.scriptwriter import generate_script
from agents.voiceover import extract_voiceover_text, generate_voiceover
from agents.editor import convert_to_portrait, overlay_voiceover, merge_videos
from agents.metadata import generate_metadata
from agents.uploader import get_authenticated_service, upload_video

UPLOADS_DIR = "uploads"
CLIPS_DIR = "clips"


def ask_yes_no(prompt):
    """Ask a yes/no question and return True for yes, False for no."""
    while True:
        answer = input(f"\n  {prompt} (y/n): ").strip().lower()
        if answer in ('y', 'yes'):
            return True
        if answer in ('n', 'no'):
            return False
        print("  Please enter 'y' or 'n'.")


def wait_for_videos(count):
    """Watch uploads folder for exactly `count` new .mp4 files. Returns list of paths."""
    existing_files = set(glob.glob(os.path.join(UPLOADS_DIR, '*.mp4')))
    collected = []

    print(f"\n  Watching for {count} new .mp4 file(s)...")
    print(f"  Drop them into: {os.path.abspath(UPLOADS_DIR)}\n")

    while len(collected) < count:
        current_files = set(glob.glob(os.path.join(UPLOADS_DIR, '*.mp4')))
        new_files = current_files - existing_files
        for nf in sorted(new_files):
            if nf not in collected:
                collected.append(nf)
                print(f"  [{len(collected)}/{count}] Detected: {os.path.basename(nf)}")
                existing_files.add(nf)
        time.sleep(2)

    # Give last file time to finish copying
    time.sleep(2)
    return collected


def select_videos_to_merge(video_list):
    """Let user explicitly pick which videos to merge and in what order.
    Returns the ordered list of selected videos, or None if user cancels merge."""

    print("\n  Videos detected:")
    for i, v in enumerate(video_list, 1):
        print(f"    [{i}] {os.path.basename(v)}")

    print("\n  Enter the numbers of videos to merge, in the order you want them.")
    print("  Example: '1 3 2' merges video 1, then 3, then 2.")
    print("  Or type 'cancel' to skip merging and process only the first video.\n")

    while True:
        choice = input("  Your selection: ").strip().lower()

        if choice == 'cancel':
            return None

        try:
            indices = [int(x) for x in choice.split()]
            if not indices:
                print("  Please enter at least one number.")
                continue
            if any(i < 1 or i > len(video_list) for i in indices):
                print(f"  Numbers must be between 1 and {len(video_list)}.")
                continue

            selected = [video_list[i - 1] for i in indices]

            # Confirm selection
            print("\n  You selected this merge order:")
            for i, v in enumerate(selected, 1):
                print(f"    {i}. {os.path.basename(v)}")

            if ask_yes_no("Confirm merge with this order?"):
                return selected
            else:
                print("  Let's try again.")

        except ValueError:
            print("  Invalid input. Enter numbers separated by spaces, e.g. '1 2 3'")


def main():
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(CLIPS_DIR, exist_ok=True)

    print("\n" + "=" * 50)
    print("   LUMORA - AI Content Pipeline")
    print("=" * 50)

    # ── Step 1: Generate Script ──
    print("\n" + "=" * 50)
    print("  STEP 1: GENERATING VIRAL VIDEO SCRIPT")
    print("=" * 50)

    script_text, script_path = generate_script()
    if not script_text:
        print("Failed to generate script. Exiting.")
        return

    print("\n" + script_text)
    print(f"\nScript saved to: {script_path}")

    # ── Step 2: Voiceover Toggle ──
    print("\n" + "=" * 50)
    print("  STEP 2: VOICEOVER OPTIONS")
    print("=" * 50)

    voiceover_path = None
    want_voiceover = ask_yes_no("Do you want AI voiceover on this video?")

    if want_voiceover:
        voiceover_text = extract_voiceover_text(script_text)
        if voiceover_text:
            print(f"  Voiceover text: {voiceover_text[:80]}...")
            timestamp = int(time.time())
            voiceover_path = generate_voiceover(voiceover_text, f"vo_{timestamp}.mp3")
        else:
            print("  No VOICEOVER SCRIPT found in generated script. Skipping voiceover.")
    else:
        print("  Voiceover skipped by user choice.")

    # ── Step 3: Video Drop + Optional Merge ──
    print("\n" + "=" * 50)
    print("  STEP 3: VIDEO INPUT OPTIONS")
    print("=" * 50)

    want_merge = ask_yes_no("Do you want to merge multiple video clips?")

    if want_merge:
        while True:
            try:
                vid_count = int(input("\n  How many videos will you drop? ").strip())
                if vid_count < 2:
                    print("  Need at least 2 videos to merge. Enter 2 or more.")
                    continue
                break
            except ValueError:
                print("  Please enter a number.")

        print(f"\n  Waiting for {vid_count} videos...")
        video_list = wait_for_videos(vid_count)

        # Let user pick exactly which ones to merge & in what order
        merge_selection = select_videos_to_merge(video_list)

        if merge_selection and len(merge_selection) >= 2:
            timestamp = int(time.time())
            merged_path = os.path.join(CLIPS_DIR, f'merged_{timestamp}.mp4')
            result = merge_videos(merge_selection, merged_path)

            if result:
                new_video = result
            else:
                print("  Merge failed. Falling back to first video.")
                new_video = video_list[0]
        else:
            print("  Merge cancelled. Using first detected video.")
            new_video = video_list[0]
    else:
        # Single video mode
        print(f"\n  Place your finished .mp4 into:")
        print(f"  --> {os.path.abspath(UPLOADS_DIR)}")

        video_list = wait_for_videos(1)
        new_video = video_list[0]

    print(f"\n  Working with video: {os.path.basename(new_video)}")

    # ── Step 4: Crop to Portrait ──
    print("\n" + "=" * 50)
    print("  STEP 4: CONVERTING TO 9:16 PORTRAIT")
    print("=" * 50)

    base_name = os.path.splitext(os.path.basename(new_video))[0]
    portrait_path = os.path.join(CLIPS_DIR, f'{base_name}_portrait.mp4')
    convert_to_portrait(new_video, portrait_path)

    # ── Step 5: Overlay Voiceover ──
    final_video_path = portrait_path

    if voiceover_path and os.path.exists(voiceover_path):
        print("\n" + "=" * 50)
        print("  STEP 5: ADDING VOICEOVER TO VIDEO")
        print("=" * 50)

        final_path = os.path.join(CLIPS_DIR, f'{base_name}_final.mp4')
        final_video_path = overlay_voiceover(portrait_path, voiceover_path, final_path)
    else:
        print("\n  Skipping voiceover overlay (no audio generated).")

    # ── Step 6: Generate Metadata ──
    print("\n" + "=" * 50)
    print("  STEP 6: GENERATING VIRAL METADATA")
    print("=" * 50)

    topic_hint = "viral short form video content"
    if script_text:
        for line in script_text.split('\n'):
            if line.strip().startswith('TOPIC:'):
                topic_hint = line.replace('TOPIC:', '').strip()
                break

    metadata = generate_metadata(topic_hint)
    print(f"  Title: {metadata['title']}")

    # ── Step 7: Upload to YouTube Shorts ──
    print("\n" + "=" * 50)
    print("  STEP 7: UPLOADING TO YOUTUBE SHORTS")
    print("=" * 50)

    youtube = get_authenticated_service()
    video_id = upload_video(
        youtube,
        final_video_path,
        metadata['title'],
        metadata['description'],
        metadata.get('tags', ['shorts', 'viral']),
        privacy_status='public'
    )

    if video_id:
        print(f"\n{'=' * 50}")
        print(f"  VIDEO IS LIVE ON YOUTUBE SHORTS!")
        print(f"  https://youtu.be/{video_id}")
        print(f"{'=' * 50}")
        print(f"\n  Run again anytime: .\\venv\\Scripts\\python.exe main.py")


if __name__ == "__main__":
    main()
