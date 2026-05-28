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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global theme settings */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #f8fafc;
        color: #0f172a;
    }
    
    /* Header layout styling */
    .header-container {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.15), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
    }
    
    .header-title {
        font-size: 2.3rem;
        font-weight: 700;
        margin: 0;
        margin-bottom: 0.5rem;
        letter-spacing: -0.025em;
        background: linear-gradient(to right, #ffffff, #c7d2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .header-subtitle {
        font-size: 1.05rem;
        color: #e0e7ff;
        font-weight: 400;
        margin: 0;
    }
    
    /* Sidebar customization */
    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #1e293b;
    }
    
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label {
        color: #f8fafc !important;
    }
    
    /* Primary buttons styling */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
        color: white;
        font-weight: 600;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2);
        width: 100%;
        height: auto;
    }
    
    div.stButton > button:first-child:hover {
        transform: translateY(-1px);
        box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.3);
        background: linear-gradient(135deg, #4338ca 0%, #3730a3 100%);
        border: none;
        color: white;
    }
    
    div.stButton > button:first-child:active {
        transform: translateY(1px);
    }
    
    /* Export and Download buttons */
    div.stDownloadButton > button:first-child {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        color: white;
        font-weight: 600;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 4px 6px -1px rgba(5, 150, 105, 0.2);
        width: 100%;
        height: auto;
    }
    
    div.stDownloadButton > button:first-child:hover {
        transform: translateY(-1px);
        box-shadow: 0 10px 15px -3px rgba(5, 150, 105, 0.3);
        background: linear-gradient(135deg, #047857 0%, #065f46 100%);
        border: none;
        color: white;
    }
    
    /* UI Cards container */
    .card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
        border: 1px solid #e2e8f0;
        margin-bottom: 1.5rem;
    }
    
    .card-title {
        font-weight: 600;
        font-size: 1.15rem;
        color: #1e293b;
        margin-bottom: 0.75rem;
    }
    
    /* Custom tabs design */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #e2e8f0;
        padding: 6px;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        white-space: pre;
        background-color: transparent;
        border-radius: 8px;
        color: #475569;
        font-weight: 500;
        transition: all 0.2s;
        border: none;
        padding: 0 20px;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #0f172a;
        background-color: rgba(255, 255, 255, 0.5);
    }
    
    .stTabs [aria-selected="true"] {
        background-color: white !important;
        color: #4f46e5 !important;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.08);
        font-weight: 600;
    }
    
    /* Feedback highlights styling */
    .strength-item {
        padding: 10px 14px;
        background-color: #f0fdf4;
        border-left: 4px solid #10b981;
        border-radius: 0 8px 8px 0;
        margin-bottom: 8px;
        font-size: 0.95rem;
        color: #14532d;
    }
    
    .keyword-item {
        display: inline-block;
        padding: 6px 12px;
        background-color: #fef2f2;
        border: 1px solid #fee2e2;
        border-radius: 100px;
        margin: 4px;
        font-size: 0.85rem;
        color: #991b1b;
        font-weight: 500;
    }
    
    .roadmap-item {
        padding: 10px 14px;
        background-color: #f0f9ff;
        border-left: 4px solid #0284c7;
        border-radius: 0 8px 8px 0;
        margin-bottom: 8px;
        font-size: 0.95rem;
        color: #0c4a6e;
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
    """Analyzes the CV against the job description using Gemini with the new google-genai SDK."""
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

        # Generate content using modern gemini-2.5-flash
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return clean_json_response(response.text)
    except Exception as e:
        st.error(f"Error during AI analysis: {str(e)}")
        return None


def tailor_cv(cv_text, job_description):
    """Generates a tailored version of the CV matching the Job Description using Gemini."""
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

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
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
        <h1 class="header-title">🚀 Professional CV Optimizer</h1>
        <p class="header-subtitle">Maximize your hiring rate with deep AI-driven ATS, formatting, and impact evaluation.</p>
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
            title = {'text': "Match Score", 'font': {'size': 20, 'weight': 'bold'}},
            gauge = {
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#475569"},
                'bar': {'color': "#4f46e5"},
                'bgcolor': "white",
                'borderwidth': 1,
                'bordercolor': "#cbd5e1",
                'steps': [
                    {'range': [0, 50], 'color': '#fee2e2'},
                    {'range': [50, 80], 'color': '#fef3c7'},
                    {'range': [80, 100], 'color': '#dcfce7'}],
                'threshold': {
                    'line': {'color': "#10b981", 'width': 4},
                    'thickness': 0.75,
                    'value': 85}}))
        
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={'color': "#0f172a", 'family': "Inter, sans-serif"},
            margin=dict(t=40, b=10, l=30, r=30),
            height=280
        )
        st.plotly_chart(fig, use_container_width=True)

    with res_col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### 📝 Executive Summary")
        st.write(analysis['summary'])
        st.markdown("</div>", unsafe_allow_html=True)

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
            for strength in analysis['top_strengths']:
                st.markdown(f"<div class='strength-item'>{strength}</div>", unsafe_allow_html=True)
                
        with col_key:
            st.markdown("#### ❌ Missing Keywords & Gaps")
            if analysis['missing_keywords']:
                st.write("Incorporate these missing keywords into your CV content to pass keyword filters:")
                for keyword in analysis['missing_keywords']:
                    st.markdown(f"<span class='keyword-item'>{keyword}</span>", unsafe_allow_html=True)
            else:
                st.success("Awesome! No critical keywords missing from your CV profile.")
                
    with tab2:
        col_ats, col_star = st.columns(2)
        with col_ats:
            st.markdown("#### 📊 ATS Formatting Review")
            st.metric("Structure Score", f"{analysis['formatting_score']}%")
            st.markdown(f"**ATS Compatibility:** {analysis['ats_compatibility']}")
            st.markdown(f"**Structuring Recommendations:** {analysis['formatting_feedback']}")
            
        with col_star:
            st.markdown("#### ✨ STAR Method Efficacy")
            st.write("Evaluating if experience bullets quantify achievements using Situation-Task-Action-Result format:")
            st.info(analysis['star_method_evaluation'])
            
    with tab3:
        st.markdown("#### 🛠 Actionable Profile Roadmap")
        st.write("Apply these specific step-by-step suggestions to enhance the impact and clarity of your CV:")
        for suggestion in analysis['improvement_suggestions']:
            st.markdown(f"<div class='roadmap-item'>• {suggestion}</div>", unsafe_allow_html=True)
            
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
