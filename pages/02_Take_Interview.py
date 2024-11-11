import streamlit as st
import sounddevice as sd
import soundfile as sf
import numpy as np
import scipy.io.wavfile as wav
import openai
from langchain_openai import ChatOpenAI
import os
import io
import time
import soundfile as sf
from openai import OpenAI

client = OpenAI()

# Set OpenAI API key
os.environ["OPENAI_API_KEY"] = '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'

# Session state variables to control recording status
if "recording" not in st.session_state:
    st.session_state.recording = False
if "audio_data" not in st.session_state:
    st.session_state.audio_data = None
if "responses" not in st.session_state:
    st.session_state.responses = []

# Function to record audio using sounddevice
def start_recording(file_path, duration=10, fs=44100, device_index=0):
    st.session_state.recording = True
    st.write(f"Recording Started....Duration is {duration} secs.")
    audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16', device=device_index)
    sd.wait()  # Wait until the recording is finished
    st.session_state.recording = False
    sf.write(file_path, audio_data, fs)
    st.write(f"Recording complete. File saved at {file_path}")

    # Convert to BytesIO object in WAV format
    audio_buffer = io.BytesIO()
    wav.write(audio_buffer, fs, audio_data)
    audio_buffer.seek(0)  # Ensure the buffer starts at the beginning
    st.session_state.audio_data = audio_buffer

# Function to transcribe audio using OpenAI's Whisper API
# Function to transcribe audio using OpenAI's Whisper API
def transcribe_audio(file_path):
    with open(file_path, 'rb') as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )

    # Print transcription to verify the format
    st.write("Transcription response:", transcription)

    # Check if transcription is a string or dictionary
    if isinstance(transcription, dict) and 'text' in transcription:
        return transcription['text']
    elif isinstance(transcription, str):
        return transcription  # Return the string if it's already in text format
    else:
        return "Error: Unexpected response format."

# Function to generate questions based on insights and job description
def generate_questions(insights, jd_text):
    prompt = f"""
    Based on the following candidate insights and job description, generate 3 interview questions:

    Candidate Insights:
    {insights}

    Job Description:
    {jd_text}

    Output the questions in a list format.
    """
    chat_model = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
    response = chat_model.generate([prompt])
    questions = response.generations[0][0].text.strip().split('\n')
    return questions

# Function to analyze the transcribed response
def analyze_response(transcript):
    prompt = f"""
    Evaluate the following answer for its relevance, clarity, and technical depth in the context of an AI engineering interview question.

    Candidate's Response: {transcript}

    Provide analysis in short bullet points: 
    - Relevance
    - Clarity
    - Technical depth
    """
    chat_model = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
    response = chat_model.generate([prompt])
    analysis = response.generations[0][0].text.strip()
    return analysis

st.title("Interview Preparation")

# Display candidate insights and job description
if "insights" in st.session_state and "jd_text" in st.session_state:
    st.write("### Candidate Insights")
    st.write(st.session_state.insights)

    st.write("### Job Description")
    st.write(st.session_state.jd_text)

    # Generate interview questions
    if "questions" not in st.session_state:
        st.session_state.questions = generate_questions(st.session_state.insights, st.session_state.jd_text)

    st.write("### Interview Questions")
    responses = []
    for i, question in enumerate(st.session_state.questions, 1):
        st.write(f"**Question {i}:** {question}")

        # Record or input text response
        col1, col2 = st.columns(2)
        with col1:
            file_path = f"recording_question_{i}.wav"
            # Start and Stop buttons for recording
            if st.button(f"Start Answer for Question {i}"):
                st.write(f"Starting to record for Question {i}...")
                start_recording(file_path=file_path, duration=10)

            if st.button(f"Analyze Answer for Question {i}") and st.session_state.audio_data:
                transcript = transcribe_audio(file_path)

                # Display the transcribed response
                st.write("### Transcription of Your Response")
                st.write(transcript)

                # Analyze the transcribed response
                analysis = analyze_response(transcript)
                st.write("### Analysis of Your Response")
                st.write(analysis)
                responses.append((transcript, analysis))

        with col2:
            text_response = st.text_area(f"Or type your answer for Question {i}")
            if text_response:
                st.write("### Analysis of Your Response")
                analysis = analyze_response(text_response)
                st.write(analysis)
                responses.append((text_response, analysis))

    # Save responses for interviewer insights
    st.session_state.responses = responses

# Submit interview and generate final interviewer insights
if st.button("Submit Interview"):
    insights_summary = "\n".join([response[1] for response in st.session_state.responses if response[1]])
    prompt = f"""
    Based on the following interview responses and analyses, provide a final summary for the interviewer:

    Interview Responses and Analyses:
    {insights_summary}

    Generate a concise structured summary in bullet points:
    - Overall performance
    - Strengths
    - Areas for improvement
    """
    chat_model = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
    response = chat_model.generate([prompt])
    final_insights = response.generations[0][0].text.strip()

    st.write("### Interviewer's Summary and Insights")
    st.write(final_insights)
