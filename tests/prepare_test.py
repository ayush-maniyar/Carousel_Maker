import yt_dlp

def download_test_video(url):
    print("--- Downloading 360p Sample for Vision Test ---")
    ydl_opts = {
        # Using height<=360 keeps the file small (~10-20MB) and fast to scan
        'format': 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]',
        'outtmpl': 'temp_video.mp4',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    print("\nSuccess! temp_video.mp4 is now in D:\SWA")

if __name__ == "__main__":
    # Using the IBM lecture link as our test subject
    download_test_video("https://www.youtube.com/watch?v=qYNweeDHiyU")