import os
import yt_dlp

def download_youtube_audio(url, output_path):
    """
    Downloads a YouTube video's audio directly.
    """
    # yt-dlp doesn't automatically add the extension unless specified,
    # but we are providing output_path which should include it.
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return output_path
    except Exception as e:
        print(f"Error downloading audio: {e}")
        return None
