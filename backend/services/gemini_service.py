import json
from google import genai
from google.genai import types
from backend.config import settings

SYSTEM_INSTRUCTION = (
    "You are an expert ATS (Applicant Tracking System) parser and senior technical "
    "recruiter with 15+ years of experience in talent acquisition. Your task is to "
    "meticulously compare the provided candidate resume against the provided job "
    "description and produce a rigorous, honest, and actionable evaluation.\n\n"
    "You must output ONLY a valid JSON object with EXACTLY the following keys and "
    "value types, and no additional keys or commentary:\n\n"
    "- \"match_score\": An integer between 0 and 100 representing how well the resume "
    "matches the job description (based on skills, experience, keywords, and "
    "qualifications alignment).\n"
    "- \"summary\": A concise 2-sentence summary of the candidate's overall fit for "
    "this specific role.\n"
    "- \"missing_keywords\": A JSON array of strings listing important technical "
    "skills, tools, certifications, or soft skills mentioned in the job description "
    "that are missing or weakly represented in the resume.\n"
    "- \"improvement_bullet_points\": A JSON array of exactly 3 strings, each "
    "describing a specific, actionable improvement the candidate could make to their "
    "resume to better match this job description.\n"
    "- \"cover_letter\": A single string containing a professional, tailored cover "
    "letter of exactly 3 paragraphs. The first paragraph should introduce the "
    "candidate and state the role they are applying for. The second paragraph should "
    "highlight relevant skills and experience that align with the job description. "
    "The third paragraph should express enthusiasm and include a call to action. "
    "Use \\n\\n to separate paragraphs within the string.\n\n"
    "Be precise, objective, and base your evaluation strictly on the content provided. "
    "Do not fabricate candidate experience that is not present in the resume."
)

REQUIRED_KEYS = [
    "match_score",
    "summary",
    "missing_keywords",
    "improvement_bullet_points",
    "cover_letter",
]


def analyze_resume(resume_text: str, jd_text: str) -> dict:
    if not settings.GEMINI_API_KEY:
        raise ValueError("Server is missing a configured Gemini API key.")

    if not resume_text or not resume_text.strip():
        raise ValueError("Resume text is empty. Cannot perform analysis.")

    if not jd_text or not jd_text.strip():
        raise ValueError("Job description text is empty. Cannot perform analysis.")

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    user_prompt = (
        f"JOB DESCRIPTION:\n{jd_text}\n\n"
        f"---\n\n"
        f"CANDIDATE RESUME:\n{resume_text}\n\n"
        f"---\n\n"
        f"Analyze the resume against the job description and return the JSON object "
        f"as instructed in the system prompt."
    )

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            temperature=0.4,
        ),
    )

    raw_text = response.text

    if not raw_text or not raw_text.strip():
        raise ValueError("The Gemini API returned an empty response.")

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse the AI response as valid JSON. Details: {str(e)}")

    missing_required = [key for key in REQUIRED_KEYS if key not in result]
    if missing_required:
        raise ValueError(f"The AI response is missing required fields: {', '.join(missing_required)}")

    try:
        result["match_score"] = max(0, min(100, int(result["match_score"])))
    except (ValueError, TypeError):
        result["match_score"] = 0

    return result
