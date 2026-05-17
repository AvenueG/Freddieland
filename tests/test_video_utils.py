import pytest
from unittest.mock import patch, MagicMock
from video_utils import download_youtube_video, extract_audio_from_video

@patch('video_utils.yt_dlp.YoutubeDL')
def test_download_youtube_video_success(mock_ydl_class):
    mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value

    url = "http://test.com"
    output = "test.mp4"
    result = download_youtube_video(url, output)

    mock_ydl_instance.download.assert_called_once_with([url])
    assert result == output

@patch('video_utils.yt_dlp.YoutubeDL')
def test_download_youtube_video_failure(mock_ydl_class):
    mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
    mock_ydl_instance.download.side_effect = Exception("Download failed")

    url = "http://test.com"
    output = "test.mp4"
    result = download_youtube_video(url, output)

    assert result is None

@patch('video_utils.VideoFileClip')
def test_extract_audio_from_video_success(mock_video_file_clip):
    mock_clip_instance = mock_video_file_clip.return_value
    mock_audio = MagicMock()
    mock_clip_instance.audio = mock_audio

    video_path = "test.mp4"
    audio_path = "test.mp3"
    result = extract_audio_from_video(video_path, audio_path)

    mock_audio.write_audiofile.assert_called_once_with(audio_path, logger=None)
    mock_audio.close.assert_called_once()
    mock_clip_instance.close.assert_called_once()
    assert result == audio_path

@patch('video_utils.VideoFileClip')
def test_extract_audio_from_video_failure(mock_video_file_clip):
    mock_video_file_clip.side_effect = Exception("Extraction failed")

    video_path = "test.mp4"
    audio_path = "test.mp3"
    result = extract_audio_from_video(video_path, audio_path)

    assert result is None
