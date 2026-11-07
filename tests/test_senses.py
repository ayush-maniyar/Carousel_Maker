import yt_dlp
import whisper
import os

def test_pipeline(url):
    try:
        # 1. DOWNLOAD AUDIO
        print("--- Phase 1: Downloading Audio ---")
        ydl_opts = {
            'format': 'm4a/bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'outtmpl': 'sample_audio.%(ext)s',
            'quiet': False,
            # Add these two lines below to mimic a real browser
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.youtube.com/',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("Contacting YouTube...")
            ydl.download([url])
        print("Audio download complete!")

        # 2. TRANSCRIBE ON GPU
        if not os.path.exists("sample_audio.wav"):
            print("Error: Audio file was not created!")
            return

        print("\n--- Phase 2: Loading Whisper on RTX 3050 ---")
        # download_root saves the model in your project folder so you can see it
        model = whisper.load_model("base", device="cuda", download_root="./models")
        
        print("Starting Transcription (this may take a minute)...")
        result = model.transcribe("sample_audio.wav", verbose=True) # verbose=True shows text as it is generated
        
        print("\n--- Final Result ---")
        print(result["text"][:500] + "...") 
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Ensure the URL is a string inside quotes!
    video_url = "https://youtu.be/qYNweeDHiyU?si=cT5jcaP4c9vKB6tG" 
    test_pipeline(video_url)