---
title: AI Resume & Portfolio Analyzer Agent
emoji: 📄
colorFrom: blue
colorTo: indigo
sdk: docker
dockerfile: docker/Dockerfile.backend
app_port: 8000
pinned: false
---

# 📄 AI Resume & Portfolio Analyzer Agent

An AI agent that reads a candidate's resume (PDF), compares it against a target job
description, and returns an ATS-style match score, a fit summary, missing keywords,
concrete improvement suggestions, and a tailored cover letter — powered by Google
Gemini (`gemini-2.5-flash`).

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B)
![License](https://img.shields.io/badge/License-MIT-green)
![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF)

---

## ✨ Features

- **PDF resume parsing** with `pdfplumber`, extracting clean, line-by-line text.
- **AI-powered analysis** using Google Gemini with enforced structured JSON output.
- **ATS match score (0–100)**, a 2-sentence fit summary, missing keyword detection,
  3 actionable resume improvements, and a full 3-paragraph tailored cover letter.
- **Secure by design** — the Gemini API key lives only on the backend server. The
  frontend and browser never see it, which makes this safe to share with a team or
  deploy publicly.
- **Access-code gated** — only people who know your group's shared access code can
  use the tool, preventing quota abuse.
- **Rate limited** per client to protect your API quota.
- **Fully containerized** with Docker and Docker Compose.
- **CI pipeline** with GitHub Actions running automated tests on every push.

---

## 🏗️ Architecture

```
┌──────────────────────┐        HTTPS + X-Access-Code header        ┌───────────────────────┐
│   Streamlit Frontend │ ────────────────────────────────────────▶ │     FastAPI Backend    │
│  (frontend/app.py)   │ ◀──────────────────────────────────────── │   (backend/main.py)   │
│                       │            JSON analysis result           │                        │
│  - Login gate         │                                           │  - Access-code check   │
│  - File upload         │                                          │  - Rate limiting       │
│  - Results UI          │                                          │  - PDF parsing         │
│  - No API key here     │                                          │  - Gemini API call     │
└──────────────────────┘                                           │  - GEMINI_API_KEY held  │
                                                                     │    only here            │
                                                                     └───────────────────────┘
```

The Gemini API key is read from `backend` environment variables / secrets only.
It is never sent to, stored in, or accessible from the frontend, so it cannot leak
through the browser, page source, or shared links — even in a multi-user/team
deployment.

---

## 📁 Project Structure

```
ai-resume-analyzer/
├── backend/
│   ├── main.py                 # FastAPI app, routes, rate limiting, CORS
│   ├── config.py                # Environment/settings loader
│   ├── models.py                 # Pydantic request/response schemas
│   ├── auth.py                    # Access-code verification dependency
│   ├── services/
│   │   ├── pdf_parser.py           # PDF text extraction
│   │   └── gemini_service.py        # Gemini prompt + API call
│   └── requirements.txt
├── frontend/
│   ├── app.py                    # Streamlit UI (calls the backend only)
│   ├── requirements.txt
│   └── .streamlit/config.toml     # Theme
├── tests/
│   ├── test_pdf_parser.py
│   └── test_api.py
├── docker/
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── .github/workflows/ci.yml       # GitHub Actions CI
├── docker-compose.yml
├── .env.example
├── .gitignore
├── LICENSE
├── Makefile
└── README.md
```

---

## 🚀 Getting Started (Local Development)

### Prerequisites
- Python 3.11+
- A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### 1. Clone and configure

```bash
git clone https://github.com/<your-username>/ai-resume-analyzer.git
cd ai-resume-analyzer
cp .env.example .env
```

Edit `.env` and set your real values:

```
GEMINI_API_KEY=your-real-gemini-api-key-here
ACCESS_CODE=choose-a-shared-group-password
```

`.env` is already in `.gitignore` — it will never be committed.

### 2. Run the backend

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API is now live at `http://localhost:8000` (interactive docs at
`http://localhost:8000/docs`).

### 3. Run the frontend (in a second terminal)

```bash
python -m venv venv-frontend
source venv-frontend/bin/activate
pip install -r frontend/requirements.txt
export BACKEND_URL=http://localhost:8000     # Windows: set BACKEND_URL=http://localhost:8000
streamlit run frontend/app.py
```

Open `http://localhost:8501`, enter your group's access code, upload a resume PDF,
paste a job description, and click **Analyze Application**.

---

## 🐳 Run Everything with Docker Compose

```bash
docker compose up --build
```

This starts both services with the environment variables from your `.env` file.
Frontend: `http://localhost:8501` · Backend: `http://localhost:8000`.

---

## ☁️ Deployment

**Backend** — deploy `backend/` to any container host (Render, Railway, Fly.io,
AWS/GCP/Azure). Set `GEMINI_API_KEY`, `ACCESS_CODE`, and the other variables from
`.env.example` as platform secrets/environment variables — never in code.

**Frontend** — deploy `frontend/` to Streamlit Community Cloud or any host. Set a
single secret, `BACKEND_URL`, pointing at your deployed backend's URL. The Gemini
key is never configured on the frontend at all.

---

## 🔌 API Reference

### `GET /api/health`
Returns service status and the active Gemini model.

### `POST /api/analyze`
**Headers:** `X-Access-Code: <group access code>`
**Body (multipart/form-data):**
| Field | Type | Description |
|---|---|---|
| `resume` | file (PDF) | Candidate resume |
| `job_description` | string | Target job description text |

**Response `200`:**
```json
{
  "match_score": 82,
  "summary": "...",
  "missing_keywords": ["Kubernetes", "GraphQL"],
  "improvement_bullet_points": ["...", "...", "..."],
  "cover_letter": "..."
}
```

**Error responses:** `400` invalid input, `401` bad access code, `413` file too
large, `429` rate limit exceeded, `502` upstream AI failure.

---

## 🧪 Running Tests

```bash
pip install -r backend/requirements.txt -r requirements-dev.txt
pytest tests/ -v
```

Tests cover PDF extraction (valid and empty documents) and the API's
authentication, validation, and error-handling behavior. GitHub Actions runs
this suite automatically on every push and pull request to `main`.

---

## 🔐 Security Notes

- The Gemini API key **only** ever exists as a backend environment variable — it
  is never returned in any API response and never shipped to the frontend.
- The shared **access code** gates usage so only your team can call the API.
- **Rate limiting** (`slowapi`) caps requests per client IP to protect your quota.
- `.env` and `.streamlit/secrets.toml` are git-ignored — commit `.env.example`
  only, and configure real secrets through your hosting platform's secrets
  manager.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI, Uvicorn, slowapi |
| Frontend UI | Streamlit |
| AI | Google Gemini (`google-genai`, model `gemini-2.5-flash`) |
| PDF Parsing | pdfplumber |
| Testing | pytest, httpx, reportlab |
| CI/CD | GitHub Actions |
| Containerization | Docker, Docker Compose |

---

## 📜 License

Released under the [MIT License](LICENSE).
