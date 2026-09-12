from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.config import settings
from backend.auth import verify_access_code
from backend.models import AnalyzeResponse, HealthResponse
from backend.services.pdf_parser import extract_pdf_text
from backend.services.gemini_service import analyze_resume

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="AI Resume & Portfolio Analyzer Agent API",
    description="Backend API that parses resumes and scores them against a job description using Google Gemini.",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    return HealthResponse(status="ok", model=settings.GEMINI_MODEL)


@app.post("/api/analyze", response_model=AnalyzeResponse, tags=["Analysis"])
@limiter.limit(settings.RATE_LIMIT)
async def analyze(
    request: Request,
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    access_code: str = Depends(verify_access_code),
):
    if resume.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted for the resume upload.",
        )

    file_bytes = await resume.read()

    max_bytes = settings.MAX_PDF_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"PDF exceeds the {settings.MAX_PDF_SIZE_MB} MB size limit.",
        )

    if not job_description or not job_description.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description text is required.",
        )

    try:
        resume_text = extract_pdf_text(file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    try:
        result = analyze_resume(resume_text, job_description)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"The AI service failed to complete the analysis: {str(e)}",
        )

    return AnalyzeResponse(**result)
