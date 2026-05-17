import pytest
from unittest.mock import patch, mock_open, MagicMock
from summarizer import transcribe_audio, summarize_text

@patch('summarizer.OpenAI')
@patch('builtins.open', new_callable=mock_open, read_data=b"dummy audio")
def test_transcribe_audio_success(mock_file, mock_openai_class):
    mock_client = mock_openai_class.return_value
    mock_transcriptions = mock_client.audio.transcriptions
    mock_response = MagicMock()
    mock_response.text = "This is a transcript."
    mock_transcriptions.create.return_value = mock_response

    result = transcribe_audio("test.mp3", "fake_key")

    mock_transcriptions.create.assert_called_once()
    assert result == "This is a transcript."

@patch('summarizer.OpenAI')
def test_transcribe_audio_failure(mock_openai_class):
    mock_openai_class.side_effect = Exception("API error")

    result = transcribe_audio("test.mp3", "fake_key")

    assert result is None

@patch('summarizer.OpenAI')
def test_summarize_text_success(mock_openai_class):
    mock_client = mock_openai_class.return_value
    mock_completions = mock_client.chat.completions
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="This is a summary."))]
    mock_completions.create.return_value = mock_response

    result = summarize_text("transcript text", "fake_key")

    mock_completions.create.assert_called_once()
    assert result == "This is a summary."

@patch('summarizer.OpenAI')
def test_summarize_text_failure(mock_openai_class):
    mock_openai_class.side_effect = Exception("API error")

    result = summarize_text("transcript text", "fake_key")

    assert result is None
