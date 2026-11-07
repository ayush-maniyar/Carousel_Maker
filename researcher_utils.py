import os
import re
import whisper
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        print("🌀 Loading Whisper (base) model on GPU...")
        _whisper_model = whisper.load_model("base")
    return _whisper_model

def extract_video_id(url: str) -> str:
    patterns = [r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', r'youtu\.be\/([0-9A-Za-z_-]{11})']
    for pattern in patterns:
        match = re.search(pattern, url)
        if match: return match.group(1)
    return url.strip()

def researcher_pipeline(video_url: str, persona: str):
    video_id = extract_video_id(video_url)
    transcript = ""

    try:
        print(f"📡 Attempting Fast Transcript pull for ID: {video_id}")
        raw_data = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([entry['text'] for entry in raw_data])
        print("✅ Fast transcript retrieved successfully.")
    except Exception as e:
        print(f"⚠️ Fast pull failed. Falling back to Whisper GPU...")
        
        try:
            print("--- Downloading Audio for Whisper ---")
            ydl_opts = {
                'format': 'm4a/bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'wav'}],
                'outtmpl': 'temp_audio.%(ext)s',
                'quiet': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            model = get_whisper_model()
            result = model.transcribe("temp_audio.wav")
            transcript = result.get("text", "")
            print("✅ Whisper transcription complete.")
            
            if os.path.exists("temp_audio.wav"):
                os.remove("temp_audio.wav")
                
        except Exception as whisper_err:
            print(f"❌ Whisper fallback error: {str(whisper_err)}")
            transcript = f"Transcript unavailable for {video_url}."

    transcript_path = "transcript.txt"
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(transcript)

    return transcript_path, []
