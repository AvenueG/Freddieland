# Video Summarizer to Google Docs

This application downloads a YouTube or Bilibili video's audio, transcribes and summarizes the audio using Google's Gemini 1.5 Flash model, and directly saves the generated summary as a new document in your Google Docs.

## Prerequisites

To run this application, you need:

1.  **Python 3.8+**
2.  **FFmpeg**: Ensure `ffmpeg` is installed on your system.
3.  **Google Gemini API Key**: Obtain an API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
3.  **Google Cloud Platform Account**: You need to set up a project and obtain OAuth 2.0 Client IDs.
    *   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    *   Enable the **Google Docs API**.
    *   Create an OAuth 2.0 Client ID (Desktop App).
    *   Download the JSON file and rename it to `credentials.json`. Place it in the root directory of this project.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```

2.  **Install dependencies:**
    It is recommended to use a virtual environment.
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

1.  Ensure you have your `credentials.json` file in the root directory.
2.  Start the Streamlit app:
    ```bash
    streamlit run app.py
    ```
3.  Open the provided local URL in your web browser.
4.  In the sidebar, enter your **Google Gemini API Key** and the path to your `credentials.json` (defaults to `credentials.json`).
5.  Enter the **Video URL** (YouTube or Bilibili) and the desired **Document Title**.
6.  Click **Generate Summary**. The application will process the video and provide a link to your newly created Google Document.

*Note: The first time you run the application and connect to Google Docs, a browser window will open asking you to grant permissions to the app. Once granted, a `token.json` file will be created locally to store your access tokens.*
