import streamlit as st
import openai
from langchain_openai import ChatOpenAI
import os
import io
import datetime
from audio_recorder_streamlit import audio_recorder

# Set OpenAI API key
os.environ["OPENAI_API_KEY"] = 'OPENAI_API_KEY'

client = openai.OpenAI()

# Initialize session state variables
if "responses" not in st.session_state:
    st.session_state.responses = []
if "questions" not in st.session_state:
    st.session_state.questions = []
if "insights" not in st.session_state:
    st.session_state.insights = "Candidate insights text here."
if "jd_text" not in st.session_state:
    st.session_state.jd_text = "Job description text here."

# Function to generate questions based on insights and job description
def generate_questions(insights, jd_text):
    prompt = f"""
    Act as an expert in AI/ML and software engineering and Based on the following candidate insights and job description, generate 3 interview questions:

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

# Function to save the audio file
def save_audio_file(audio_bytes, file_extension="wav"):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"audio_{timestamp}.{file_extension}"
    file_path = os.path.join("saved_audios", file_name)

    os.makedirs("saved_audios", exist_ok=True)  # Ensure the directory exists

    with open(file_path, "wb") as f:
        f.write(audio_bytes)
    return file_path

# Function to transcribe audio using Whisper API
def transcribe_audio(file_path):
    with open(file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcription.text

# Function to analyze the transcribed response
def analyze_response(transcript):
    prompt = f"""
    Act as an expert in AI/ML and software engineering and Evaluate the following answer for its relevance, clarity, and technical depth in the context of an AI engineering interview question.

    Candidate's Response: {transcript}

    Provide analysis in short (one-liner) & crisp bullet points: 
    - Relevance
    - Clarity
    - Technical depth
    """
    chat_model = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
    response = chat_model.generate([prompt])
    analysis = response.generations[0][0].text.strip()
    return analysis

# Function to handle audio recording and transcription
def handle_audio_recording(question_index):
    audio_bytes = audio_recorder(pause_threshold=2.0, sample_rate=41000, key=f"audio_recorder_{question_index}")
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")  # Play recorded audio

        # Save audio and provide feedback on file path
        file_path = save_audio_file(audio_bytes, "wav")
        st.write(f"Audio saved to: {file_path}")

        # Transcribe the saved audio file and analyze the response
        transcript = transcribe_audio(file_path)  # Transcribe using Whisper
        st.write("### Transcription of Your Response")
        st.write(transcript)

        analysis = analyze_response(transcript)
        st.write("### Analysis of Your Response")
        st.write(analysis)

        return transcript, analysis
    return None, None

st.title("Interview Preparation")

# Display candidate insights and job description
st.write("### Candidate Insights")
st.write(st.session_state.insights)

st.write("### Job Description")
st.write(st.session_state.jd_text)

# Generate interview questions if they haven't been generated yet
if not st.session_state.questions:
    st.session_state.questions = generate_questions(st.session_state.insights, st.session_state.jd_text)

# Display and interact with each question
responses = []
for i, question in enumerate(st.session_state.questions, 1):
    st.write(f"**Question {i}:** {question}")

    col1, col2 = st.columns(2)
    with col1:
        st.write("#### Record Your Answer")
        transcript, analysis = handle_audio_recording(i)  # Pass the question index to avoid duplicate IDs
        if transcript and analysis:
            responses.append((transcript, analysis))

    with col2:
        st.write("#### Or Type Your Answer")
        text_response = st.text_area(f"Type your answer for Question {i}", key=f"text_response_{i}")
        if text_response:
            analysis = analyze_response(text_response)
            st.write("### Analysis of Your Response")
            st.write(analysis)
            responses.append((text_response, analysis))

# Save responses in session state
st.session_state.responses = responses

# Submit interview and generate final insights
if st.button("Submit Interview"):
    insights_summary = "\n".join([response[1] for response in st.session_state.responses if response[1]])
    prompt = f"""
    Act as an expert in AI/ML and software engineering and Based on the following interview responses and analyses, provide a final summary for the interviewer:

    Interview Responses and Analyses:
    {insights_summary}

    Generate a short (one-liner) & concise structured summary in bullet points:
    - Overall performance
    - Strengths
    - Areas for improvement
    - Can the candidate be selected for the Next round?
    """
    chat_model = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
    response = chat_model.generate([prompt])
    final_insights = response.generations[0][0].text.strip()

    st.write("### Interviewer's Summary and Insights")
    st.write(final_insights)
