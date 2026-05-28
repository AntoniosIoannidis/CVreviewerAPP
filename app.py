import streamlit as st
import pdfplumber
from google import genai
from google.genai import types
import os
import json
import plotly.graph_objects as go
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from io import BytesIO

# Load environment variables
load_dotenv()

# Streamlit UI Configuration (Must be first Streamlit command)
st.set_page_config(
    page_title="Professional AI CV Reviewer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if "api_key" not in st.session_state:
    st.session_state["api_key"] = os.getenv("GOOGLE_API_KEY") or ""

if "analysis" not in st.session_state:
    st.session_state["analysis"] = None

if "job_desc" not in st.session_state:
    st.session_state["job_desc"] = ""

if "tailored_cv" not in st.session_state:
    st.session_state["tailored_cv"] = None

if "cv_text" not in st.session_state:
    st.session_state["cv_text"] = ""

# Custom Premium CSS Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif;
        background: radial-gradient(circle at 50% 0%, #17153b 0%, #0c0a1a 50%, #030008 100%) !important;
        color: #f8fafc !important;
    }

    /* Header Container */
    .header-container {
        position: relative;
        background: linear-gradient(135deg, rgba(30, 27, 75, 0.5) 0%, rgba(15, 23, 42, 0.8) 100%);
        padding: 3rem 2.5rem;
        border-radius: 20px;
        border: 1px solid rgba(99, 102, 241, 0.2);
        margin-bottom: 2.5rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        overflow: hidden;
    }

    .header-container::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(168, 85, 247, 0.08) 0%, transparent 60%);
        pointer-events: none;
    }

    .header-tag {
        display: inline-block;
        padding: 6px 12px;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 100px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        color: #c7d2fe;
        margin-bottom: 1.25rem;
    }

    .header-title {
        font-size: 2.75rem !important;
        font-weight: 800 !important;
        margin: 0 !important;
        margin-bottom: 0.75rem !important;
        letter-spacing: -0.03em !important;
        background: linear-gradient(135deg, #ffffff 30%, #c7d2fe 70%, #a855f7 100%);
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        line-height: 1.2 !important;
    }

    .header-subtitle {
        font-size: 1.15rem !important;
        color: #94a3b8 !important;
        font-weight: 400 !important;
        margin: 0 !important;
        max-width: 800px;
        line-height: 1.6 !important;
    }

    /* Sidebar Customization */
    [data-testid="stSidebar"] {
        background-color: #06040c !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
    }

    [data-testid="stSidebar"] p, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label {
        color: #f8fafc !important;
    }

    /* Primary buttons styling */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 0.85rem 2rem !important;
        border-radius: 12px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.35) !important;
        width: 100% !important;
        height: auto !important;
        font-size: 1.05rem !important;
        letter-spacing: -0.01em !important;
    }

    div.stButton > button:first-child:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 30px rgba(168, 85, 247, 0.5) !important;
        background: linear-gradient(135deg, #4f46e5 0%, #9333ea 100%) !important;
        color: white !important;
    }

    div.stButton > button:first-child:active {
        transform: translateY(1px) !important;
    }

    /* Download buttons */
    div.stDownloadButton > button:first-child {
        background: linear-gradient(135deg, #06b6d4 0%, #0d9488 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 0.85rem 2rem !important;
        border-radius: 12px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 20px rgba(6, 182, 212, 0.25) !important;
        width: 100% !important;
        height: auto !important;
        font-size: 1.05rem !important;
    }

    div.stDownloadButton > button:first-child:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 30px rgba(13, 148, 136, 0.4) !important;
        background: linear-gradient(135deg, #0891b2 0%, #0f766e 100%) !important;
        color: white !important;
    }

    /* UI Cards container */
    .card {
        background: rgba(15, 23, 42, 0.55) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        padding: 2rem !important;
        border-radius: 18px !important;
        border: 1px solid rgba(99, 102, 241, 0.15) !important;
        box-shadow: 0 12px 36px rgba(0, 0, 0, 0.25) !important;
        margin-bottom: 2rem !important;
        transition: all 0.3s ease !important;
    }

    .card:hover {
        transform: translateY(-4px) !important;
        border-color: rgba(168, 85, 247, 0.3) !important;
        box-shadow: 0 20px 40px rgba(168, 85, 247, 0.08), 0 12px 36px rgba(0, 0, 0, 0.3) !important;
    }

    .executive-summary-card {
        border-left: 5px solid #a855f7 !important;
    }

    .card-title {
        font-weight: 700 !important;
        font-size: 1.35rem !important;
        color: #ffffff !important;
        margin-bottom: 1rem !important;
        letter-spacing: -0.02em !important;
    }

    .card-header-icon {
        font-size: 1.75rem !important;
        margin-bottom: 0.5rem !important;
    }

    .card-body-text {
        font-size: 1.05rem !important;
        color: #cbd5e1 !important;
        line-height: 1.6 !important;
    }

    /* Inputs override */
    div[data-testid="stTextArea"] textarea {
        background-color: rgba(15, 23, 42, 0.6) !important;
        color: #f8fafc !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: 12px !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease-in-out !important;
    }

    div[data-testid="stTextArea"] textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.25) !important;
    }

    div[data-testid="stFileUploader"] section {
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 1px dashed rgba(99, 102, 241, 0.3) !important;
        border-radius: 12px !important;
        color: #f8fafc !important;
        transition: all 0.2s ease-in-out !important;
        padding: 2rem !important;
    }

    div[data-testid="stFileUploader"] section:hover {
        border-color: #a855f7 !important;
        background-color: rgba(15, 23, 42, 0.8) !important;
    }

    div[data-testid="stFileUploader"] section [data-testid="stMarkdownContainer"] p {
        color: #cbd5e1 !important;
    }

    /* Tabs override */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px !important;
        background-color: rgba(15, 23, 42, 0.65) !important;
        padding: 8px !important;
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        margin-bottom: 2rem !important;
    }

    .stTabs [data-baseweb="tab"] {
        height: 46px !important;
        background-color: transparent !important;
        border-radius: 10px !important;
        color: #94a3b8 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: none !important;
        padding: 0 24px !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #ffffff !important;
        background-color: rgba(255, 255, 255, 0.04) !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%) !important;
        color: #c7d2fe !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        box-shadow: 0 4px 20px -2px rgba(99, 102, 241, 0.15) !important;
        font-weight: 700 !important;
    }

    /* Metric styling */
    .metric-card {
        background: rgba(15, 23, 42, 0.5) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(99, 102, 241, 0.15) !important;
        padding: 1.5rem !important;
        margin-bottom: 1.5rem !important;
    }

    .metric-label {
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: #94a3b8 !important;
        margin-bottom: 0.5rem !important;
        font-weight: 700 !important;
    }

    .metric-value {
        font-size: 2.75rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #60a5fa 0%, #a855f7 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        margin-bottom: 0.75rem !important;
        line-height: 1.1 !important;
    }

    .metric-status {
        color: #e2e8f0 !important;
        font-size: 0.95rem !important;
        margin-bottom: 0.5rem !important;
    }

    .metric-desc {
        color: #cbd5e1 !important;
        font-size: 0.9rem !important;
        line-height: 1.5 !important;
        border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
        padding-top: 0.75rem !important;
        margin-top: 0.75rem !important;
    }

    /* Strengths Container */
    .strengths-container {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }

    .strength-card {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 1.15rem 1.4rem;
        background: rgba(16, 185, 129, 0.05) !important;
        border: 1px solid rgba(16, 185, 129, 0.25) !important;
        border-radius: 12px;
        transition: all 0.2s ease;
    }

    .strength-card:hover {
        background: rgba(16, 185, 129, 0.08) !important;
        transform: translateX(4px);
        border-color: rgba(16, 185, 129, 0.4) !important;
    }

    .strength-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background-color: #10b981;
        color: #030712;
        font-size: 0.85rem;
        font-weight: 800;
    }

    .strength-text {
        font-size: 1rem;
        color: #dcfce7;
        font-weight: 500;
    }

    /* Keywords Pill Section */
    .keywords-container {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 12px;
    }

    .keyword-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        background: rgba(239, 68, 68, 0.05) !important;
        border: 1px solid rgba(239, 68, 68, 0.2) !important;
        border-radius: 100px;
        font-size: 0.9rem;
        color: #fecdd3;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .keyword-badge:hover {
        background: rgba(239, 68, 68, 0.1) !important;
        border-color: rgba(239, 68, 68, 0.45) !important;
        transform: scale(1.03);
    }

    .keyword-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #ef4444;
        box-shadow: 0 0 8px #ef4444;
    }

    /* STAR Efficacy Card */
    .star-card {
        background: rgba(15, 23, 42, 0.5) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(168, 85, 247, 0.2) !important;
        padding: 1.5rem !important;
        position: relative;
        overflow: hidden;
    }

    .star-badge {
        position: absolute;
        top: 1rem;
        right: 1rem;
        padding: 4px 8px;
        background: rgba(168, 85, 247, 0.15) !important;
        border: 1px solid rgba(168, 85, 247, 0.3) !important;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        color: #e9d5ff;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .star-content {
        font-size: 1rem !important;
        color: #e2e8f0 !important;
        line-height: 1.6 !important;
        padding-top: 1.5rem !important;
    }

    /* Roadmap Grid */
    .roadmap-container {
        display: flex;
        flex-direction: column;
        gap: 14px;
    }

    .roadmap-card {
        display: flex;
        align-items: flex-start;
        gap: 16px;
        padding: 1.25rem 1.5rem;
        background: rgba(30, 41, 59, 0.3) !important;
        border: 1px solid rgba(99, 102, 241, 0.15) !important;
        border-radius: 14px;
        transition: all 0.25s ease;
    }

    .roadmap-card:hover {
        background: rgba(30, 41, 59, 0.5) !important;
        border-color: rgba(99, 102, 241, 0.45) !important;
        transform: translateX(6px);
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05), 0 8px 24px rgba(0, 0, 0, 0.15);
    }

    .roadmap-number-badge {
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 32px;
        height: 32px;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        border-radius: 50%;
        color: #ffffff;
        font-weight: 800;
        font-size: 0.95rem;
        box-shadow: 0 0 12px rgba(168, 85, 247, 0.4);
    }

    .roadmap-text {
        font-size: 1rem;
        color: #cbd5e1;
        line-height: 1.5;
        font-weight: 500;
        padding-top: 2px;
    }

    /* Sidebar lists & divider */
    .stDivider {
        margin: 2.5rem 0 !important;
    }

    hr {
        border-color: rgba(255, 255, 255, 0.08) !important;
    }

    /* Typography styles inside blocks */
    h4 {
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        color: #ffffff !important;
        margin-bottom: 1.25rem !important;
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
        st.error(f"Error extracting PDF text: {e}")
    return text


def clean_json_response(json_text):
    """Safely cleans the raw API output text and wraps JSON parsing logic."""
    json_text = json_text.strip()
    if json_text.startswith("```json"):
        json_text = json_text[7:]
    elif json_text.startswith("```"):
        json_text = json_text[3:]
    if json_text.endswith("```"):
        json_text = json_text[:-3]
    return json.loads(json_text.strip())


def get_genai_client():
    """Creates a client instance using the session API key."""
    if st.session_state["api_key"]:
        return genai.Client(api_key=st.session_state["api_key"])
    return None


def analyze_cv(cv_text, job_description):
    """Analyzes the CV against the job description using Gemini with automatic model fallback."""
    client = get_genai_client()
    if not client:
        return None

    try:
        prompt = f"""
        You are an expert HR Recruiter and Career Coach specializing in ATS (Applicant Tracking Systems) and candidate evaluation.
        Analyze the following CV against the provided Job Description and return your analysis in JSON format.

        CV Content:
        {cv_text}

        Job Description:
        {job_description}

        The JSON response must have exactly these keys and types:
        1. "match_score": (integer between 0 and 100)
        2. "missing_keywords": (list of strings)
        3. "formatting_score": (integer between 0 and 100)
        4. "formatting_feedback": (string)
        5. "star_method_evaluation": (string)
        6. "ats_compatibility": (string)
        7. "top_strengths": (list of strings, max 3)
        8. "improvement_suggestions": (list of strings)
        9. "summary": (string, brief 2-sentence summary)

        Ensure all keys exist and values match the requested formats.
        """

        # Try primary model: gemini-2.5-flash
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return clean_json_response(response.text)
        except Exception as primary_err:
            err_str = str(primary_err)
            if "503" in err_str or "UNAVAILABLE" in err_str or "ResourceExhausted" in err_str or "429" in err_str:
                st.info("⚠️ Primary model (gemini-2.5-flash) is currently busy. Switching seamlessly to highly reliable fallback model (gemini-1.5-flash)...")
                response = client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                return clean_json_response(response.text)
            else:
                raise primary_err
    except Exception as e:
        st.error(f"Error during AI analysis: {str(e)}")
        return None


def tailor_cv(cv_text, job_description):
    """Generates a tailored version of the CV matching the Job Description with automatic model fallback."""
    client = get_genai_client()
    if not client:
        return None

    try:
        prompt = f"""
        You are an expert resume writer and career consultant.
        Your task is to rewrite and tailor the candidate's CV to match the target Job Description as closely as possible.
        
        Original CV Content:
        {cv_text}

        Target Job Description:
        {job_description}

        Follow these strict guidelines:
        1. **Do NOT Fabricate Information**: Do not add degrees, companies, projects, or work experiences that are not present in the original CV. You may, however, rephrase, expand, or highlight existing experience to match job requirements.
        2. **Optimize Keywords**: Seamlessly integrate relevant keywords from the job description into the tailored CV's skills and experience sections.
        3. **Apply the STAR Method**: Rewrite professional experience bullet points to emphasize action verbs, situation, task, and measurable results (quantified where possible).
        4. **Clean Markdown Format**: Return the tailored CV formatted cleanly in Markdown, using clear sections (e.g., Summary, Professional Experience, Skills, Education).
        
        Produce only the tailored CV in markdown format without any conversational intro/outro.
        """

        # Try primary model: gemini-2.5-flash
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            return response.text
        except Exception as primary_err:
            err_str = str(primary_err)
            if "503" in err_str or "UNAVAILABLE" in err_str or "ResourceExhausted" in err_str or "429" in err_str:
                st.info("⚠️ Primary model (gemini-2.5-flash) is currently busy. Switching seamlessly to highly reliable fallback model (gemini-1.5-flash)...")
                response = client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=prompt,
                )
                return response.text
            else:
                raise primary_err
    except Exception as e:
        st.error(f"Error tailoring CV: {str(e)}")
        return None


def create_pdf_report(analysis_data):
    """Generates a professional multi-page PDF report using ReportLab flowables to handle wrapping."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    story = []
    
    # Styles Setup
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1e1b4b'),
        spaceAfter=15
    )
    
    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#4f46e5'),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )
    
    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    # Document Header
    story.append(Paragraph("CV Optimization & Match Report", title_style))
    story.append(Paragraph("A comprehensive ATS compatibility, formatting, and performance analysis powered by AI.", body_style))
    story.append(Spacer(1, 15))
    
    # KPI Grid Table
    score_data = [
        [
            Paragraph(f"<b>Match Score:</b> {analysis_data['match_score']}%", body_style),
            Paragraph(f"<b>Formatting Score:</b> {analysis_data['formatting_score']}%", body_style)
        ]
    ]
    score_table = Table(score_data, colWidths=[250, 250])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('PADDING', (0,0), (-1,-1), 12),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 15))
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", h2_style))
    story.append(Paragraph(analysis_data['summary'], body_style))
    story.append(Spacer(1, 10))
    
    # Top Strengths
    story.append(Paragraph("Top Strengths", h2_style))
    for strength in analysis_data['top_strengths']:
        story.append(Paragraph(f"• {strength}", bullet_style))
    story.append(Spacer(1, 10))
    
    # Missing Keywords
    story.append(Paragraph("Missing Keywords & Gaps", h2_style))
    if analysis_data['missing_keywords']:
        keywords_str = ", ".join(analysis_data['missing_keywords'])
        story.append(Paragraph(keywords_str, body_style))
    else:
        story.append(Paragraph("No critical keywords missing from CV.", body_style))
    story.append(Spacer(1, 10))
    
    # ATS Compatibility
    story.append(Paragraph("ATS Compatibility & Format Feedback", h2_style))
    story.append(Paragraph(f"<b>System Readability:</b> {analysis_data['ats_compatibility']}", body_style))
    story.append(Paragraph(f"<b>Structuring Tips:</b> {analysis_data['formatting_feedback']}", body_style))
    story.append(Spacer(1, 10))
    
    # STAR Method Evaluation
    story.append(Paragraph("STAR Impact Analysis", h2_style))
    story.append(Paragraph(analysis_data['star_method_evaluation'], body_style))
    story.append(Spacer(1, 10))
    
    # Action Roadmap
    story.append(Paragraph("Actionable Optimization Roadmap", h2_style))
    for suggestion in analysis_data['improvement_suggestions']:
        story.append(Paragraph(f"• {suggestion}", bullet_style))
        
    # Running footer template
    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#64748b'))
        canvas.drawString(54, 30, "Confidential | Professional CV Reviewer Report")
        canvas.drawRightString(letter[0] - 54, 30, f"Page {doc.page}")
        canvas.restoreState()
        
    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    buffer.seek(0)
    return buffer


# Sidebar settings configuration
with st.sidebar:
    st.markdown("### Settings & Configuration")
    
    # API key load / input handling
    if os.getenv("GOOGLE_API_KEY"):
        st.success("✅ API Key loaded from system .env file")
        st.session_state["api_key"] = os.getenv("GOOGLE_API_KEY")
    else:
        user_key = st.text_input("Gemini API Key:", value=st.session_state["api_key"], type="password", help="Configure your Gemini API key here")
        if user_key and user_key != st.session_state["api_key"]:
            st.session_state["api_key"] = user_key
            st.success("API Key updated for session!")

    st.divider()
    st.markdown("""
    **Evaluation Metrics:**
    - **ATS Standard Compatibility**: Analyzes file headers, standard margins, and structural elements.
    - **Keyword Semantic Fit**: Evaluates gaps between CV terms and the job description.
    - **STAR Efficacy**: Measures standard Situation-Task-Action-Result quantification.
    """)

# Custom Page Header
st.markdown("""
    <div class="header-container">
        <div class="header-tag">✨ POWERED BY GEMINI 2.5 FLASH</div>
        <h1 class="header-title">Professional CV Optimizer</h1>
        <p class="header-subtitle">Elevate your application with institutional-grade ATS parsing, semantic keyword intelligence, and STAR impact quantification.</p>
    </div>
    """, unsafe_allow_html=True)

# Application Input Layout
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 1. Job Details")
    st.session_state["job_desc"] = st.text_area(
        "Paste the Target Job Description:",
        value=st.session_state["job_desc"],
        height=300,
        placeholder="Copy and paste the job duties, requirements, and responsibilities here..."
    )

with col2:
    st.markdown("### 2. Your Document")
    uploaded_file = st.file_uploader("Upload your CV (PDF format):", type="pdf")
    if uploaded_file:
        st.success(f"File '{uploaded_file.name}' successfully loaded!")

st.divider()

# Analyze action execution
if st.button("Generate Comprehensive Analysis"):
    if not st.session_state["job_desc"] or not uploaded_file:
        st.warning("Please upload a CV and paste the target job description to run analysis.")
    elif not st.session_state["api_key"]:
        st.error("Missing Gemini API Key. Configure the key in the settings sidebar.")
    else:
        with st.spinner("Analyzing professional profile metrics..."):
            cv_text = extract_text_from_pdf(uploaded_file)
            if cv_text.strip():
                st.session_state["cv_text"] = cv_text
                st.session_state["tailored_cv"] = None  # Reset tailoring draft
                analysis_results = analyze_cv(cv_text, st.session_state["job_desc"])
                if analysis_results:
                    st.session_state["analysis"] = analysis_results
                    st.balloons()
            else:
                st.error("Could not extract readable text from the uploaded PDF document. Please verify standard file encoding.")

# Persist and display dashboard contents
if st.session_state["analysis"]:
    analysis = st.session_state["analysis"]
    
    # 2 Column layout: Gauge Match Chart and Executive Summary
    res_col1, res_col2 = st.columns([1, 2], gap="medium")
    
    with res_col1:
        # Gauge Plotly Chart
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = analysis['match_score'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Match Score", 'font': {'size': 20, 'weight': 'bold', 'color': '#ffffff'}},
            gauge = {
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#94a3b8"},
                'bar': {'color': "#818cf8"},
                'bgcolor': "rgba(15, 23, 42, 0.4)",
                'borderwidth': 1,
                'bordercolor': "rgba(99, 102, 241, 0.2)",
                'steps': [
                    {'range': [0, 50], 'color': 'rgba(239, 68, 68, 0.15)'},
                    {'range': [50, 80], 'color': 'rgba(245, 158, 11, 0.15)'},
                    {'range': [80, 100], 'color': 'rgba(16, 185, 129, 0.15)'}],
                'threshold': {
                    'line': {'color': "#10b981", 'width': 4},
                    'thickness': 0.75,
                    'value': 85}}))
        
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={'color': "#f8fafc", 'family': "'Plus Jakarta Sans', 'Inter', sans-serif"},
            margin=dict(t=40, b=10, l=30, r=30),
            height=280
        )
        st.plotly_chart(fig, use_container_width=True)

    with res_col2:
        st.markdown(f"<div class='card executive-summary-card'><div class='card-header-icon'>📝</div><div class='card-title'>Executive Summary</div><div class='card-body-text'>{analysis['summary']}</div></div>", unsafe_allow_html=True)

    st.divider()

    # Detailed Analysis Tab Interface
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Profile Strengths & Keywords",
        "📋 ATS & Formatting Check",
        "💡 Improvement Roadmap",
        "✨ Tailored CV Editor",
        "📥 Export PDF Report"
    ])
    
    with tab1:
        col_str, col_key = st.columns(2)
        with col_str:
            st.markdown("#### ✅ Top Core Strengths")
            strengths_html = "<div class='strengths-container'>"
            for strength in analysis['top_strengths']:
                strengths_html += f"<div class='strength-card'><div class='strength-icon'>✓</div><div class='strength-text'>{strength}</div></div>"
            strengths_html += "</div>"
            st.markdown(strengths_html, unsafe_allow_html=True)
                
        with col_key:
            st.markdown("#### ❌ Missing Keywords & Gaps")
            if analysis['missing_keywords']:
                st.markdown("<p style='color: #cbd5e1; margin-bottom: 12px;'>Incorporate these critical keywords into your CV content to bypass semantic ATS filter thresholds:</p>", unsafe_allow_html=True)
                keywords_html = "<div class='keywords-container'>"
                for keyword in analysis['missing_keywords']:
                    keywords_html += f"<span class='keyword-badge'><span class='keyword-dot'></span>{keyword}</span>"
                keywords_html += "</div>"
                st.markdown(keywords_html, unsafe_allow_html=True)
            else:
                st.success("Awesome! No critical keywords missing from your CV profile.")
                
    with tab2:
        col_ats, col_star = st.columns(2)
        with col_ats:
            st.markdown("#### 📊 ATS Formatting Review")
            st.markdown(f"<div class='metric-card'><div class='metric-label'>Structure & Parsability Score</div><div class='metric-value'>{analysis['formatting_score']}%</div><div class='metric-status'><b>ATS Compatibility:</b> {analysis['ats_compatibility']}</div><div class='metric-desc'><b>Formatting Feedback:</b> {analysis['formatting_feedback']}</div></div>", unsafe_allow_html=True)
            
        with col_star:
            st.markdown("#### ✨ STAR Method Efficacy")
            st.markdown(f"<div class='star-card'><div class='star-badge'>AI Evaluation</div><div class='star-content'>{analysis['star_method_evaluation']}</div></div>", unsafe_allow_html=True)
            
    with tab3:
        st.markdown("#### 🛠 Actionable Profile Roadmap")
        st.markdown("<p style='color: #cbd5e1; margin-bottom: 16px;'>Apply these sequential recommendations to strategically optimize candidate fit and human readability:</p>", unsafe_allow_html=True)
        roadmap_html = "<div class='roadmap-container'>"
        for idx, suggestion in enumerate(analysis['improvement_suggestions']):
            roadmap_html += f"<div class='roadmap-card'><div class='roadmap-number-badge'>{idx + 1}</div><div class='roadmap-text'>{suggestion}</div></div>"
        roadmap_html += "</div>"
        st.markdown(roadmap_html, unsafe_allow_html=True)
            
    with tab4:
        st.markdown("#### ✨ AI-Tailored CV Editor")
        st.write("Generate a professionally tailored and job-optimized draft of your CV. This applies the AI's suggestions and structures bullets using the STAR method without fabricating any data.")
        
        if not st.session_state["tailored_cv"]:
            if st.button("Generate Tailored CV Draft"):
                with st.spinner("AI is crafting your tailored CV..."):
                    tailored = tailor_cv(st.session_state["cv_text"], st.session_state["job_desc"])
                    if tailored:
                        st.session_state["tailored_cv"] = tailored
                        st.rerun()
        else:
            edited_cv = st.text_area(
                "Review & Edit your tailored CV (Markdown format):",
                value=st.session_state["tailored_cv"],
                height=500
            )
            
            if edited_cv != st.session_state["tailored_cv"]:
                st.session_state["tailored_cv"] = edited_cv
                
            st.divider()
            
            exp_col1, exp_col2, exp_col3 = st.columns([1, 1, 2])
            with exp_col1:
                st.download_button(
                    label="📥 Download as Markdown (.md)",
                    data=st.session_state["tailored_cv"],
                    file_name="Tailored_CV.md",
                    mime="text/markdown"
                )
            with exp_col2:
                st.download_button(
                    label="📥 Download as Text (.txt)",
                    data=st.session_state["tailored_cv"],
                    file_name="Tailored_CV.txt",
                    mime="text/plain"
                )
            with exp_col3:
                if st.button("🔄 Regenerate Tailored CV Draft"):
                    st.session_state["tailored_cv"] = None
                    st.rerun()

    with tab5:
        st.markdown("#### 📥 Download Official Optimization Report")
        st.write("Generate a professionally structured, printable PDF report. This report handles text wrapping cleanly and can be shared offline.")
        
        pdf_data = create_pdf_report(analysis)
        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_data,
            file_name="CV_Optimization_Report.pdf",
            mime="application/pdf",
        )
