import streamlit as st
import tempfile
import fitz  # PyMuPDF
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import os

# Set your OpenAI API key here
os.environ["OPENAI_API_KEY"] = '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'

# Function to generate insights based on context
def generate_insights(resume_text, resume_links):
    prompt_template = f"""
    You are an experienced Technical Recruiter specializing in AI roles. 
    Review the candidate's resume and extract key insights relevant to an AI engineering position.

    Resume Details:
    - Parsed Resume Text Content: {resume_text}
    - Hyperlinked Information: {resume_links}

    Please extract and organize the following information:
    1. **Candidate Name**
    2. **Educational Qualifications**
    3. **Total Work Experience**
    4. **Relevant AI Experience**
    5. **Gaps in Employment**
    6. **Publications**
    7. **Professional Links**
    8. **Other Noteworthy Details**

    Output the insights in a clear, summarized format.
    """
    prompt = PromptTemplate.from_template(prompt_template)
    chat_model = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
    response = chat_model.generate([prompt.format(resume_text=resume_text, resume_links=resume_links)])
    insights = response.generations[0][0].text.strip()
    return insights

# Function to parse PDF with text and hyperlinks
def parse_pdf_with_links(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(uploaded_file.read())
        temp_file_path = temp_file.name

    text_content = []
    links_with_display_names = []

    with fitz.open(temp_file_path) as doc:
        for page_num, page in enumerate(doc):
            text_content.append(page.get_text("text"))
            for link in page.get_links():
                if link.get("uri"):
                    rect = fitz.Rect(link["from"])
                    display_name = page.get_text("text", clip=rect).strip() or "Unnamed Link"
                    links_with_display_names.append({
                        "page": page_num + 1,
                        "display_name": display_name,
                        "uri": link["uri"],
                        "rect": rect
                    })

    full_text = "\n".join(text_content)
    return full_text, links_with_display_names

# Initialize session states for page control
if "page" not in st.session_state:
    st.session_state.page = "upload"  # Set default page to "upload"

# Display upload page if "upload" page is active
if st.session_state.page == "upload":
    st.header("Resume Insights Generator")
    resume_file = st.file_uploader("Upload Resume (PDF only)", type="pdf")
    jd_file = st.file_uploader("Upload Job Description (PDF only)", type="pdf")

    if resume_file:
        resume_text, resume_links = parse_pdf_with_links(resume_file)
        formatted_links = [f"Page {link['page']}: [{link['display_name']}]({link['uri']}) at {link['rect']}" for link in resume_links]
        st.session_state.resume_text = resume_text
        st.session_state.resume_links = "\n".join(formatted_links)

    if jd_file:
        jd_text, jd_links = parse_pdf_with_links(jd_file)
        st.session_state.jd_text = jd_text

    if st.button("Generate Insights from Resume"):
        if "resume_text" in st.session_state and "resume_links" in st.session_state:
            insights = generate_insights(st.session_state.resume_text, st.session_state.resume_links)
            st.session_state.insights = insights
            st.write("### Extracted Insights from the Resume")
            st.write(insights)
        else:
            st.error("Please upload a resume before generating insights.")
