import streamlit as st
from dotenv import load_dotenv
import os
from moviepy.editor import VideoFileClip,AudioFileClip,CompositeVideoClip
import requests
import assemblyai as aai
from gtts import gTTS

load_dotenv()

apiKey=os.getenv('apiKey')
endpoint=os.getenv('endpointUrl')
aaiKey = os.getenv('assembly')


if apiKey and endpoint and aaiKey:
    aai.settings.api_key=aaiKey
    transcriber = aai.Transcriber()

    st.title('Audio Correction')
    st.header('Fixes broken audios in videos')

    video = st.file_uploader('Your video file',['mp4','mkv'],False,'video')    

    if video is not None:
        st.title('Preview')
        st.video(video)

        video = VideoFileClip(video.name)
        audio_path = "temp_audio.wav"  # Temporary audio file

        # Save the audio as WAV to a temporary file
        video.audio.write_audiofile(audio_path, codec='pcm_s16le')

        # Play the audio in Streamlit
        st.write('Extracted Audio')
        st.audio(audio_path, format="audio/wav")

        st.success("Audio extracted and playing successfully!")

        st.info('Transcribing in process...')
        transcript = transcriber.transcribe(audio_path)
        # Cleanup: Remove the temporary audio file

        if transcript and transcript.status!=aai.TranscriptStatus.error:
            os.remove(audio_path)
            transcript=transcript.text
            st.success('Speech to Text transcription Successfull')
            headers = {
                "Content-Type": "application/json",  # Specifies that we are sending JSON data
                "api-key": apiKey  # The API key for authentication
            }
            
            # Data to be sent to Azure OpenAI
            # Define the payload, which includes the message prompt and token limit.
            # **** This is where you can customize the message prompt and token limit. ****
            data = {
                "messages": [{"role": "user", "content": f"Fine tune this speech to remove unnecessary sound and fillers\n{transcript} and only return the transcription"}],  # The message we want the model to respond to
                "max_tokens": len(transcript)  # Limit the response length
            }

            try:
                response = requests.post(endpoint, headers=headers, json=data)
                if response.status_code == 200:
                    result = response.json()  # Parse the JSON response
                    st.success('Successfully received refined speech')
                    content=result["choices"][0]["message"]["content"].strip()
                    tts=gTTS(content,lang='en')
                    tts_audio_path = 'tts_audio.mp3'
                    tts.save(tts_audio_path)

                    tts_audio = AudioFileClip(tts_audio_path)
                    finalvid = video.set_audio(tts_audio)
                    final='final_video.mp4'
                    finalvid.write_videofile(final,codec='libx264')
                    st.success('Final video created successfully!')
                    st.video(final)

                    os.remove(tts_audio_path)
                    os.remove(final)
                else:
                    # Handle errors if the request was not successful
                    st.error(f"Failed to connect or retrieve response: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Failed to connect or retrieve response: {str(e)}")
        else:
            st.error('Error' or transcript.error)