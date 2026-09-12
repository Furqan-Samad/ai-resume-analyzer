import os
import streamlit as st
import requests

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


BACKEND_URL = get_config("BACKEND_URL", "http://localhost:8000").rstrip("/")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "access_code" not in st.session_state:
    st.session_state.access_code = ""

if "analyses_used" not in st.session_state:
    st.session_state.analyses_used = 0

if not st.session_state.authenticated:
    st.title("📄 AI Resume & Portfolio Analyzer Agent")
    st.markdown(
        "This tool is restricted to authorized group members. "
        "Enter your group access code to continue."
    )
    entered_code = st.text_input("Group access code", type="password")

    if st.button("Unlock", type="primary"):
        try:
            check = requests.get(f"{BACKEND_URL}/api/health", timeout=10)
            check.raise_for_status()
        except requests.exceptions.RequestException:
            st.error("⚠️ Could not reach the backend service. Please try again later.")
            st.stop()

        st.session_state.access_code = entered_code
        st.session_state.authenticated = True
        st.rerun()

    st.stop()

with st.sidebar:
    st.header("⚙️ Session Info")
    st.success("🔒 Connected to a secured backend. The API key never touches this app.")
    st.caption(f"Analyses this session: {st.session_state.analyses_used}")
    st.markdown("---")
    if st.button("Log out"):
        st.session_state.authenticated = False
        st.session_state.access_code = ""
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
            with st.spinner("🤖 Analyzing application..."):
                files = {
                    "resume": (
                        uploaded_resume.name,
                        uploaded_resume.getvalue(),
                        "application/pdf",
                    )
                }
                data = {"job_description": job_description}
                headers = {"X-Access-Code": st.session_state.access_code}

                response = requests.post(
                    f"{BACKEND_URL}/api/analyze",
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=120,
                )

            if response.status_code == 401:
                st.error("❌ Your access code was rejected by the server. Please log out and try again.")
            elif response.status_code == 429:
                st.error("⏳ Rate limit reached. Please wait a while before trying again.")
            elif response.status_code >= 400:
                try:
                    detail = response.json().get("detail", response.text)
                except ValueError:
                    detail = response.text
                st.error(f"⚠️ {detail}")
            else:
                analysis_result = response.json()
                st.session_state.analyses_used += 1

                st.success("✅ Analysis complete!")
                st.markdown("---")

                st.subheader("📊 ATS Match Score")
                match_score = int(analysis_result.get("match_score", 0))
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
                    use_container_width=True,
                )

        except requests.exceptions.Timeout:
            st.error("⏳ The request timed out. Please try again.")
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Could not reach the backend service: {str(e)}")
