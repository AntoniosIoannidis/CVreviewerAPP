import streamlit as st
import pdfplumber
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
# Users should set their GOOGLE_API_KEY in a .env file or streamlit secrets
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def extract_text_from_pdf(uploaded_file):
    """Extracts text from an uploaded PDF file using pdfplumber."""
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def analyze_cv(cv_text, job_description):
    """Analyzes the CV against the job description using Gemini."""
    if not api_key:
        return "Error: Gemini API key not found. Please set GOOGLE_API_KEY in your .env file."

    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    You are an expert HR Recruiter and Career Coach. Analyze the following CV against the provided Job Description.
    
    CV Content:
    {cv_text}
    
    Job Description:
    {job_description}
    
    Please provide a detailed evaluation in the following format:
    
    1. **Match Score**: A score out of 100 based on how well the candidate fits the role.
    2. **Keyword Matching**: List missing critical keywords from the job description that should be in the CV.
    3. **Formatting Evaluation**: Assess the CV's layout, readability, and structure.
    4. **Impact-Quantification (STAR Method)**: Evaluate if the candidate uses the STAR (Situation, Task, Action, Result) method and quantifies their achievements.
    5. **Specific Improvement Suggestions**: Provide actionable advice to improve the CV for this specific role.
    
    Be objective, professional, and constructive.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error during analysis: {str(e)}"

# Streamlit UI
st.set_page_config(page_title="AI CV Reviewer", page_icon="📄", layout="wide")

st.title("📄 AI CV Reviewer")
st.markdown("""
Upload your CV (PDF) and paste the Job Description to get an AI-powered analysis of your fit for the role.
""")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Job Description")
    job_desc = st.text_area("Paste the job description here:", height=300)

with col2:
    st.subheader("2. Upload CV")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if st.button("Analyze CV"):
    if not job_desc:
        st.error("Please provide a job description.")
    elif not uploaded_file:
        st.error("Please upload a CV PDF.")
    elif not api_key:
        st.error("API Key not found. Please configure GOOGLE_API_KEY.")
    else:
        with st.spinner("Analyzing your CV..."):
            cv_text = extract_text_from_pdf(uploaded_file)
            if cv_text.strip():
                analysis = analyze_cv(cv_text, job_desc)
                st.subheader("Analysis Results")
                st.markdown(analysis)
            else:
                st.error("Could not extract text from the PDF. Please ensure it's not a scanned image without OCR.")

with st.sidebar:
    st.subheader("Configuration")
    if not api_key:
        new_api_key = st.text_input("Enter your Gemini API Key:", type="password")
        if new_api_key:
            genai.configure(api_key=new_api_key)
            api_key = new_api_key
            st.success("API Key configured for this session!")
    else:
        st.success("Gemini API is configured.")
    
    st.info("""
    **How it works:**
    - Extracts text from your PDF.
    - Uses Gemini 1.5 Flash to match keywords.
    - Evaluates impact using the STAR method.
    - Provides a Match Score and improvement tips.
    """)
