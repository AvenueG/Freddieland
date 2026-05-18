import pytest
from unittest.mock import patch, MagicMock
from summarizer import summarize_audio_with_gemini

@patch('summarizer.genai')
@patch('summarizer.time.sleep')
def test_summarize_audio_with_gemini_success(mock_sleep, mock_genai):
    # Mock upload
    mock_file = MagicMock()
    mock_file.state.name = "ACTIVE"
    mock_file.name = "test_file_id"
    mock_genai.upload_file.return_value = mock_file

    # Mock generate content
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "This is a summary from Gemini."
    mock_model.generate_content.return_value = mock_response
    mock_genai.GenerativeModel.return_value = mock_model

    result = summarize_audio_with_gemini("test.mp3", "fake_key")

    mock_genai.configure.assert_called_once_with(api_key="fake_key")
    mock_genai.upload_file.assert_called_once_with(path="test.mp3")
    mock_genai.GenerativeModel.assert_called_once_with("gemini-1.5-flash")
    mock_model.generate_content.assert_called_once()
    mock_genai.delete_file.assert_called_once_with("test_file_id")

    assert result == "This is a summary from Gemini."

@patch('summarizer.genai')
@patch('summarizer.time.sleep')
def test_summarize_audio_with_gemini_processing_wait(mock_sleep, mock_genai):
    # Mock upload with PROCESSING state then ACTIVE
    mock_file_proc = MagicMock()
    mock_file_proc.state.name = "PROCESSING"
    mock_file_proc.name = "test_file_id"

    mock_file_active = MagicMock()
    mock_file_active.state.name = "ACTIVE"
    mock_file_active.name = "test_file_id"

    mock_genai.upload_file.return_value = mock_file_proc
    mock_genai.get_file.return_value = mock_file_active

    # Mock generate content
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Summary"
    mock_model.generate_content.return_value = mock_response
    mock_genai.GenerativeModel.return_value = mock_model

    result = summarize_audio_with_gemini("test.mp3", "fake_key")

    mock_genai.get_file.assert_called_once_with("test_file_id")
    assert result == "Summary"

@patch('summarizer.genai')
@patch('summarizer.time.sleep')
def test_summarize_audio_with_gemini_failure_state(mock_sleep, mock_genai):
    mock_file = MagicMock()
    mock_file.state.name = "FAILED"
    mock_genai.upload_file.return_value = mock_file

    result = summarize_audio_with_gemini("test.mp3", "fake_key")

    assert result is None

@patch('summarizer.genai')
def test_summarize_audio_with_gemini_exception(mock_genai):
    mock_genai.configure.side_effect = Exception("API error")

    result = summarize_audio_with_gemini("test.mp3", "fake_key")

    assert result is None
