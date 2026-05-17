import pytest
from unittest.mock import patch, MagicMock
from google_docs import authenticate_google_docs, create_google_doc, insert_text_to_doc

@patch('google_docs.os.path.exists')
@patch('google_docs.Credentials.from_authorized_user_file')
@patch('google_docs.build')
def test_authenticate_google_docs_with_token(mock_build, mock_credentials, mock_exists):
    mock_exists.return_value = True
    mock_creds = MagicMock()
    mock_creds.valid = True
    mock_credentials.return_value = mock_creds

    mock_service = MagicMock()
    mock_build.return_value = mock_service

    result = authenticate_google_docs("creds.json")

    assert result == mock_service
    mock_build.assert_called_once_with('docs', 'v1', credentials=mock_creds)

def test_create_google_doc_success():
    mock_service = MagicMock()
    mock_execute = mock_service.documents.return_value.create.return_value.execute
    mock_execute.return_value = {'documentId': '12345'}

    result = create_google_doc("Test Doc", mock_service)

    assert result == '12345'
    mock_service.documents().create.assert_called_once()

def test_create_google_doc_failure():
    mock_service = MagicMock()
    mock_service.documents().create.side_effect = Exception("API error")

    result = create_google_doc("Test Doc", mock_service)

    assert result is None

def test_insert_text_to_doc_success():
    mock_service = MagicMock()
    mock_execute = mock_service.documents.return_value.batchUpdate.return_value.execute
    mock_execute.return_value = {'replies': []}

    result = insert_text_to_doc("12345", "test text", mock_service)

    assert result is not None
    mock_service.documents().batchUpdate.assert_called_once()

def test_insert_text_to_doc_failure():
    mock_service = MagicMock()
    mock_service.documents().batchUpdate.side_effect = Exception("API error")

    result = insert_text_to_doc("12345", "test text", mock_service)

    assert result is None
