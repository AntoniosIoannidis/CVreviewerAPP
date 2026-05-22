import streamlit as st
import pdfplumber
import google.generativeai as genai
import os
import json
import plotly.graph_objects as go
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Custom CSS for a professional look
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #0056b3;
        border-color: #0056b3;
    }
    .reportview-container .main .block-container {
        padding-top: 2rem;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

def extract_text_from_pdf(uploaded_file):
    """Extracts text from an uploaded PDF file."""
    text = ""
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        st.error(f"Error extracting PDF: {e}")
    return text

def analyze_cv(cv_text, job_description):
    """Analyzes the CV against the job description using Gemini with structured output."""
    if not api_key:
        return None

    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    You are an expert HR Recruiter and Career Coach specializing in ATS (Applicant Tracking Systems) and candidate evaluation.
    Analyze the following CV against the provided Job Description and return your analysis STRICTLY in JSON format.

    CV Content:
    {cv_text}

    Job Description:
    {job_description}

    The JSON response must have exactly these keys:
    1. "match_score": (int, 0-100)
    2. "missing_keywords": (list of strings)
    3. "formatting_score": (int, 0-100)
    4. "formatting_feedback": (string)
    5. "star_method_evaluation": (string)
    6. "ats_compatibility": (string)
    7. "top_strengths": (list of strings, max 3)
    8. "improvement_suggestions": (list of strings)
    9. "summary": (string, brief 2-sentence summary)

    Ensure the JSON is valid and properly escaped.
    """

    try:
        response = model.generate_content(prompt)
        json_text = response.text.strip()
        if json_text.startswith("```json"):
            json_text = json_text[7:-3].strip()
        elif json_text.startswith("```"):
            json_text = json_text[3:-3].strip()
        
        return json.loads(json_text)
    except Exception as e:
        st.error(f"Error during analysis: {str(e)}")
        return None

def create_pdf_report(analysis_data):
    """Generates a PDF report of the analysis."""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 50, "CV Analysis Report")
    
    p.setFont("Helvetica", 12)
    p.drawString(100, height - 80, f"Match Score: {analysis_data['match_score']}%")
    p.drawString(100, height - 100, f"Summary: {analysis_data['summary']}")
    
    y = height - 130
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, y, "Missing Keywords:")
    p.setFont("Helvetica", 10)
    for kw in analysis_data['missing_keywords']:
        y -= 15
        p.drawString(120, y, f"- {kw}")
    
    y -= 30
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, y, "Top Strengths:")
    p.setFont("Helvetica", 10)
    for strength in analysis_data['top_strengths']:
        y -= 15
        p.drawString(120, y, f"- {strength}")

    y -= 30
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, y, "Improvement Suggestions:")
    p.setFont("Helvetica", 10)
    for suggestion in analysis_data['improvement_suggestions']:
        y -= 15
        if len(suggestion) > 80:
             p.drawString(120, y, f"- {suggestion[:80]}...")
        else:
            p.drawString(120, y, f"- {suggestion}")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# Streamlit UI
st.set_page_config(page_title="Professional AI CV Reviewer", page_icon="📄", layout="wide")

# Sidebar for configuration
with st.sidebar:
    st.title("🛠 Settings")
    if not api_key:
        new_api_key = st.text_input("Gemini API Key:", type="password", help="Get your key from Google AI Studio")
        if new_api_key:
            genai.configure(api_key=new_api_key)
            api_key = new_api_key
            st.success("API Key configured!")
    else:
        st.success("Gemini API Connected")
    
    st.divider()
    st.info(\"\"\"
    **Pro Tip for Recruiters:**
    This tool evaluates CVs based on modern ATS standards, STAR method efficacy, and semantic keyword matching.
    \"\"\")

# Main Content
st.title("🚀 Professional CV Optimizer")
st.subheader("Get hired by transforming your CV into a recruiter magnet.")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 1. Job Opportunity")
    job_desc = st.text_area("Paste the Job Description:", height=300, placeholder="Copy the job requirements and responsibilities here...")

with col2:
    st.markdown("### 2. Your CV")
    uploaded_file = st.file_uploader("Upload your CV (PDF):", type="pdf")
    if uploaded_file:
        st.success(f"File '{uploaded_file.name}' uploaded successfully!")

st.divider()

if st.button("Generate Comprehensive Analysis"):
    if not job_desc or not uploaded_file:
        st.warning("Please provide both a Job Description and a CV.")
    elif not api_key:
        st.error("Missing Gemini API Key. Please configure it in the sidebar.")
    else:
        with st.spinner("AI is analyzing your professional profile..."):
            cv_text = extract_text_from_pdf(uploaded_file)
            if cv_text.strip():
                analysis = analyze_cv(cv_text, job_desc)
                
                if analysis:
                    st.balloons()
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = analysis['match_score'],
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "Match Score", 'font': {'size': 24}},
                        gauge = {
                            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                            'bar': {'color': "#007bff"},
                            'bgcolor': "white",
                            'borderwidth': 2,
                            'bordercolor': "gray",
                            'steps': [
                                {'range': [0, 50], 'color': '#ffcccc'},
                                {'range': [50, 80], 'color': '#fff3cd'},
                                {'range': [80, 100], 'color': '#d4edda'}],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 90}}))
                    
                    st.plotly_chart(fig, use_container_width=True)

                    st.markdown(f"### 📝 Executive Summary")
                    st.info(analysis['summary'])

                    res_col1, res_col2 = st.columns(2)
                    with res_col1:
                        st.markdown("#### ✅ Top Strengths")
                        for s in analysis['top_strengths']:
                            st.write(f"- {s}")
                    
                    with res_col2:
                        st.markdown("#### ❌ Missing Keywords")
                        if analysis['missing_keywords']:
                            st.error(", ".join(analysis['missing_keywords']))
                        else:
                            st.success("No critical keywords missing!")

                    st.divider()

                    with st.expander("📊 Detailed ATS & Formatting Evaluation", expanded=True):
                        e_col1, e_col2 = st.columns(2)
                        e_col1.metric("Formatting Score", f"{analysis['formatting_score']}%")
                        e_col2.write(f"**ATS Compatibility:** {analysis['ats_compatibility']}")
                        st.write(f"**Formatting Feedback:** {analysis['formatting_feedback']}")
                    
                    with st.expander("✨ STAR Method & Impact Analysis", expanded=False):
                        st.write(analysis['star_method_evaluation'])

                    with st.expander("💡 Improvement Roadmap", expanded=True):
                        for suggestion in analysis['improvement_suggestions']:
                            st.write(f"🔹 {suggestion}")

                    pdf_data = create_pdf_report(analysis)
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_data,
                        file_name="CV_Analysis_Report.pdf",
                        mime="application/pdf",
                    )
            else:
                st.error("Could not read text from the CV. Is it an image-based PDF?")
