import pytest
from unittest.mock import patch
from video_utils import download_youtube_audio

@patch('video_utils.yt_dlp.YoutubeDL')
def test_download_youtube_audio_success(mock_ydl_class):
    mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value

    url = "http://test.com"
    output = "test.mp3"
    result = download_youtube_audio(url, output)

    mock_ydl_instance.download.assert_called_once_with([url])
    assert result == output

@patch('video_utils.yt_dlp.YoutubeDL')
def test_download_youtube_audio_failure(mock_ydl_class):
    mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
    mock_ydl_instance.download.side_effect = Exception("Download failed")

    url = "http://test.com"
    output = "test.mp3"
    result = download_youtube_audio(url, output)

    assert result is None
