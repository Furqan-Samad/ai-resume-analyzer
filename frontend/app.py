import os
import streamlit as st

from pdf_parser import extract_pdf_text
from gemini_service import analyze_resume

st.set_page_config(
    page_title="AI Resume & Portfolio Analyzer Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)


def get_config(key, default=None):
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, default)


GEMINI_API_KEY = get_config("GEMINI_API_KEY")
ACCESS_CODE = get_config("ACCESS_CODE")
GEMINI_MODEL = get_config("GEMINI_MODEL", "gemini-2.5-flash")

if not GEMINI_API_KEY:
    st.error(
        "⚠️ No Gemini API key is configured on this server. "
        "Add GEMINI_API_KEY under Settings > Secrets on Streamlit Community Cloud, "
        "or to .streamlit/secrets.toml when running locally."
    )
    st.stop()

if not ACCESS_CODE:
    st.error(
        "⚠️ No ACCESS_CODE is configured on this server. "
        "Add ACCESS_CODE under Settings > Secrets on Streamlit Community Cloud, "
        "or to .streamlit/secrets.toml when running locally."
    )
    st.stop()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "analyses_used" not in st.session_state:
    st.session_state.analyses_used = 0

if not st.session_state.authenticated:
    st.title("📄 AI Resume & Portfolio Analyzer Agent")
    st.markdown("This tool is restricted to authorized group members.")
    entered_code = st.text_input("Enter the group access code", type="password")
    if st.button("Unlock", type="primary"):
        if entered_code == ACCESS_CODE:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Incorrect access code.")
    st.stop()

with st.sidebar:
    st.header("⚙️ Session Info")
    st.success("🔒 API key is securely configured on the server.")
    st.caption(f"Analyses used this session: {st.session_state.analyses_used}")
    st.markdown("---")
    if st.button("Log out"):
        st.session_state.authenticated = False
        st.rerun()
    st.markdown("---")
    st.caption("AI Resume & Portfolio Analyzer Agent v1.0")

st.title("📄 AI Resume & Portfolio Analyzer Agent")
st.markdown(
    "Upload a candidate's resume and paste a target job description to get an "
    "instant ATS-style match score, skill gap analysis, and a tailored cover letter."
)
st.markdown("---")

input_col1, input_col2 = st.columns(2)

with input_col1:
    st.subheader("📎 Candidate Resume")
    uploaded_resume = st.file_uploader(
        "Upload resume as PDF",
        type=["pdf"],
        help="Only PDF files are supported."
    )

with input_col2:
    st.subheader("🎯 Target Job Description")
    job_description = st.text_area(
        "Paste the job description here",
        height=280,
        placeholder="Paste the full job description text here..."
    )

st.markdown("---")

analyze_clicked = st.button("🚀 Analyze Application", type="primary", use_container_width=True)

if analyze_clicked:
    if uploaded_resume is None:
        st.error("⚠️ Please upload a candidate resume in PDF format.")
    elif not job_description or not job_description.strip():
        st.error("⚠️ Please paste a job description before analyzing.")
    else:
        try:
            with st.spinner("🔍 Extracting resume content..."):
                resume_text = extract_pdf_text(uploaded_resume.getvalue())

            with st.spinner("🤖 Analyzing application with Gemini AI..."):
                analysis_result = analyze_resume(resume_text, job_description, GEMINI_API_KEY, GEMINI_MODEL)

            st.session_state.analyses_used += 1

            st.success("✅ Analysis complete!")
            st.markdown("---")

            st.subheader("📊 ATS Match Score")
            match_score = analysis_result.get("match_score", 0)

            try:
                match_score = int(match_score)
            except (ValueError, TypeError):
                match_score = 0

            match_score = max(0, min(100, match_score))

            score_col1, score_col2 = st.columns([1, 3])
            with score_col1:
                st.metric(label="Match Score", value=f"{match_score}/100")
            with score_col2:
                st.progress(match_score / 100.0)

            st.markdown("---")

            st.subheader("📝 Candidate Fit Summary")
            st.write(analysis_result.get("summary", "No summary available."))

            st.markdown("---")

            output_col1, output_col2 = st.columns(2)

            with output_col1:
                st.subheader("🔑 Missing Keywords")
                missing_keywords = analysis_result.get("missing_keywords", [])
                if missing_keywords:
                    for keyword in missing_keywords:
                        st.markdown(f"- {keyword}")
                else:
                    st.info("No significant missing keywords identified.")

            with output_col2:
                st.subheader("💡 Improvement Suggestions")
                improvement_points = analysis_result.get("improvement_bullet_points", [])
                if improvement_points:
                    for point in improvement_points:
                        st.markdown(f"- {point}")
                else:
                    st.info("No specific improvement suggestions identified.")

            st.markdown("---")

            st.subheader("✉️ Tailored Cover Letter")
            cover_letter_text = analysis_result.get("cover_letter", "")

            st.text_area(
                "Generated Cover Letter",
                value=cover_letter_text,
                height=350,
                key="cover_letter_output"
            )

            st.download_button(
                label="⬇️ Download Cover Letter",
                data=cover_letter_text,
                file_name="Tailored_Cover_Letter.txt",
                mime="text/plain",
                use_container_width=True
            )

        except ValueError as ve:
            st.error(f"⚠️ {str(ve)}")
        except Exception as e:
            st.error(
                "❌ An unexpected error occurred while processing your request. "
                f"Details: {str(e)}"
            )