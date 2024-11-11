import streamlit as st
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tempfile
from langchain_openai import ChatOpenAI
import os
import openai

# Set OpenAI API key
os.environ["OPENAI_API_KEY"] = 'your-api-key-here'

# Function to capture audio input from user
def record_audio(duration=30, fs=44100):
    st.write(f"Recording... you have {duration} seconds.")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    return np.squeeze(recording), fs

# Function to save audio as .wav file
def save_audio(audio, fs, filename="user_audio.wav"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        wav.write(temp_file.name, fs, audio)
        return temp_file.name

# Function to transcribe audio using OpenAI's Whisper API
def transcribe_audio(audio_path):
    with open(audio_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
    return transcript["text"]

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
            if st.button(f"Record Answer for Question {i}"):
                audio, fs = record_audio(duration=30)
                audio_path = save_audio(audio, fs, f"user_audio_q{i}.wav")
                st.session_state[f"audio_path_q{i}"] = audio_path
                st.write(f"Recording for Question {i} saved.")
                st.audio(audio_path, format="audio/wav")

                # Transcribe and analyze if audio exists
                transcript = transcribe_audio(audio_path)
                st.write("### Transcription of Your Response")
                st.write(transcript)
                analysis = analyze_response(transcript)
                st.write("### Analysis of Your Response")
                st.write(analysis)
                responses.append((transcript, analysis, audio_path))

        with col2:
            text_response = st.text_area(f"Or type your answer for Question {i}")
            if text_response:
                st.write("### Analysis of Your Response")
                analysis = analyze_response(text_response)
                st.write(analysis)
                responses.append((text_response, analysis, None))

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

    # Save audio files for record-keeping
    for idx, (transcript, analysis, audio_path) in enumerate(st.session_state.responses):
        if audio_path:
            st.write(f"Audio saved for Question {idx + 1}: {audio_path}")
