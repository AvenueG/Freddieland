import streamlit as st
import os
import uuid
from video_utils import download_youtube_audio
from summarizer import summarize_audio_with_gemini
from google_docs import authenticate_google_docs, create_google_doc, insert_text_to_doc

st.set_page_config(page_title="Video Summarizer to Google Docs", page_icon="📝")

st.title("🎥 Video Summarizer to Google Docs")
st.write("Convert any YouTube video into a comprehensive summary using Google Gemini and save it directly to your Google Docs.")

with st.sidebar:
    st.header("⚙️ Configuration")
    gemini_api_key = st.text_input("Gemini API Key", type="password")
    google_creds_path = st.text_input("Google Credentials Path", value="credentials.json")

    st.markdown("---")
    st.markdown("""
    ### How to use:
    1. Enter your Google Gemini API key.
    2. Ensure your Google `credentials.json` is in the specified path.
    3. Paste a YouTube URL.
    4. Click 'Generate Summary'.
    """)

youtube_url = st.text_input("YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")
doc_title = st.text_input("Document Title", value="Video Summary")

if st.button("Generate Summary", type="primary"):
    if not youtube_url:
        st.error("Please enter a YouTube URL.")
    elif not gemini_api_key:
        st.error("Please enter your Gemini API Key in the sidebar.")
    elif not os.path.exists(google_creds_path):
        st.error(f"Google credentials file not found at '{google_creds_path}'. Please check the path.")
    else:
        with st.status("Processing video...", expanded=True) as status:
            temp_id = str(uuid.uuid4())
            audio_path = f"temp_audio_{temp_id}.mp3"

            try:
                # Step 1: Download Audio
                st.write("📥 Downloading audio...")
                downloaded_audio = download_youtube_audio(youtube_url, audio_path)
                if not downloaded_audio:
                    st.error("Failed to download audio.")
                    st.stop()

                # Step 2: Summarize with Gemini
                st.write("🧠 Generating summary using Gemini...")
                summary = summarize_audio_with_gemini(audio_path, gemini_api_key)
                if not summary:
                    st.error("Failed to generate summary.")
                    st.stop()

                # Step 3: Save to Google Docs
                st.write("📄 Saving to Google Docs...")
                docs_service = authenticate_google_docs(google_creds_path)
                if not docs_service:
                    st.error("Failed to authenticate with Google Docs.")
                    st.stop()

                doc_id = create_google_doc(doc_title, docs_service)
                if not doc_id:
                    st.error("Failed to create Google Document.")
                    st.stop()

                insert_result = insert_text_to_doc(doc_id, summary, docs_service)
                if not insert_result:
                    st.error("Failed to insert text into Google Document.")
                    st.stop()

                status.update(label="Summary generated and saved successfully!", state="complete", expanded=False)

                doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
                st.success(f"Successfully created summary!")
                st.markdown(f"[**Open Google Document**]({doc_url})")

                with st.expander("View Summary"):
                    st.write(summary)

            except Exception as e:
                status.update(label="An error occurred.", state="error", expanded=False)
                st.error(f"An error occurred: {e}")
            finally:
                # Cleanup temporary files
                if os.path.exists(audio_path):
                    os.remove(audio_path)
