import os
from openai import OpenAI

def transcribe_audio(audio_path, api_key):
    """
    Transcribes audio using OpenAI's Whisper model.
    """
    try:
        client = OpenAI(api_key=api_key)

        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

        return transcript.text
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None

def summarize_text(text, api_key):
    """
    Summarizes the provided text using OpenAI's GPT-4o model.
    """
    try:
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a highly skilled AI trained in summarizing video transcripts into well-structured, easy-to-read, and comprehensive notes."},
                {"role": "user", "content": f"Please summarize the following text comprehensively, highlighting the key points, main themes, and actionable takeaways:\n\n{text}"}
            ]
        )

        return response.choices[0].message.content
    except Exception as e:
        print(f"Error summarizing text: {e}")
        return None
