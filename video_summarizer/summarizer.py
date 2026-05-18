import google.generativeai as genai
import time

def summarize_audio_with_gemini(audio_path, api_key):
    """
    Uploads audio to Gemini API and asks it to transcribe and summarize it.
    """
    try:
        genai.configure(api_key=api_key)

        # Upload the file to Gemini
        uploaded_file = genai.upload_file(path=audio_path)

        # Wait until the file is active (some processing might happen on the backend)
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(2)
            uploaded_file = genai.get_file(uploaded_file.name)

        if uploaded_file.state.name == "FAILED":
            print(f"Error: File processing failed.")
            return None

        # Choose a Gemini model that supports multi-modal (audio)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = "Please transcribe and summarize the following audio comprehensively, highlighting the key points, main themes, and actionable takeaways."

        response = model.generate_content([prompt, uploaded_file])

        # Clean up the file from Gemini servers
        genai.delete_file(uploaded_file.name)

        return response.text

    except Exception as e:
        print(f"Error summarizing audio with Gemini: {e}")
        return None
