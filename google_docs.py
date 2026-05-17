import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/documents']

def authenticate_google_docs(credentials_path):
    """
    Authenticates with Google Docs API and returns the service.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                print(f"Credentials file not found at {credentials_path}")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('docs', 'v1', credentials=creds)
        return service
    except Exception as e:
        print(f"Error building service: {e}")
        return None


def create_google_doc(title, service):
    """
    Creates a new Google Document and returns its ID.
    """
    try:
        document = service.documents().create(body={'title': title}).execute()
        return document.get('documentId')
    except Exception as e:
        print(f"Error creating document: {e}")
        return None


def insert_text_to_doc(document_id, text, service):
    """
    Inserts text into a Google Document.
    """
    try:
        requests = [
            {
                'insertText': {
                    'location': {
                        'index': 1,
                    },
                    'text': text
                }
            }
        ]

        result = service.documents().batchUpdate(
            documentId=document_id, body={'requests': requests}).execute()
        return result
    except Exception as e:
        print(f"Error inserting text: {e}")
        return None
