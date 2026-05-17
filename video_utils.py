import os
import yt_dlp
from moviepy import VideoFileClip

def download_youtube_video(url, output_path):
    """
    Downloads a YouTube video to the specified output path.
    """
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return output_path
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None

def extract_audio_from_video(video_path, audio_path):
    """
    Extracts audio from a video file and saves it to the specified path.
    """
    try:
        video_clip = VideoFileClip(video_path)
        audio_clip = video_clip.audio
        audio_clip.write_audiofile(audio_path, logger=None)

        # Close the clips to release resources
        audio_clip.close()
        video_clip.close()

        return audio_path
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return None
