"""
Editor Agent
Handles video processing: cropping to 9:16 portrait, overlaying voiceover audio,
and merging multiple video clips.
"""
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips


def convert_to_portrait(input_path, output_path):
    """Center-crops any video to 9:16 portrait aspect ratio without rotation."""
    print(f"  [Editor] Loading: {input_path}")
    clip = VideoFileClip(input_path)
    w, h = clip.size
    print(f"  [Editor] Original: {w}x{h}")

    target_ratio = 9 / 16

    if w / h > target_ratio:
        new_w = int(h * target_ratio)
        new_h = h
    else:
        new_w = w
        new_h = int(w / target_ratio)

    x1 = int((w - new_w) / 2)
    y1 = int((h - new_h) / 2)

    print(f"  [Editor] Cropping to {new_w}x{new_h} (9:16)")
    cropped = clip.cropped(x1=x1, y1=y1, x2=x1 + new_w, y2=y1 + new_h)
    cropped.write_videofile(output_path, codec='libx264', audio_codec='aac', logger='bar')
    clip.close()
    cropped.close()
    print(f"  [Editor] Portrait saved: {output_path}")
    return output_path


def overlay_voiceover(video_path, voiceover_path, output_path):
    """Overlays voiceover audio on top of the video's original audio (mixed)."""
    print(f"  [Editor] Overlaying voiceover onto video...")
    
    video = VideoFileClip(video_path)
    voiceover = AudioFileClip(voiceover_path)
    
    # If voiceover is longer than video, trim it. If shorter, that's fine.
    if voiceover.duration > video.duration:
        voiceover = voiceover.with_subclip(0, video.duration)
    
    # Mix original video audio (lowered) with voiceover
    if video.audio is not None:
        # Lower original audio to 20% so voiceover is dominant
        original_audio = video.audio.with_effects([lambda get_frame, t: get_frame(t) * 0.2])
        mixed = CompositeAudioClip([original_audio, voiceover])
    else:
        mixed = voiceover
    
    final = video.with_audio(mixed)
    final.write_videofile(output_path, codec='libx264', audio_codec='aac', logger='bar')
    
    video.close()
    voiceover.close()
    final.close()
    print(f"  [Editor] Final video with voiceover saved: {output_path}")
    return output_path


def merge_videos(video_paths, output_path):
    """Merges multiple video files into a single video, played sequentially."""
    print(f"  [Editor] Merging {len(video_paths)} videos...")
    for i, vp in enumerate(video_paths, 1):
        print(f"    {i}. {vp}")

    clips = []
    try:
        for vp in video_paths:
            clips.append(VideoFileClip(vp))

        merged = concatenate_videoclips(clips, method="compose")
        merged.write_videofile(output_path, codec='libx264', audio_codec='aac', logger='bar')
        merged.close()

        print(f"  [Editor] Merged video saved: {output_path}")
        return output_path

    except Exception as e:
        print(f"  [Editor] Merge Error: {e}")
        return None
    finally:
        for c in clips:
            c.close()
