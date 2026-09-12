"""
app.py - AI Resume & Portfolio Analyzer Agent (Cyber Command Center Edition)
A futuristic, highly animated developer command center that extracts, analyzes,
and evaluates candidate resumes and portfolios against target job descriptions.

Features:
- Futuristic HUD & Top Control Toolbar: Zero scrolling friction; instant mode switching.
- Dual Persona: Candidate Mode (Single Dossier) & Recruiter Mode (Batch Leaderboard).
- Side-by-Side Holographic Dropzones: Neon dashed borders and live status indicators.
- Heavy CSS Animations: Keyframes (cyberpunkGlow, floatCard, neonPulse, slideUp, radarSweep).
- High-Contrast Obsidian Palette: #05070f base accented with #8b5cf6, #06b6d4, and #10b981.
- Visual Resume Previews: High-res PDF thumbnail rendering via PyMuPDF (fitz).
- Dual-Engine Parsing: Primary pdfplumber with PyPDF2 fallback & python-docx support.
- Granular ATS Scoring: Hard Skills, Keyword Density & Relevancy, Document Formatting.
- Visual Sub-Score Chart: Altair graphical breakdown with dark-mode cyberpunk styling.
- Official Gemini API Integration: google-genai SDK for live deep evaluation and chat.
- Interactive Mock Interview Simulator: Live Q&A, STAR grading, and tailored follow-ups.
- Multi-Format Diagnostic Reports: Downloadable Markdown (.md) and Publication-Grade PDF (ReportLab).
- Instant Reset & Session Reboot: Clear state & re-upload without browser reloads.
"""

from __future__ import annotations

import datetime
import io
import json
import re
import time
from typing import Dict, List, Optional, Set, Tuple

import altair as alt
import pandas as pd
import streamlit as st

# Optional / Official Gemini SDK
try:
    from google import genai
    from google.genai.errors import APIError, ClientError
    _HAS_GOOGLE_GENAI = True
except ImportError:
    genai = None
    _HAS_GOOGLE_GENAI = False

# PyMuPDF for High-Quality Visual Resume Page Thumbnails
try:
    import pymupdf as fitz
    _HAS_PYMUPDF = True
except ImportError:
    try:
        import fitz
        _HAS_PYMUPDF = True
    except ImportError:
        fitz = None
        _HAS_PYMUPDF = False

# ReportLab for Professional PDF Generation
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    _HAS_REPORTLAB = True
except ImportError:
    _HAS_REPORTLAB = False

# Import the robust text parser module
from parser import extract_text_from_file, clean_text, ParseResult


# ==============================================================================
# 1. Page Configuration & Futuristic Cyberpunk Design System
# ==============================================================================

st.set_page_config(
    page_title="CYBER-ATS // Resume Intelligence Command Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root {
    --bg-obsidian: #05070f;
    --surface-dark: #090d1a;
    --card-surface: rgba(14, 20, 39, 0.75);
    --card-border: rgba(139, 92, 246, 0.28);
    --border-glow: rgba(6, 182, 212, 0.4);
    --primary-violet: #8b5cf6;
    --primary-cyan: #06b6d4;
    --primary-emerald: #10b981;
    --primary-rose: #f43f5e;
    --primary-amber: #f59e0b;
    --neon-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%);
    --neon-gradient-rev: linear-gradient(135deg, #06b6d4 0%, #8b5cf6 50%, #d946ef 100%);
    --text-primary: #f8fafc;
    --text-muted: #94a3b8;
}

/* Base Body & App Background */
.stApp {
    background: radial-gradient(circle at 50% -10%, #0e1633 0%, #05070f 65%, #020307 100%) !important;
    color: var(--text-primary);
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Keyframe Animations */
@keyframes slideUp {
    from {
        opacity: 0;
        transform: translateY(18px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes cyberpunkGlow {
    0%, 100% {
        box-shadow: 0 0 15px rgba(139, 92, 246, 0.25), 0 0 35px rgba(6, 182, 212, 0.15), inset 0 0 15px rgba(139, 92, 246, 0.1);
    }
    50% {
        box-shadow: 0 0 28px rgba(139, 92, 246, 0.45), 0 0 50px rgba(6, 182, 212, 0.28), inset 0 0 22px rgba(6, 182, 212, 0.15);
    }
}

@keyframes floatCard {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-4px); }
}

@keyframes neonPulse {
    0% {
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.85);
    }
    70% {
        box-shadow: 0 0 0 9px rgba(16, 185, 129, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
    }
}

@keyframes borderFlow {
    0% { border-color: rgba(139, 92, 246, 0.45); }
    50% { border-color: rgba(6, 182, 212, 0.7); }
    100% { border-color: rgba(139, 92, 246, 0.45); }
}

@keyframes laserShimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(200%); }
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Typography Hierarchy */
h1, h2, h3, h4 {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.025em;
    color: #f8fafc;
}

code, pre, .mono-font {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Top Futuristic HUD Header */
/* Top Futuristic HUD Header */
.cyber-hud-header {
    background: rgba(20, 25, 45, 0.45) !important;
    backdrop-filter: blur(28px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
    border: 0.5px solid rgba(255, 255, 255, 0.14) !important;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.18) !important;
    border-radius: 24px !important;
    padding: 1.4rem 1.8rem;
    margin-bottom: 0px !important;
    position: relative;
    overflow: hidden;
    animation: slideUp 0.45s cubic-bezier(0.16, 1, 0.3, 1);
}

.cyber-hud-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #6366f1, #06b6d4, #10b981, #d946ef);
}

.hud-tag {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 14px;
    border-radius: 9999px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    background: rgba(139, 92, 246, 0.18);
    border: 0.5px solid rgba(139, 92, 246, 0.45);
    color: #c4b5fd;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12);
}

.hud-live-pill {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 5px 14px;
    border-radius: 9999px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    background: rgba(16, 185, 129, 0.16);
    border: 0.5px solid rgba(16, 185, 129, 0.45);
    color: #34d399;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12);
}

.hud-live-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background-color: #10b981;
    animation: neonPulse 2s infinite;
}

.cyber-title {
    font-size: 2.25rem;
    font-weight: 800;
    margin: 0.4rem 0 0.2rem 0;
    background: linear-gradient(135deg, #ffffff 15%, #cbd5e1 55%, #94a3b8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.03em;
}

.cyber-subtitle {
    color: var(--text-muted);
    font-size: 0.95rem;
    max-width: 680px;
    line-height: 1.45;
}

/* Command Deck Top Control Bar */
.command-deck-container {
    background: rgba(20, 25, 45, 0.45) !important;
    backdrop-filter: blur(28px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
    border: 0.5px solid rgba(255, 255, 255, 0.14) !important;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.18) !important;
    border-radius: 22px !important;
    padding: 1.15rem 1.5rem;
    margin-top: 0.35rem !important;
    margin-bottom: 1.25rem !important;
    animation: slideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

.hud-label {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.09em !important;
    color: #38bdf8 !important; /* Crisp high-contrast neon cyan */
    text-shadow: 0 0 12px rgba(56, 189, 248, 0.4) !important;
    margin-bottom: 0.45rem !important;
    display: block !important;
    text-transform: uppercase !important;
}

/* Holographic Dropzone & Input Bay Cards */
.holographic-dropzone {
    background: rgba(20, 25, 45, 0.45) !important;
    backdrop-filter: blur(28px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
    border: 0.5px dashed rgba(139, 92, 246, 0.5) !important;
    border-radius: 22px !important;
    padding: 1.35rem 1.45rem;
    position: relative;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.18) !important;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    animation: slideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

.holographic-dropzone:hover {
    border-color: rgba(56, 189, 248, 0.7) !important;
    transform: translateY(-3px);
    box-shadow: 0 24px 48px rgba(0, 0, 0, 0.6), 0 0 25px rgba(139, 92, 246, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.28) !important;
}

.bay-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.85rem;
}

.bay-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.08rem;
    font-weight: 700;
    color: #f1f5f9;
    display: flex;
    align-items: center;
    gap: 8px;
}

.bay-status {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 9999px;
    background: rgba(6, 182, 212, 0.18);
    border: 0.5px solid rgba(6, 182, 212, 0.45);
    color: #22d3ee;
    text-transform: uppercase;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

/* Metric Cards with Glowing Border and Hover Elevation */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1.25rem;
    margin-bottom: 1.75rem;
}

@media (max-width: 960px) {
    .metric-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

.custom-card {
    background: rgba(20, 25, 45, 0.45) !important;
    backdrop-filter: blur(28px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
    border: 0.5px solid rgba(255, 255, 255, 0.14) !important;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.18) !important;
    border-radius: 22px !important;
    padding: 1.4rem 1.3rem;
    position: relative;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    animation: slideUp 0.45s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

.custom-card:hover {
    transform: translateY(-4px) scale(1.01);
    border-color: rgba(56, 189, 248, 0.55) !important;
    box-shadow: 0 24px 48px rgba(0, 0, 0, 0.6), 0 0 25px rgba(139, 92, 246, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.28) !important;
}

.card-top-bar {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
}

.top-bar-primary { background: var(--neon-gradient); }
.top-bar-emerald { background: linear-gradient(90deg, #10b981, #06b6d4); }
.top-bar-cyan { background: linear-gradient(90deg, #06b6d4, #3b82f6); }
.top-bar-amber { background: linear-gradient(90deg, #f59e0b, #ef4444); }

.card-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #38bdf8 !important; /* High-contrast neon cyan sub-label */
    text-shadow: 0 0 10px rgba(56, 189, 248, 0.35);
    font-weight: 700;
    margin-bottom: 0.35rem;
}

.card-value {
    font-family: 'Outfit', sans-serif;
    font-size: 2.25rem;
    font-weight: 800;
    color: #ffffff;
    line-height: 1.1;
    margin-bottom: 0.25rem;
    letter-spacing: -0.02em;
}

.card-caption {
    font-size: 0.8rem;
    color: #f8fafc !important; /* Crisp white */
    opacity: 0.85;
}

/* Progress Cards with Laser Shimmer */
.progress-card {
    background: rgba(20, 25, 45, 0.45) !important;
    backdrop-filter: blur(28px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
    border: 0.5px solid rgba(255, 255, 255, 0.14) !important;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.18) !important;
    border-radius: 20px !important;
    padding: 1.15rem 1.3rem;
    margin-bottom: 0.85rem;
    transition: all 0.3s ease;
    animation: slideUp 0.45s ease-out;
}

.progress-card:hover {
    border-color: rgba(56, 189, 248, 0.6) !important;
    transform: translateY(-2px);
    box-shadow: 0 24px 48px rgba(0, 0, 0, 0.6), 0 0 20px rgba(139, 92, 246, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.25) !important;
}

.progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}

.progress-title {
    font-size: 0.94rem;
    font-weight: 600;
    color: #f1f5f9;
    display: flex;
    align-items: center;
    gap: 8px;
}

.progress-pct {
    font-family: 'Outfit', sans-serif;
    font-size: 1.18rem;
    font-weight: 800;
}

.progress-bar-bg {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 9999px;
    height: 10px;
    width: 100%;
    overflow: hidden;
    position: relative;
    border: 0.5px solid rgba(255, 255, 255, 0.1);
}

.progress-bar-fill {
    height: 100%;
    border-radius: 9999px;
    transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.progress-bar-fill::after {
    content: '';
    position: absolute;
    top: 0; left: 0; bottom: 0;
    width: 60px;
    background: linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.45) 50%, rgba(255,255,255,0) 100%);
    animation: laserShimmer 2.2s infinite;
}

/* Keyword Badges */
.badge-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 0.85rem 0;
}

.badge-tag {
    padding: 6px 14px;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.badge-tag:hover {
    transform: translateY(-2px) scale(1.05);
}

.badge-matched {
    background: rgba(16, 185, 129, 0.16);
    border: 0.5px solid rgba(16, 185, 129, 0.5);
    color: #34d399;
    box-shadow: 0 2px 12px rgba(16, 185, 129, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.badge-missing {
    background: rgba(244, 63, 94, 0.16);
    border: 0.5px solid rgba(244, 63, 94, 0.5);
    color: #fb7185;
    box-shadow: 0 2px 12px rgba(244, 63, 94, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

/* Feedback & Insights Cards */
.insight-card {
    background: rgba(20, 25, 45, 0.45) !important;
    backdrop-filter: blur(28px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
    border: 0.5px solid rgba(255, 255, 255, 0.14) !important;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.18) !important;
    border-radius: 20px;
    padding: 1.35rem;
    margin-bottom: 1rem;
    transition: all 0.3s ease;
    animation: slideUp 0.45s ease-out;
}

.insight-card:hover {
    transform: translateY(-3px);
    border-color: rgba(56, 189, 248, 0.55) !important;
    box-shadow: 0 24px 48px rgba(0, 0, 0, 0.6), 0 0 20px rgba(139, 92, 246, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.25) !important;
}

.insight-header {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 1.08rem;
    font-weight: 700;
    color: #f8fafc;
    margin-bottom: 0.8rem;
}

/* iOS-Style Liquid Glassmorphism Buttons (Global Pill Design) */
button,
button[data-testid*="baseButton"],
button[data-testid*="stBaseButton"],
div.stButton button,
div.stDownloadButton button,
.stButton > button,
.stDownloadButton > button {
    background: rgba(22, 30, 58, 0.65) !important;
    background-color: rgba(22, 30, 58, 0.65) !important;
    backdrop-filter: blur(20px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
    border: 0.5px solid rgba(255, 255, 255, 0.18) !important;
    color: #ffffff !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important;
    border-radius: 9999px !important; /* Apple Pill Shape */
    padding: 0.65rem 1.5rem !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.25) !important;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

button:hover,
button[data-testid*="baseButton"]:hover,
button[data-testid*="stBaseButton"]:hover,
div.stButton button:hover,
div.stDownloadButton button:hover,
.stButton > button:hover,
.stDownloadButton > button:hover {
    background: rgba(32, 44, 82, 0.8) !important;
    background-color: rgba(32, 44, 82, 0.8) !important;
    border-color: rgba(56, 189, 248, 0.7) !important;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.55), 0 0 20px rgba(56, 189, 248, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.45) !important;
    transform: translateY(-2px) !important;
    color: #ffffff !important;
}

button *,
button[data-testid*="baseButton"] *,
button[data-testid*="stBaseButton"] *,
div.stButton button *,
div.stDownloadButton button *,
.stButton > button *,
.stDownloadButton > button * {
    color: #ffffff !important;
    font-weight: 700 !important;
}

/* Eliminate Dead Space between Hero Header and Command Deck */
div[data-testid="stHorizontalBlock"]:has(.cyber-hud-header) {
    margin-bottom: 0px !important;
    padding-bottom: 0px !important;
}

div:has(> .command-deck-container) {
    margin-top: -12px !important;
    padding-top: 0px !important;
}

/* Top HUD Column 2 Container (Apple Liquid Glass Pill Container) */
div[data-testid="stHorizontalBlock"]:has(.cyber-hud-header) > div[data-testid="stColumn"]:nth-child(2) {
    background: rgba(20, 25, 45, 0.45) !important;
    border: 0.5px solid rgba(255, 255, 255, 0.14) !important;
    border-radius: 24px !important;
    padding: 1.2rem 1.1rem !important;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.18) !important;
    backdrop-filter: blur(28px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    text-align: center !important;
    transition: all 0.3s ease !important;
}

div[data-testid="stHorizontalBlock"]:has(.cyber-hud-header) > div[data-testid="stColumn"]:nth-child(2):hover {
    border-color: rgba(56, 189, 248, 0.6) !important;
    box-shadow: 0 24px 48px rgba(0, 0, 0, 0.6), 0 0 25px rgba(139, 92, 246, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.28) !important;
}

div[data-testid="stHorizontalBlock"]:has(.cyber-hud-header) > div[data-testid="stColumn"]:nth-child(2) button,
div[data-testid="stHorizontalBlock"]:has(.cyber-hud-header) > div[data-testid="stColumn"]:nth-child(2) [data-testid*="baseButton"] {
    background: rgba(26, 36, 70, 0.8) !important;
    background-color: rgba(26, 36, 70, 0.8) !important;
    border: 0.5px solid rgba(255, 255, 255, 0.25) !important;
    color: #ffffff !important;
    border-radius: 9999px !important;
    padding: 0.65rem 1.5rem !important;
    font-size: 0.88rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.04em !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.35) !important;
}

div[data-testid="stHorizontalBlock"]:has(.cyber-hud-header) > div[data-testid="stColumn"]:nth-child(2) button:hover,
div[data-testid="stHorizontalBlock"]:has(.cyber-hud-header) > div[data-testid="stColumn"]:nth-child(2) [data-testid*="baseButton"]:hover {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.6) 0%, rgba(6, 182, 212, 0.6) 100%) !important;
    background-color: rgba(139, 92, 246, 0.6) !important;
    border-color: rgba(56, 189, 248, 0.85) !important;
    box-shadow: 0 0 25px rgba(6, 182, 212, 0.5), 0 0 35px rgba(139, 92, 246, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.5) !important;
    transform: translateY(-2px) scale(1.02) !important;
    color: #ffffff !important;
}

div[data-testid="stHorizontalBlock"]:has(.cyber-hud-header) > div[data-testid="stColumn"]:nth-child(2) button * {
    color: #ffffff !important;
    font-weight: 800 !important;
}

/* Preset & Clear Buttons in Ingestion Bay B */
.preset-buttons div.stButton > button {
    background: rgba(22, 32, 60, 0.7) !important;
    border: 0.5px solid rgba(255, 255, 255, 0.18) !important;
    color: #ffffff !important;
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    padding: 0.45rem 1rem !important;
    border-radius: 9999px !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.22) !important;
}

.preset-buttons div.stButton > button:hover {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.5) 0%, rgba(6, 182, 212, 0.5) 100%) !important;
    border-color: rgba(56, 189, 248, 0.85) !important;
    box-shadow: 0 0 18px rgba(6, 182, 212, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.4) !important;
    color: #ffffff !important;
    transform: translateY(-1px) !important;
}

/* Primary Action Buttons (Launch Deck - Liquid Apple Pill) */
.launch-deck div.stButton > button {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.9) 0%, rgba(139, 92, 246, 0.9) 50%, rgba(6, 182, 212, 0.9) 100%) !important;
    background-size: 200% 200% !important;
    border: 0.5px solid rgba(255, 255, 255, 0.35) !important;
    color: #ffffff !important;
    font-size: 1.05rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.04em !important;
    border-radius: 9999px !important; /* Liquid Glass Pill */
    padding: 0.85rem 2.2rem !important;
    box-shadow: 0 12px 35px rgba(139, 92, 246, 0.55), inset 0 1px 0 rgba(255, 255, 255, 0.4) !important;
    animation: gradientShift 6s ease infinite !important;
}

.launch-deck div.stButton > button:hover {
    box-shadow: 0 16px 45px rgba(6, 182, 212, 0.7), 0 0 30px rgba(139, 92, 246, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.55) !important;
    transform: translateY(-3px) scale(1.02) !important;
    color: #ffffff !important;
}

/* Floating Pill Tabs Styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    background: rgba(20, 25, 45, 0.45) !important;
    padding: 8px;
    border-radius: 9999px !important;
    border: 0.5px solid rgba(255, 255, 255, 0.14) !important;
    backdrop-filter: blur(28px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.18) !important;
}

.stTabs [data-baseweb="tab"] {
    height: 48px;
    border-radius: 9999px !important;
    color: #94a3b8;
    font-weight: 600;
    font-size: 0.95rem;
    padding: 0 22px;
    transition: all 0.25s ease;
    border: 1px solid transparent;
}

.stTabs [data-baseweb="tab"]:hover {
    color: #f1f5f9;
    background: rgba(255, 255, 255, 0.08);
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.4) 0%, rgba(6, 182, 212, 0.35) 100%) !important;
    color: #ffffff !important;
    border: 0.5px solid rgba(255, 255, 255, 0.25) !important;
    box-shadow: 0 4px 20px rgba(139, 92, 246, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
}

/* Tab Panels Entrance Animation */
[data-baseweb="tab-panel"] {
    animation: slideUp 0.45s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

/* Chat Message Styling */
[data-testid="stChatMessage"] {
    background: rgba(20, 25, 45, 0.45) !important;
    backdrop-filter: blur(28px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
    border: 0.5px solid rgba(255, 255, 255, 0.14) !important;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.18) !important;
    border-radius: 20px !important;
    margin-bottom: 0.85rem !important;
    animation: slideUp 0.35s ease-out;
}

/* Holographic Thumbnail Container */
.thumbnail-container {
    background: rgba(20, 25, 45, 0.45) !important;
    backdrop-filter: blur(28px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
    border: 0.5px solid rgba(56, 189, 248, 0.4) !important;
    border-radius: 22px !important;
    padding: 14px;
    text-align: center;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.18) !important;
    transition: all 0.3s ease;
    animation: slideUp 0.45s ease-out;
}

.thumbnail-container:hover {
    border-color: rgba(139, 92, 246, 0.6) !important;
    box-shadow: 0 24px 48px rgba(0, 0, 0, 0.6), 0 0 35px rgba(139, 92, 246, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
}

/* Modern File Uploader Integration */
[data-testid="stFileUploader"] {
    background: rgba(20, 25, 45, 0.35);
    border: 0.5px dashed rgba(139, 92, 246, 0.45);
    border-radius: 18px;
    padding: 10px;
    transition: all 0.3s ease;
}

[data-testid="stFileUploader"]:hover {
    border-color: rgba(56, 189, 248, 0.7);
    box-shadow: 0 0 20px rgba(6, 182, 212, 0.25);
}

/* Textarea and Text Inputs */
.stTextArea textarea, .stTextInput input {
    background: rgba(16, 20, 38, 0.65) !important;
    border: 0.5px solid rgba(255, 255, 255, 0.14) !important;
    border-radius: 16px !important;
    color: #f1f5f9 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
    transition: all 0.25s ease !important;
}

.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: rgba(56, 189, 248, 0.7) !important;
    box-shadow: 0 0 0 2px rgba(6, 182, 212, 0.3) !important;
}

/* Streamlit Horizontal Radio Buttons styled as glowing pills */
div[role="radiogroup"] {
    gap: 8px !important;
}

div[role="radiogroup"] > label span,
div[role="radiogroup"] > label p,
.stSelectbox label p,
.stCheckbox label p,
.stCheckbox label span {
    color: #f8fafc !important;
    font-weight: 700 !important;
}

div[role="radiogroup"] > label {
    background: rgba(20, 25, 45, 0.5) !important;
    border: 0.5px solid rgba(255, 255, 255, 0.14) !important;
    padding: 7px 16px !important;
    border-radius: 9999px !important; /* Apple Pill Radio */
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12) !important;
    transition: all 0.25s ease !important;
}

div[role="radiogroup"] > label:hover {
    border-color: rgba(56, 189, 248, 0.7) !important;
    background: rgba(30, 40, 75, 0.7) !important;
    box-shadow: 0 0 15px rgba(56, 189, 248, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
}

/* Sidebar Liquid Glassmorphism */
section[data-testid="stSidebar"] {
    background: rgba(10, 14, 28, 0.75) !important;
    backdrop-filter: blur(28px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
    border-right: 0.5px solid rgba(255, 255, 255, 0.14) !important;
}

/* ==============================================================================
   Concept 1: The Apple-Style Minimalist Pulse Boot Screen
   ============================================================================== */
@keyframes appleDissolve {
    0% { opacity: 0; }
    18% { opacity: 1; }
    80% { opacity: 1; transform: scale(1); }
    100% { opacity: 0; transform: scale(1.02); }
}

@keyframes orbPulse {
    0% { 
        transform: scale(0.82); 
        box-shadow: 0 0 25px rgba(99, 102, 241, 0.45), 0 0 50px rgba(236, 72, 153, 0.3); 
    }
    50% { 
        transform: scale(1.08); 
        box-shadow: 0 0 55px rgba(99, 102, 241, 0.85), 0 0 100px rgba(236, 72, 153, 0.65), inset 0 0 20px rgba(255, 255, 255, 0.6); 
    }
    100% { 
        transform: scale(1.0); 
        box-shadow: 0 0 35px rgba(99, 102, 241, 0.65), 0 0 75px rgba(236, 72, 153, 0.45), inset 0 0 15px rgba(255, 255, 255, 0.45); 
    }
}

@keyframes titleFadeUp {
    0% { opacity: 0; transform: translateY(14px); letter-spacing: 0.18em; }
    40% { opacity: 0.4; }
    100% { opacity: 1; transform: translateY(0px); letter-spacing: 0.32em; }
}

.apple-boot-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: radial-gradient(circle at 50% 50%, #0d1329 0%, #05070f 65%, #020308 100%);
    z-index: 99999999;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    animation: appleDissolve 1.1s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    pointer-events: all;
}

.apple-pulse-orb {
    width: 78px;
    height: 78px;
    border-radius: 50%;
    background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
    animation: orbPulse 1.1s cubic-bezier(0.4, 0, 0.2, 1) forwards;
    position: relative;
}

.apple-pulse-orb::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0) 75%);
    filter: blur(4px);
    opacity: 0.8;
}

.apple-boot-title {
    font-family: 'JetBrains Mono', -apple-system, BlinkMacSystemFont, monospace;
    font-size: 1.15rem;
    font-weight: 700;
    color: #f8fafc;
    text-shadow: 0 0 25px rgba(255, 255, 255, 0.45);
    margin-top: 2.2rem;
    animation: titleFadeUp 1.0s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ==============================================================================
# 2. Session State Management & Instant Reboot Logic
# ==============================================================================

if "boot_intro_played" not in st.session_state:
    st.session_state["boot_intro_played"] = False

if not st.session_state.get("boot_intro_played", False):
    boot_placeholder = st.empty()
    boot_html = """
    <div class="apple-boot-overlay">
        <div class="apple-pulse-orb"></div>
        <div class="apple-boot-title">CYBER // ATS</div>
    </div>
    """
    boot_placeholder.markdown(boot_html, unsafe_allow_html=True)
    time.sleep(1.1)
    st.session_state["boot_intro_played"] = True
    boot_placeholder.empty()
    st.rerun()

if "app_persona" not in st.session_state:
    st.session_state["app_persona"] = "👤 Candidate Dossier"
if "parsed_result" not in st.session_state:
    st.session_state["parsed_result"] = None
if "analysis_data" not in st.session_state:
    st.session_state["analysis_data"] = None
if "batch_results" not in st.session_state:
    st.session_state["batch_results"] = []
if "pdf_thumbnail" not in st.session_state:
    st.session_state["pdf_thumbnail"] = None
if "job_description" not in st.session_state:
    st.session_state["job_description"] = ""
if "cover_letter_draft" not in st.session_state:
    st.session_state["cover_letter_draft"] = ""
if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0
if "model_choice" not in st.session_state:
    st.session_state["model_choice"] = "⚡ Fast Heuristic"
if "api_key" not in st.session_state:
    st.session_state["api_key"] = ""
if "role_seniority" not in st.session_state:
    st.session_state["role_seniority"] = "Senior / Lead"
if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []
if "mock_interview_history" not in st.session_state:
    st.session_state["mock_interview_history"] = []
if "mock_question_index" not in st.session_state:
    st.session_state["mock_question_index"] = 0


def reset_session_state():
    """Clears all session variables to enable instant fresh analysis without browser reload."""
    st.session_state["parsed_result"] = None
    st.session_state["analysis_data"] = None
    st.session_state["batch_results"] = []
    st.session_state["pdf_thumbnail"] = None
    st.session_state["job_description"] = ""
    st.session_state["cover_letter_draft"] = ""
    st.session_state["chat_messages"] = []
    st.session_state["mock_interview_history"] = []
    st.session_state["mock_question_index"] = 0
    st.session_state["uploader_key"] += 1
    st.session_state["boot_intro_played"] = True
    st.toast("System reboot complete. Memory cleared & ready for new payload!", icon="🔄")


# Sample Job Specifications for quick testing
SAMPLE_SPECS = {
    "Staff AI Engineer": (
        "Role: Staff AI / Machine Learning Engineer\n"
        "Requirements:\n"
        "- 6+ years building and scaling production machine learning systems.\n"
        "- Advanced expertise in Python, PyTorch, LLMs, NLP, and Prompt Engineering.\n"
        "- Deep hands-on experience with Docker, Kubernetes, AWS, and Microservices.\n"
        "- Proven track record leading System Design, CI/CD, and agile engineering workflows."
    ),
    "Senior Fullstack Lead": (
        "Role: Senior Fullstack Software Engineer\n"
        "Requirements:\n"
        "- Proficiency in Python, TypeScript, React, Node.js, and FastAPI.\n"
        "- Production experience with PostgreSQL, Redis, REST API, GraphQL, and Git.\n"
        "- Cloud deployment on AWS / GCP using Docker and Terraform.\n"
        "- Strong background in unit testing, microservice architecture, and technical leadership."
    )
}


# ==============================================================================
# 3. Visual Resume Thumbnail Generator (PyMuPDF / fitz)
# ==============================================================================

def render_pdf_thumbnail(pdf_bytes: bytes, dpi: int = 140) -> Optional[bytes]:
    """
    Renders the first page of a PDF document as a crisp PNG image thumbnail in memory.
    Uses PyMuPDF (fitz) for high-performance vector-to-raster conversion.
    """
    if not _HAS_PYMUPDF or not pdf_bytes:
        return None
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if len(doc) > 0:
            page = doc[0]
            pix = page.get_pixmap(dpi=dpi)
            return pix.tobytes("png")
    except Exception:
        return None
    return None


# ==============================================================================
# 4. Resume Evaluation & Keyword Extraction Engine
# ==============================================================================

COMMON_KEYWORDS_CATALOG = {
    "Python", "SQL", "JavaScript", "TypeScript", "React", "Node.js", "Java", "C++",
    "Go", "Rust", "Docker", "Kubernetes", "AWS", "Azure", "GCP", "FastAPI",
    "Django", "Flask", "PostgreSQL", "MongoDB", "Redis", "Kafka", "REST API",
    "GraphQL", "CI/CD", "Git", "Machine Learning", "Deep Learning", "NLP", "LLM",
    "PyTorch", "TensorFlow", "Pandas", "Scikit-Learn", "Agile", "Scrum",
    "System Design", "Microservices", "Terraform", "Linux", "DevOps", "Cybersecurity",
    "Data Engineering", "ETL", "Tableau", "PowerBI", "Product Management",
    "Leadership", "Mentorship", "Unit Testing", "TDD", "Prompt Engineering"
}


def extract_keywords_from_text(text: str) -> Set[str]:
    """Extracts known industry skills and keywords present in text."""
    found = set()
    lowered = text.lower()
    for kw in COMMON_KEYWORDS_CATALOG:
        pattern = r"\b" + re.escape(kw.lower()) + r"\b"
        if re.search(pattern, lowered):
            found.add(kw)
    return found


def call_official_gemini_api(
    api_key: str,
    resume_text: str,
    job_desc: str,
    role_seniority: str
) -> Optional[Dict]:
    """
    Invokes the official Google GenAI SDK (google-genai) to perform live ATS evaluation.
    """
    if not _HAS_GOOGLE_GENAI or not api_key or not api_key.strip():
        return None

    system_instruction = (
        "You are an expert executive resume reviewer and ATS system auditor. "
        "Analyze the provided resume against the target job description. "
        "Return ONLY a valid, raw JSON object (no markdown quotes, no triple backticks) matching this structure:\n"
        "{\n"
        '  "ats_score": <int 0-100>,\n'
        '  "hard_skills_score": <int 0-100>,\n'
        '  "keyword_density_score": <int 0-100>,\n'
        '  "formatting_score": <int 0-100>,\n'
        '  "matched_keywords": [<str>, ...],\n'
        '  "missing_keywords": [<str>, ...],\n'
        '  "strengths": [<str>, ...],\n'
        '  "improvements": [<str>, ...],\n'
        '  "cover_letter": "<str>"\n'
        "}"
    )

    user_prompt = f"Target Seniority: {role_seniority}\n\nJob Description:\n{job_desc[:3000]}\n\nResume Text:\n{resume_text[:4000]}"

    try:
        client = genai.Client(api_key=api_key.strip())
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{system_instruction}\n\n{user_prompt}"
        )
        if response and response.text:
            raw_text = response.text.strip()
            clean_json = re.sub(r"^```(json)?|```$", "", raw_text, flags=re.MULTILINE).strip()
            return json.loads(clean_json)
    except Exception:
        pass

    return None


def call_official_gemini_chat(
    api_key: str,
    resume_text: str,
    job_desc: str,
    chat_history: List[Dict[str, str]],
    user_prompt: str,
    is_mock_interview: bool = False
) -> Optional[str]:
    """
    Invokes official google-genai SDK for interactive conversational Q&A or mock interviews.
    """
    if not _HAS_GOOGLE_GENAI or not api_key or not api_key.strip():
        return None

    if is_mock_interview:
        system_instruction = (
            "You are an executive hiring manager and technical interviewer conducting a live mock interview. "
            "Evaluate the candidate's response to your previous question based on their resume and the job description. "
            "Provide: 1. A score out of 10. 2. What went well (STAR framework). 3. What to improve. 4. An exemplary response. "
            "5. Then ask the NEXT challenging technical or behavioral question."
        )
    else:
        system_instruction = (
            "You are an elite career strategist and technical recruiter. "
            "You have full context of the candidate's resume and their target job description. "
            "Provide direct, high-impact, actionable answers to their questions, such as "
            "rewriting resume bullets, proposing interview questions, or addressing skill gaps."
        )

    conversation_context = f"Candidate Resume:\n{resume_text[:3500]}\n\nTarget Job Description:\n{job_desc[:2500]}\n\nUser Input:\n{user_prompt}"

    try:
        client = genai.Client(api_key=api_key.strip())
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{system_instruction}\n\n{conversation_context}"
        )
        if response and response.text:
            return response.text.strip()
    except Exception:
        pass

    return None


def analyze_document_against_job(
    resume_text: str,
    job_desc: str,
    raw_result: ParseResult,
    engine: str = "⚡ Fast Heuristic",
    api_key: str = "",
    role_seniority: str = "Senior / Lead"
) -> Dict:
    """
    Evaluates resume text against target job description.
    Computes ATS compatibility score, granular sub-scores, keywords, and structured insights.
    """
    resume_words = resume_text.split()
    word_count = len(resume_words)
    char_count = len(resume_text)

    # 1. Attempt Official Gemini API evaluation if enabled
    if "Gemini" in engine and api_key.strip():
        gemini_data = call_official_gemini_api(
            api_key=api_key,
            resume_text=resume_text,
            job_desc=job_desc,
            role_seniority=role_seniority
        )
        if gemini_data:
            gemini_data["word_count"] = word_count
            gemini_data["char_count"] = char_count
            gemini_data["evaluation_engine_used"] = "✨ Google Gemini API (gemini-2.5-flash)"
            return gemini_data

    # 2. Enhanced Heuristic Evaluation Engine
    resume_keywords = extract_keywords_from_text(resume_text)

    if job_desc.strip():
        jd_keywords = extract_keywords_from_text(job_desc)
        if not jd_keywords:
            words = re.findall(r"\b[A-Z][a-zA-Z0-9+#\.-]{2,}\b", job_desc)
            jd_keywords = set(words[:12])
    else:
        jd_keywords = {"Python", "SQL", "Git", "Docker", "REST API", "Agile", "Leadership"}

    matched_keywords = sorted(list(resume_keywords.intersection(jd_keywords)))
    missing_keywords = sorted(list(jd_keywords - resume_keywords))

    # Sub-Score 1: Hard Skills Match (%)
    if jd_keywords:
        match_ratio = len(matched_keywords) / len(jd_keywords)
        hard_skills_score = max(20, min(98, int(match_ratio * 100)))
    else:
        hard_skills_score = 65

    # Sub-Score 2: Keyword Density & Relevancy (%)
    total_keyword_mentions = sum(len(re.findall(r"\b" + re.escape(kw.lower()) + r"\b", resume_text.lower())) for kw in matched_keywords)
    density_pct = (total_keyword_mentions / max(100, word_count)) * 100
    if 1.5 <= density_pct <= 4.5:
        keyword_density_score = 92
    elif density_pct > 4.5:
        keyword_density_score = 75
    elif density_pct >= 0.8:
        keyword_density_score = 78
    else:
        keyword_density_score = 50

    # Sub-Score 3: Document Formatting & Structure (%)
    formatting_score = 85
    if 350 <= word_count <= 950:
        formatting_score += 5
    elif word_count < 300 or word_count > 1200:
        formatting_score -= 15

    if 1 <= raw_result.page_count <= 2:
        formatting_score += 5
    else:
        formatting_score -= 10

    action_verbs = ["led", "developed", "architected", "engineered", "scaled", "optimized", "managed", "designed", "deployed", "spearheaded"]
    found_verbs = [v for v in action_verbs if re.search(r"\b" + v + r"\b", resume_text.lower())]
    if len(found_verbs) >= 4:
        formatting_score += 5
    elif len(found_verbs) <= 1:
        formatting_score -= 10

    formatting_score = max(25, min(98, formatting_score))

    # Overall Weighted ATS Score
    ats_score = int((0.45 * hard_skills_score) + (0.30 * keyword_density_score) + (0.25 * formatting_score))
    ats_score = max(25, min(98, ats_score))

    # Qualitative Feedback
    strengths = []
    improvements = []

    if len(matched_keywords) >= 4:
        strengths.append(f"Strong technical alignment: Identified key matches for **{', '.join(matched_keywords[:4])}**.")
    else:
        improvements.append("Low keyword overlap: Seamlessly incorporate target skills from the job description into experience bullet points.")

    if 350 <= word_count <= 900:
        strengths.append(f"Optimal resume brevity ({word_count} words), allowing recruiters and ATS parsers to scan efficiently.")
    elif word_count < 300:
        improvements.append(f"Document is brief ({word_count} words). Expand on measurable metrics, scope of responsibility, and deliverables.")
    else:
        improvements.append(f"Document is lengthy ({word_count} words). Consolidate older experience into high-impact highlights.")

    if len(found_verbs) >= 3:
        strengths.append(f"Action-oriented language: Employs decisive impact verbs ({', '.join(found_verbs[:3])}).")
    else:
        improvements.append("Passive phrasing detected: Lead achievements with dynamic action verbs (e.g. 'Architected', 'Spearheaded').")

    if raw_result.page_count in [1, 2]:
        strengths.append(f"Document structure spans {raw_result.page_count} page(s), adhering to current industry hiring standards.")

    # Tailored Cover Letter Draft
    top_skills_str = ", ".join(matched_keywords[:4]) if matched_keywords else "software architecture and agile system development"
    cover_letter = (
        "Dear Hiring Team,\n\n"
        "I am writing to express my enthusiastic interest in the open position at your organization. "
        f"With deep hands-on experience in {top_skills_str}, I have built a track record of delivering "
        "high-quality, performant solutions that align technical execution with strategic company objectives.\n\n"
        "Throughout my career, I have prioritized clean design principles, robust test coverage, and "
        "measurable business impact. My background directly aligns with your team's current technical requirements, "
        f"particularly in leveraging {matched_keywords[0] if matched_keywords else 'modern engineering best practices'} to solve complex challenges.\n\n"
        "I welcome the opportunity to discuss how my qualifications and enthusiasm can drive value for your team. "
        "Thank you for your time and consideration.\n\n"
        "Sincerely,\n"
        "[Candidate Name]\n"
        "[Contact Information]"
    )

    return {
        "ats_score": ats_score,
        "hard_skills_score": hard_skills_score,
        "keyword_density_score": keyword_density_score,
        "formatting_score": formatting_score,
        "word_count": word_count,
        "char_count": char_count,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "strengths": strengths,
        "improvements": improvements,
        "cover_letter": cover_letter,
        "evaluation_engine_used": "⚡ Fast Heuristic Mode (Enhanced Rule-Based)"
    }


# ==============================================================================
# 5. Diagnostic Report Exporters (Markdown & Publication-Grade PDF)
# ==============================================================================

def generate_master_report_md(
    result: ParseResult,
    analysis: Dict,
    job_desc: str,
    role_seniority: str
) -> str:
    """Compiles a comprehensive diagnostic Markdown audit report for export."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    matched_str = ", ".join(analysis["matched_keywords"]) if analysis["matched_keywords"] else "None detected"
    missing_str = ", ".join(analysis["missing_keywords"]) if analysis["missing_keywords"] else "None (Complete match)"

    strengths_md = "\n".join([f"- {s}" for s in analysis["strengths"]])
    improvements_md = "\n".join([f"- {i}" for i in analysis["improvements"]])

    report = f"""# 📄 Candidate Resume & Portfolio Diagnostic Report
*Generated on {timestamp} by CYBER-ATS Neural Intelligence OS*

---

## 1. Document & Evaluation Metadata
- **Candidate File**: `{result.file_name or 'Uploaded Document'}`
- **Extraction Engine**: `{result.extraction_method}` (Pages: `{result.page_count}`)
- **Document Length**: `{analysis['word_count']}` words | `{analysis['char_count']}` characters
- **Target Seniority**: `{role_seniority}`
- **Analysis Engine**: `{analysis.get('evaluation_engine_used', 'Heuristic')}`

---

## 2. ATS Compatibility Scorecard
- **Overall ATS Match Score**: **{analysis['ats_score']}%**

### Granular Score Breakdown
| Dimension | Score | Assessment |
| :--- | :---: | :--- |
| **Hard Skills Match** | **{analysis['hard_skills_score']}%** | {'Optimal' if analysis['hard_skills_score'] >= 80 else 'Good' if analysis['hard_skills_score'] >= 60 else 'Needs Attention'} |
| **Keyword Density & Relevancy** | **{analysis['keyword_density_score']}%** | {'Optimal' if analysis['keyword_density_score'] >= 80 else 'Good' if analysis['keyword_density_score'] >= 60 else 'Needs Attention'} |
| **Document Formatting & Layout** | **{analysis['formatting_score']}%** | {'Clean Structure' if analysis['formatting_score'] >= 80 else 'Acceptable' if analysis['formatting_score'] >= 60 else 'Formatting Adjustments Recommended'} |

---

## 3. Skill & Keyword Diagnostics
- **✅ Matched Keywords**: {matched_str}
- **⚠️ Missing / High-Priority Keywords**: {missing_str}

---

## 4. AI Qualitative Insights
### 🌟 Key Strengths
{strengths_md}

### ⚡ Opportunities for Improvement
{improvements_md}

---

## 5. Tailored Cover Letter Draft
```text
{analysis['cover_letter']}
```

---
*Report generated automatically. Proprietary ATS diagnostic algorithms courtesy of CYBER-ATS.*
"""
    return report.strip()


def generate_professional_pdf_report(
    result: ParseResult,
    analysis: Dict,
    role_seniority: str
) -> bytes:
    """
    Compiles a publication-quality PDF diagnostic report using ReportLab Platypus.
    Returns raw PDF bytes.
    """
    if not _HAS_REPORTLAB:
        return b""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1e1b4b'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=10
    )
    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#312e81'),
        spaceBefore=8,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=10,
        spaceAfter=3
    )

    elements = []

    # Title & Metadata
    elements.append(Paragraph('CYBER-ATS // Resume Diagnostic Audit Report', title_style))
    now_str = datetime.datetime.now().strftime('%B %d, %Y - %H:%M:%S')
    doc_name = result.file_name or "Uploaded Resume"
    elements.append(Paragraph(f'Generated on {now_str} | Candidate File: <b>{doc_name}</b> | Seniority: <b>{role_seniority}</b>', subtitle_style))
    elements.append(HRFlowable(width='100%', thickness=1.5, color=colors.HexColor('#6366f1'), spaceBefore=0, spaceAfter=10))

    # ATS Score Table
    elements.append(Paragraph('1. ATS Compatibility Scorecard', h2_style))
    ats_score = analysis['ats_score']
    hard_skills = analysis['hard_skills_score']
    density = analysis['keyword_density_score']
    formatting = analysis['formatting_score']

    score_data = [
        ['Evaluation Dimension', 'Score', 'Status Assessment'],
        ['Overall ATS Compatibility', f'{ats_score}%', 'Optimal Fit' if ats_score >= 80 else 'Good' if ats_score >= 60 else 'Needs Attention'],
        ['Hard Skills Match', f'{hard_skills}%', 'Strong Overlap' if hard_skills >= 80 else 'Moderate' if hard_skills >= 60 else 'Skills Deficit'],
        ['Keyword Density & Relevancy', f'{density}%', 'Natural Balance' if density >= 80 else 'Acceptable' if density >= 60 else 'Low Frequency'],
        ['Document Structure & Hygiene', f'{formatting}%', 'ATS Clean' if formatting >= 80 else 'Minor Risks' if formatting >= 60 else 'Formatting Adjustments']
    ]
    t = Table(score_data, colWidths=[230, 80, 220])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4338ca')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('TOPPADDING', (0, 0), (-1, 0), 5),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8.5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 10))

    # Key Skills
    elements.append(Paragraph('2. Skill & Keyword Diagnostics', h2_style))
    matched_text = ', '.join(analysis['matched_keywords']) if analysis['matched_keywords'] else 'None detected'
    missing_text = ', '.join(analysis['missing_keywords']) if analysis['missing_keywords'] else 'None (Complete overlap)'
    elements.append(Paragraph(f'<b>Matched Keywords:</b> {matched_text}', body_style))
    elements.append(Spacer(1, 3))
    elements.append(Paragraph(f'<b>Missing / Recommended Keywords:</b> {missing_text}', body_style))
    elements.append(Spacer(1, 10))

    # Qualitative Strengths & Improvements
    elements.append(Paragraph('3. AI Qualitative Assessment', h2_style))
    elements.append(Paragraph('<b>Key Strengths:</b>', body_style))
    for s in analysis['strengths']:
        clean_s = s.replace('**', '')
        elements.append(Paragraph(f'• {clean_s}', bullet_style))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph('<b>Opportunities for Improvement:</b>', body_style))
    for imp in analysis['improvements']:
        clean_imp = imp.replace('**', '')
        elements.append(Paragraph(f'• {clean_imp}', bullet_style))
    elements.append(Spacer(1, 10))

    # Cover Letter
    elements.append(Paragraph('4. Tailored Cover Letter Summary', h2_style))
    cl_lines = analysis['cover_letter'].split('\n\n')
    for p in cl_lines:
        if p.strip():
            elements.append(Paragraph(p.strip().replace('\n', '<br/>'), body_style))
            elements.append(Spacer(1, 3))

    doc.build(elements)
    return buffer.getvalue()


# ==============================================================================
# 6. Futuristic Top HUD & Command Deck Toolbar
# ==============================================================================

# HUD Header Bar & System Control
hud_c1, hud_c2 = st.columns([3.3, 1.1], gap="small")

with hud_c1:
    st.markdown(
        """
        <div class="cyber-hud-header">
            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 0.35rem;">
                <span class="hud-tag">⚡ CYBER-ATS V2.5</span>
                <span class="hud-live-pill"><span class="hud-live-dot"></span> NEURAL ENGINE ACTIVE</span>
                <span class="hud-tag" style="background: rgba(6, 182, 212, 0.12); border-color: rgba(6, 182, 212, 0.35); color: #67e8f9;">LATENCY: 14ms</span>
            </div>
            <h1 class="cyber-title">AI RESUME & PORTFOLIO ANALYZER</h1>
            <div class="cyber-subtitle">
                Next-gen recruitment intelligence command center. Ingest candidate dossiers,
                screen cohorts at scale, inspect visual thumbnails, and run live STAR mock interviews.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with hud_c2:
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 6px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.74rem; font-weight: 800; color: #38bdf8; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 2px;">
                ⚡ SYSTEM CONTROL
            </div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #94a3b8;">
                BUFFER PURGE & REBOOT
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("🔄 REBOOT / RESET", use_container_width=True, help="Clear active memory & start a fresh session", key="top_reboot_btn"):
        reset_session_state()
        st.rerun()

# Top Command Deck Toolbar (Zero dead space flow)
st.markdown('<div class="command-deck-container">', unsafe_allow_html=True)
ctrl_c1, ctrl_c2, ctrl_c3, ctrl_c4 = st.columns([1.5, 1.4, 1.2, 0.9])

with ctrl_c1:
    st.markdown("<span class='hud-label'>🎯 MISSION PERSONA</span>", unsafe_allow_html=True)
    current_persona = st.session_state.get("app_persona", "👤 Candidate Dossier")
    persona_choice = st.radio(
        "Mission Persona",
        ["👤 Candidate Dossier", "👥 Recruiter Batch Screener"],
        index=0 if "Candidate" in current_persona else 1,
        horizontal=True,
        label_visibility="collapsed",
        key="top_persona_selector"
    )
    st.session_state["app_persona"] = persona_choice
    is_recruiter_mode = "Recruiter" in persona_choice

with ctrl_c2:
    st.markdown("<span class='hud-label'>🤖 NEURAL AI ENGINE</span>", unsafe_allow_html=True)
    current_model = st.session_state.get("model_choice", "⚡ Fast Heuristic")
    model_choice = st.radio(
        "Evaluation Engine",
        ["⚡ Fast Heuristic", "✨ Gemini API Mode"],
        index=0 if "Heuristic" in current_model else 1,
        horizontal=True,
        label_visibility="collapsed",
        key="top_engine_selector"
    )
    st.session_state["model_choice"] = model_choice

with ctrl_c3:
    st.markdown("<span class='hud-label'>🎖️ TARGET SENIORITY</span>", unsafe_allow_html=True)
    seniority_options = ["Entry-Level", "Mid-Level", "Senior / Lead", "Staff / Principal", "Executive / VP"]
    seniority_choice = st.selectbox(
        "Target Seniority",
        seniority_options,
        index=2,
        label_visibility="collapsed",
        key="top_seniority_selector"
    )
    st.session_state["role_seniority"] = seniority_choice

with ctrl_c4:
    st.markdown("<span class='hud-label'>⚡ SANITIZATION</span>", unsafe_allow_html=True)
    clean_text_enabled = st.checkbox(
        "Clean Text",
        value=True,
        help="Normalizes ligatures, removes non-standard control characters, and joins broken hyphenated lines.",
        key="top_clean_toggle"
    )

# Gemini API Key Drawer (if Gemini API Mode is selected)
if "Gemini" in st.session_state.get("model_choice", ""):
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    api_col1, api_col2 = st.columns([3, 1])
    with api_col1:
        api_key_input = st.text_input(
            "Gemini API Key (Optional)",
            value=st.session_state.get("api_key", ""),
            type="password",
            placeholder="Enter AIzaSy... or leave blank for automatic heuristic fallback",
            help="Your key stays secure in local session state. If empty, local neural heuristic rules are executed."
        )
        st.session_state["api_key"] = api_key_input
    with api_col2:
        st.markdown("<div style='height: 26px;'></div>", unsafe_allow_html=True)
        if api_key_input.strip():
            st.markdown("<span class='hud-live-pill' style='font-size: 0.78rem;'><span class='hud-live-dot'></span> LIVE GEMINI CONNECTED</span>", unsafe_allow_html=True)
        else:
            st.caption("⚡ Heuristic fallback armed")
else:
    api_key_input = ""

st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# 7. Side-by-Side Holographic Dropzones & Input Bays
# ==============================================================================

uploader_key_str = f"resume_uploader_{st.session_state['uploader_key']}"

bay_col1, bay_col2 = st.columns([1, 1], gap="medium")

# INGESTION BAY A: Document Upload
with bay_col1:
    st.markdown(
        f"""
        <div class="holographic-dropzone">
            <div class="bay-header">
                <div class="bay-title">📁 INGESTION BAY A: {"COHORT BATCH ARCHIVE" if is_recruiter_mode else "CANDIDATE DOSSIER"}</div>
                <div class="bay-status">{"BATCH QUEUE" if is_recruiter_mode else "SINGLE DOSSIER"}</div>
            </div>
        """,
        unsafe_allow_html=True
    )

    if is_recruiter_mode:
        uploaded_files = st.file_uploader(
            "Upload Candidate Resumes (PDF / DOCX)",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            key=uploader_key_str,
            help="Upload multiple candidate resumes to screen and rank a cohort simultaneously."
        )
        if uploaded_files:
            st.markdown(
                f"<div style='margin-top: 8px;'><span class='hud-live-pill'><span class='hud-live-dot'></span> {len(uploaded_files)} CANDIDATE FILES QUEUED</span></div>",
                unsafe_allow_html=True
            )
        uploaded_file = None
    else:
        uploaded_file = st.file_uploader(
            "Upload Resume / Portfolio (PDF / DOCX)",
            type=["pdf", "docx"],
            key=uploader_key_str,
            help="Supports PDF and DOCX files. Dual-engine parsing with PyMuPDF visual preview.",
        )
        if uploaded_file is not None:
            file_kb = uploaded_file.size / 1024
            st.markdown(
                f"<div style='margin-top: 8px;'><span class='hud-live-pill'><span class='hud-live-dot'></span> {uploaded_file.name} ({file_kb:.1f} KB)</span></div>",
                unsafe_allow_html=True
            )
        uploaded_files = None

    st.markdown("</div>", unsafe_allow_html=True)

# INGESTION BAY B: Job Matrix Spec
with bay_col2:
    st.markdown(
        """
        <div class="holographic-dropzone">
            <div class="bay-header">
                <div class="bay-title">🎯 INGESTION BAY B: TARGET JOB SPEC MATRIX</div>
                <div class="bay-status">ATS CRITERIA</div>
            </div>
        """,
        unsafe_allow_html=True
    )

    # Preset spec loader buttons
    st.markdown('<div class="preset-buttons">', unsafe_allow_html=True)
    preset_c1, preset_c2, preset_c3 = st.columns([1, 1, 0.6])
    with preset_c1:
        if st.button("📋 Staff AI Spec", use_container_width=True, key="preset_ai_btn"):
            st.session_state["job_description"] = SAMPLE_SPECS["Staff AI Engineer"]
            st.rerun()
    with preset_c2:
        if st.button("📋 Fullstack Spec", use_container_width=True, key="preset_fs_btn"):
            st.session_state["job_description"] = SAMPLE_SPECS["Senior Fullstack Lead"]
            st.rerun()
    with preset_c3:
        if st.button("🧹 Clear", use_container_width=True, key="preset_clr_btn"):
            st.session_state["job_description"] = ""
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    job_description = st.text_area(
        "Target Job Description (JD)",
        value=st.session_state.get("job_description", ""),
        placeholder="Paste target job posting, requirements, or role description here...",
        height=145,
        label_visibility="collapsed",
        help="The AI will compare resumes against this job description to evaluate ATS match and missing skills."
    )
    st.session_state["job_description"] = job_description

    st.markdown("</div>", unsafe_allow_html=True)


# High-Impact Action Launch Deck
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
action_col1, action_col2, action_col3 = st.columns([1, 2.2, 1])

with action_col2:
    st.markdown('<div class="launch-deck">', unsafe_allow_html=True)
    btn_label = "⚡ EXECUTE COHORT SCREENING PIPELINE" if is_recruiter_mode else "⚡ INITIALIZE NEURAL ATS ANALYSIS"
    analyze_button = st.button(btn_label, use_container_width=True, key="main_action_btn")
    st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# 8. Minimized Telemetry & Quick Export Sidebar
# ==============================================================================

with st.sidebar:
    st.markdown("### 🛰️ CYBER-ATS TELEMETRY")
    st.caption("Real-time subsystem status & diagnostic telemetry.")

    st.markdown(
        f"""
        <div style="background: rgba(20, 25, 45, 0.45); backdrop-filter: blur(28px) saturate(180%); -webkit-backdrop-filter: blur(28px) saturate(180%); border: 0.5px solid rgba(255, 255, 255, 0.14); box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.18); border-radius: 20px; padding: 16px; margin-bottom: 14px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #38bdf8; font-weight: 800; letter-spacing: 0.08em; margin-bottom: 8px;">SUBSYSTEM STATUS:</div>
            <div style="font-size: 0.76rem; color: #34d399; margin-bottom: 4px;">● pdfplumber: READY</div>
            <div style="font-size: 0.76rem; color: #34d399; margin-bottom: 4px;">● PyPDF2 Fallback: ARMED</div>
            <div style="font-size: 0.76rem; color: #34d399; margin-bottom: 4px;">● python-docx: ACTIVE</div>
            <div style="font-size: 0.76rem; color: {'#34d399' if _HAS_PYMUPDF else '#94a3b8'}; margin-bottom: 4px;">
                ● PyMuPDF (fitz): {'ONLINE' if _HAS_PYMUPDF else 'OFFLINE'}
            </div>
            <div style="font-size: 0.76rem; color: {'#34d399' if _HAS_REPORTLAB else '#94a3b8'}; margin-bottom: 4px;">
                ● ReportLab PDF: {'ONLINE' if _HAS_REPORTLAB else 'OFFLINE'}
            </div>
            <div style="font-size: 0.76rem; color: {'#34d399' if _HAS_GOOGLE_GENAI else '#94a3b8'};">
                ● Google GenAI: {'AVAILABLE' if _HAS_GOOGLE_GENAI else 'OFFLINE'}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Quick Exports if single candidate analysis is available
    if not is_recruiter_mode and st.session_state.get("analysis_data") and st.session_state.get("parsed_result"):
        st.markdown("---")
        st.markdown("##### 📥 Quick Exports")
        res_obj = st.session_state["parsed_result"]
        an_data = st.session_state["analysis_data"]

        if _HAS_REPORTLAB:
            pdf_bytes = generate_professional_pdf_report(
                result=res_obj,
                analysis=an_data,
                role_seniority=st.session_state.get("role_seniority", "Senior / Lead")
            )
            st.download_button(
                label="📥 Download PDF Audit",
                data=pdf_bytes,
                file_name=f"{res_obj.file_name.rsplit('.', 1)[0] if res_obj.file_name else 'resume'}_audit.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        quick_report = generate_master_report_md(
            result=res_obj,
            analysis=an_data,
            job_desc=st.session_state.get("job_description", ""),
            role_seniority=st.session_state.get("role_seniority", "Senior / Lead")
        )
        st.download_button(
            label="📥 Download Markdown (.md)",
            data=quick_report,
            file_name=f"{res_obj.file_name.rsplit('.', 1)[0] if res_obj.file_name else 'resume'}_audit.md",
            mime="text/markdown",
            use_container_width=True
        )

    st.markdown("---")
    if st.button("🔄 Reboot Session", use_container_width=True, key="sidebar_reboot_btn"):
        reset_session_state()
        st.rerun()


# ==============================================================================
# 9. Pipeline Execution Logic
# ==============================================================================

if analyze_button:
    selected_engine = st.session_state.get("model_choice", "⚡ Fast Heuristic")
    role_seniority = st.session_state.get("role_seniority", "Senior / Lead")

    if is_recruiter_mode:
        # Batch Screening Pipeline
        if not uploaded_files:
            st.error("⚠️ Ingestion Bay A Empty: Please upload candidate resumes to execute batch cohort screening.")
        else:
            with st.spinner(f"Executing batch cohort screening on {len(uploaded_files)} resumes..."):
                batch_data_list = []
                for file_item in uploaded_files:
                    time.sleep(0.1)
                    parse_res = extract_text_from_file(file_item, clean=clean_text_enabled)
                    if parse_res.success:
                        analysis_res = analyze_document_against_job(
                            resume_text=parse_res.text,
                            job_desc=job_description,
                            raw_result=parse_res,
                            engine=selected_engine,
                            api_key=api_key_input,
                            role_seniority=role_seniority
                        )
                        # Render thumbnail if PDF
                        thumb_bytes = None
                        if file_item.name.lower().endswith(".pdf"):
                            try:
                                file_item.seek(0)
                                thumb_bytes = render_pdf_thumbnail(file_item.read())
                            except Exception:
                                pass

                        score = analysis_res["ats_score"]
                        fit_cat = "🌟 Strong Match" if score >= 80 else "⚡ Moderate" if score >= 65 else "⚠️ Low Match"

                        batch_data_list.append({
                            "Candidate / File": file_item.name,
                            "Overall ATS Score (%)": score,
                            "Hard Skills (%)": analysis_res["hard_skills_score"],
                            "Keyword Density (%)": analysis_res["keyword_density_score"],
                            "Formatting (%)": analysis_res["formatting_score"],
                            "Fit Category": fit_cat,
                            "Engine": parse_res.extraction_method,
                            "Word Count": analysis_res["word_count"],
                            "Page Count": parse_res.page_count,
                            "Matched Skills": ", ".join(analysis_res["matched_keywords"][:5]),
                            "parse_result": parse_res,
                            "analysis": analysis_res,
                            "thumbnail": thumb_bytes
                        })

                batch_data_list.sort(key=lambda x: x["Overall ATS Score (%)"], reverse=True)
                st.session_state["batch_results"] = batch_data_list
                st.toast(f"Batch analysis complete: {len(batch_data_list)} resumes ranked!", icon="🏆")

    else:
        # Single Candidate Pipeline
        if uploaded_file is None:
            st.error("⚠️ Ingestion Bay A Empty: Please upload a PDF or DOCX resume before running analysis.")
        else:
            with st.spinner(f"Extracting document structure & running {selected_engine}..."):
                time.sleep(0.3)
                parse_res = extract_text_from_file(uploaded_file, clean=clean_text_enabled)
                st.session_state["parsed_result"] = parse_res

                if parse_res.success:
                    analysis = analyze_document_against_job(
                        resume_text=parse_res.text,
                        job_desc=job_description,
                        raw_result=parse_res,
                        engine=selected_engine,
                        api_key=api_key_input,
                        role_seniority=role_seniority
                    )
                    st.session_state["analysis_data"] = analysis
                    st.session_state["cover_letter_draft"] = analysis["cover_letter"]

                    # Render Visual PDF Thumbnail
                    if uploaded_file.name.lower().endswith(".pdf"):
                        try:
                            uploaded_file.seek(0)
                            st.session_state["pdf_thumbnail"] = render_pdf_thumbnail(uploaded_file.read())
                        except Exception:
                            st.session_state["pdf_thumbnail"] = None
                    else:
                        st.session_state["pdf_thumbnail"] = None

                    # Reset / Seed Chat
                    if not st.session_state["chat_messages"]:
                        st.session_state["chat_messages"] = [
                            {
                                "role": "assistant",
                                "content": (
                                    f"👋 **CYBER-ATS AI Agent Online. Indexed dossier `{parse_res.file_name}`.**\n\n"
                                    f"Your estimated ATS match score is **{analysis['ats_score']}%**. "
                                    "Ask me to rewrite bullet points using the STAR method, simulate an interview, "
                                    "or explain how to incorporate missing target skills!"
                                )
                            }
                        ]

                    st.toast(f"Analysis completed via {analysis.get('evaluation_engine_used')}!", icon="✅")
                else:
                    st.session_state["analysis_data"] = None


# ==============================================================================
# 10. Multi-Tab Command Center Dashboard
# ==============================================================================

st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 ATS TELEMETRY & MATCH" if not is_recruiter_mode else "🏆 COHORT SCREENING LEADERBOARD",
    "📄 RAW & CLEANED DOSSIER PREVIEW",
    "✉️ COVER LETTER SYNTHESIZER",
    "💬 INTERACTIVE AI COPILOT & MOCK INTERVIEW"
])

result: Optional[ParseResult] = st.session_state.get("parsed_result")
analysis: Optional[Dict] = st.session_state.get("analysis_data")
batch_data: List[Dict] = st.session_state.get("batch_results", [])
pdf_thumb: Optional[bytes] = st.session_state.get("pdf_thumbnail")


# ------------------------------------------------------------------------------
# TAB 1: ATS Telemetry / Cohort Screening Leaderboard
# ------------------------------------------------------------------------------
with tab1:
    if is_recruiter_mode:
        st.markdown("### 🏆 Cohort Screening Leaderboard")
        st.caption("Automated batch ranking of candidate resumes evaluated against your target Job Description.")

        if not batch_data:
            st.markdown(
                """
                <div style="text-align: center; padding: 4.5rem 2rem; border-radius: 24px; border: 0.5px dashed rgba(56, 189, 248, 0.45); background: rgba(20, 25, 45, 0.45); backdrop-filter: blur(28px) saturate(180%); -webkit-backdrop-filter: blur(28px) saturate(180%); box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.18);">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">👥</div>
                    <h3 style="color: #f8fafc; margin-bottom: 0.5rem;">Recruiter Batch Screener Active</h3>
                    <p style="color: #94a3b8; max-width: 560px; margin: 0 auto 1.5rem auto;">
                        Upload candidate resumes into <b>Ingestion Bay A</b> above, verify your target job spec in <b>Ingestion Bay B</b>,
                        and click <b>⚡ EXECUTE COHORT SCREENING PIPELINE</b> to generate a real-time ranked candidate leaderboard.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            total_cand = len(batch_data)
            top_cand = batch_data[0]
            avg_score = int(sum(c["Overall ATS Score (%)"] for c in batch_data) / total_cand)
            strong_matches = sum(1 for c in batch_data if c["Overall ATS Score (%)"] >= 80)

            st.markdown(
                f"""
                <div class="metric-grid">
                    <div class="custom-card">
                        <div class="card-top-bar top-bar-primary"></div>
                        <div class="card-label">CANDIDATES SCREENED</div>
                        <div class="card-value">{total_cand}</div>
                        <div class="card-caption">Total resumes parsed in batch</div>
                    </div>
                    <div class="custom-card">
                        <div class="card-top-bar top-bar-emerald"></div>
                        <div class="card-label">TOP CONTENDER</div>
                        <div class="card-value" style="color: #10b981; font-size: 1.8rem;">{top_cand['Overall ATS Score (%)']}%</div>
                        <div class="card-caption">{top_cand['Candidate / File']}</div>
                    </div>
                    <div class="custom-card">
                        <div class="card-top-bar top-bar-cyan"></div>
                        <div class="card-label">COHORT MEAN ATS</div>
                        <div class="card-value">{avg_score}%</div>
                        <div class="card-caption">Mean compatibility benchmark</div>
                    </div>
                    <div class="custom-card">
                        <div class="card-top-bar top-bar-amber"></div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div class="card-label">HIGH-FIT TALENT</div>
                            <span class="hud-live-pill" style="font-size: 0.68rem; padding: 2px 8px;"><span class="hud-live-dot"></span> ≥ 80%</span>
                        </div>
                        <div class="card-value" style="color: #f59e0b;">{strong_matches}</div>
                        <div class="card-caption">Scoring ≥ 80% compatibility</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            leaderboard_df = pd.DataFrame([
                {
                    "Rank": f"#{i+1}",
                    "Candidate File": c["Candidate / File"],
                    "Overall Match": f"{c['Overall ATS Score (%)']}%",
                    "Hard Skills": f"{c['Hard Skills (%)']}%",
                    "Keyword Density": f"{c['Keyword Density (%)']}%",
                    "Formatting": f"{c['Formatting (%)']}%",
                    "Fit Category": c["Fit Category"],
                    "Parser Engine": c["Engine"]
                }
                for i, c in enumerate(batch_data)
            ])

            st.dataframe(
                leaderboard_df,
                use_container_width=True,
                hide_index=True
            )

            csv_data = leaderboard_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Candidate Leaderboard (CSV)",
                data=csv_data,
                file_name="candidate_screening_leaderboard.csv",
                mime="text/csv"
            )

            st.markdown("---")

            # Drill-Down Candidate Dossier Inspector
            st.markdown("### 🔍 Candidate Deep-Dive Dossier")
            candidate_names = [f"#{i+1} - {c['Candidate / File']} ({c['Overall ATS Score (%)']}%)" for i, c in enumerate(batch_data)]
            selected_idx = st.selectbox("Select Candidate to Inspect Full Report", range(len(candidate_names)), format_func=lambda i: candidate_names[i])

            chosen_cand = batch_data[selected_idx]
            ch_parse: ParseResult = chosen_cand["parse_result"]
            ch_an: Dict = chosen_cand["analysis"]

            d_col1, d_col2 = st.columns([1, 2], gap="medium")
            with d_col1:
                if chosen_cand["thumbnail"]:
                    st.markdown('<div class="thumbnail-container">', unsafe_allow_html=True)
                    st.image(chosen_cand["thumbnail"], caption=f"Preview: {chosen_cand['Candidate / File']}", use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info(f"Visual thumbnail not available for {chosen_cand['Candidate / File']}.")

            with d_col2:
                st.markdown(f"#### 👤 {chosen_cand['Candidate / File']}")
                st.markdown(f"**Overall Score:** `{chosen_cand['Overall ATS Score (%)']}%` | **Engine:** `{ch_parse.extraction_method}`")

                m_badges = "".join([f'<span class="badge-tag badge-matched">✓ {kw}</span>' for kw in ch_an["matched_keywords"][:6]])
                st.markdown(f'<div class="badge-container">{m_badges}</div>', unsafe_allow_html=True)

                st.markdown("##### Strengths")
                for s in ch_an["strengths"][:2]:
                    st.markdown(f"- {s}")

                st.markdown("##### Improvement Areas")
                for imp in ch_an["improvements"][:2]:
                    st.markdown(f"- {imp}")

                if _HAS_REPORTLAB:
                    cand_pdf = generate_professional_pdf_report(ch_parse, ch_an, st.session_state.get("role_seniority", "Senior / Lead"))
                    st.download_button(
                        label=f"📥 Download PDF Dossier for #{selected_idx+1}",
                        data=cand_pdf,
                        file_name=f"{chosen_cand['Candidate / File'].rsplit('.', 1)[0]}_audit.pdf",
                        mime="application/pdf",
                        key=f"dl_pdf_cand_{selected_idx}"
                    )

    else:
        # Candidate Mode
        if result and not result.success:
            st.error(f"❌ **Document Parsing Failed:** {result.error}")
            st.info("Tip: Ensure document is not password-protected, corrupt, or empty.")
        elif analysis and result and result.success:
            ats_score = analysis["ats_score"]
            score_color = "#10b981" if ats_score >= 80 else "#f59e0b" if ats_score >= 60 else "#f43f5e"

            st.markdown(
                f"""
                <div class="metric-grid">
                    <div class="custom-card">
                        <div class="card-top-bar top-bar-primary"></div>
                        <div class="card-label">OVERALL ATS COMPATIBILITY</div>
                        <div class="card-value" style="color: {score_color};">{ats_score}%</div>
                        <div class="card-caption">Multi-dimensional weighted fit</div>
                    </div>
                    <div class="custom-card">
                        <div class="card-top-bar top-bar-emerald"></div>
                        <div class="card-label">DOCUMENT BREVITY</div>
                        <div class="card-value">{analysis['word_count']:,}</div>
                        <div class="card-caption">~{analysis['char_count']:,} characters</div>
                    </div>
                    <div class="custom-card">
                        <div class="card-top-bar top-bar-cyan"></div>
                        <div class="card-label">PAGE STRUCTURE</div>
                        <div class="card-value">{result.page_count}</div>
                        <div class="card-caption">Estimated document length</div>
                    </div>
                    <div class="custom-card">
                        <div class="card-top-bar top-bar-amber"></div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div class="card-label">EXTRACTION ENGINE</div>
                            <span class="hud-live-pill" style="font-size: 0.68rem; padding: 2px 8px;"><span class="hud-live-dot"></span> ACTIVE</span>
                        </div>
                        <div class="card-value" style="font-size: 1.5rem; margin-top: 5px;">{result.extraction_method}</div>
                        <div class="card-caption">{analysis.get('evaluation_engine_used')}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Graphical Breakdown & Granular Scores
            st.markdown("### 📊 Multi-Dimensional ATS Evaluation Matrix")
            st.caption("Detailed score distribution across critical hiring criteria.")

            chart_col, bars_col = st.columns([1.1, 1], gap="medium")

            h_score = analysis.get("hard_skills_score", 70)
            k_score = analysis.get("keyword_density_score", 75)
            f_score = analysis.get("formatting_score", 85)

            with chart_col:
                chart_df = pd.DataFrame([
                    {"Dimension": "Hard Skills", "Score": h_score},
                    {"Dimension": "Keyword Density", "Score": k_score},
                    {"Dimension": "Formatting & Hygiene", "Score": f_score},
                ])
                bar_chart = (
                    alt.Chart(chart_df)
                    .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8, size=42)
                    .encode(
                        x=alt.X('Dimension:N', axis=alt.Axis(labelAngle=0, labelFont='Plus Jakarta Sans', labelColor='#94a3b8', title=None)),
                        y=alt.Y('Score:Q', scale=alt.Scale(domain=[0, 100]), title="Compatibility (%)", axis=alt.Axis(labelColor='#94a3b8', titleColor='#94a3b8')),
                        color=alt.Color('Dimension:N', scale=alt.Scale(
                            domain=["Hard Skills", "Keyword Density", "Formatting & Hygiene"],
                            range=["#10b981", "#8b5cf6", "#06b6d4"]
                        ), legend=None),
                        tooltip=['Dimension', 'Score']
                    )
                    .properties(height=260)
                    .configure_view(strokeOpacity=0)
                )
                st.altair_chart(bar_chart, use_container_width=True)

            with bars_col:
                h_color = "#10b981" if h_score >= 80 else "#f59e0b" if h_score >= 60 else "#f43f5e"
                st.markdown(
                    f"""
                    <div class="progress-card">
                        <div class="progress-header">
                            <span class="progress-title">🎯 Hard Skills Overlap</span>
                            <span class="progress-pct" style="color: {h_color};">{h_score}%</span>
                        </div>
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" style="width: {h_score}%; background: {h_color};"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                k_color = "#10b981" if k_score >= 80 else "#f59e0b" if k_score >= 60 else "#f43f5e"
                st.markdown(
                    f"""
                    <div class="progress-card">
                        <div class="progress-header">
                            <span class="progress-title">📈 Keyword Density & Natural Flow</span>
                            <span class="progress-pct" style="color: {k_color};">{k_score}%</span>
                        </div>
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" style="width: {k_score}%; background: {k_color};"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                f_color = "#10b981" if f_score >= 80 else "#f59e0b" if f_score >= 60 else "#f43f5e"
                st.markdown(
                    f"""
                    <div class="progress-card">
                        <div class="progress-header">
                            <span class="progress-title">📐 Layout & Brevity Hygiene</span>
                            <span class="progress-pct" style="color: {f_color};">{f_score}%</span>
                        </div>
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" style="width: {f_score}%; background: {f_color};"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            col_left, col_right = st.columns([1, 1], gap="large")

            with col_left:
                st.markdown("### 🎯 Skill & Keyword Alignment")
                st.caption("Comparison of critical skills identified in the resume vs. the job description.")

                st.markdown("##### ✅ Matched Skills & Keywords")
                if analysis["matched_keywords"]:
                    badges_html = "".join([f'<span class="badge-tag badge-matched">✓ {kw}</span>' for kw in analysis["matched_keywords"]])
                    st.markdown(f'<div class="badge-container">{badges_html}</div>', unsafe_allow_html=True)
                else:
                    st.warning("No direct keyword matches detected. Ensure your target job description is loaded.")

                st.markdown("##### ⚠️ Missing / Recommended Keywords")
                if analysis["missing_keywords"]:
                    missing_html = "".join([f'<span class="badge-tag badge-missing">+ {kw}</span>' for kw in analysis["missing_keywords"]])
                    st.markdown(f'<div class="badge-container">{missing_html}</div>', unsafe_allow_html=True)
                    st.info("💡 **Recommendation:** Weaving these missing terms into relevant project bullet points will raise your ATS match.")
                else:
                    st.success("🎉 Excellent! All major target skills were identified in your document.")

                st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                st.markdown("##### 📥 Export Diagnostic Reports")
                btn_pdf_col, btn_md_col = st.columns([1, 1])

                with btn_pdf_col:
                    if _HAS_REPORTLAB:
                        pdf_data = generate_professional_pdf_report(
                            result=result,
                            analysis=analysis,
                            role_seniority=st.session_state.get("role_seniority", "Senior / Lead")
                        )
                        st.download_button(
                            label="📄 Download PDF Audit",
                            data=pdf_data,
                            file_name=f"{result.file_name.rsplit('.', 1)[0] if result.file_name else 'resume'}_audit.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    else:
                        st.caption("ReportLab required for PDF export.")

                with btn_md_col:
                    master_report_md = generate_master_report_md(
                        result=result,
                        analysis=analysis,
                        job_desc=st.session_state.get("job_description", ""),
                        role_seniority=st.session_state.get("role_seniority", "Senior / Lead")
                    )
                    st.download_button(
                        label="📝 Download Markdown (.md)",
                        data=master_report_md,
                        file_name=f"{result.file_name.rsplit('.', 1)[0] if result.file_name else 'resume'}_audit.md",
                        mime="text/markdown",
                        use_container_width=True
                    )

            with col_right:
                st.markdown("### 💡 AI Qualitative Audit & Guidance")
                st.caption("Actionable insights on impact framing, layout hygiene, and recruiter scannability.")

                with st.container():
                    st.markdown(
                        """
                        <div class="insight-card" style="border-left: 4px solid #10b981;">
                            <div class="insight-header">🌟 Key Strengths</div>
                        """,
                        unsafe_allow_html=True
                    )
                    for s in analysis["strengths"]:
                        st.markdown(f"- {s}")
                    st.markdown("</div>", unsafe_allow_html=True)

                with st.container():
                    st.markdown(
                        """
                        <div class="insight-card" style="border-left: 4px solid #f59e0b;">
                            <div class="insight-header">⚡ Opportunities for Improvement</div>
                        """,
                        unsafe_allow_html=True
                    )
                    for imp in analysis["improvements"]:
                        st.markdown(f"- {imp}")
                    st.markdown("</div>", unsafe_allow_html=True)

        else:
            st.markdown(
                """
                <div style="text-align: center; padding: 4.5rem 2rem; border-radius: 24px; border: 0.5px dashed rgba(56, 189, 248, 0.45); background: rgba(20, 25, 45, 0.45); backdrop-filter: blur(28px) saturate(180%); -webkit-backdrop-filter: blur(28px) saturate(180%); box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.18);">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
                    <h3 style="color: #f8fafc; margin-bottom: 0.5rem;">Ready for Neural Analysis</h3>
                    <p style="color: #94a3b8; max-width: 560px; margin: 0 auto 1.5rem auto;">
                        Upload a candidate resume or portfolio in <b>Ingestion Bay A</b>, load or paste your target job spec
                        in <b>Ingestion Bay B</b>, and click <b>⚡ INITIALIZE NEURAL ATS ANALYSIS</b> to execute multi-dimensional scoring.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )


# ------------------------------------------------------------------------------
# TAB 2: Parsed Document Output & Visual Thumbnail Preview
# ------------------------------------------------------------------------------
with tab2:
    st.markdown("### 📄 Parsed Document Output & Visual Preview")
    st.caption("Cleaned, artifact-free text alongside high-resolution visual page previews.")

    if result and result.success:
        top_col1, top_col2, top_col3 = st.columns([2, 1, 1])
        with top_col1:
            st.success(f"Extracted **{len(result.text):,}** characters across **{result.page_count}** page(s) using **`{result.extraction_method}`**.")
        with top_col2:
            view_mode = st.radio("Display View", ["Cleaned Text", "Raw Extracted"], horizontal=True)
        with top_col3:
            st.download_button(
                label="📥 Download Clean Text",
                data=result.text,
                file_name=f"{result.file_name.rsplit('.', 1)[0] if result.file_name else 'resume'}_cleaned.txt",
                mime="text/plain",
                use_container_width=True
            )

        content_to_show = result.text if view_mode == "Cleaned Text" else result.raw_text

        thumb_col, text_col = st.columns([1, 1.8], gap="large")

        with thumb_col:
            st.markdown("#### 🖼️ Visual Page Preview")
            if pdf_thumb:
                st.markdown('<div class="thumbnail-container">', unsafe_allow_html=True)
                st.image(pdf_thumb, caption=f"Page 1 Render: {result.file_name}", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            elif result.file_name and result.file_name.lower().endswith(".docx"):
                st.info("📄 **Microsoft Word Document (.docx)**\n\nVisual raster thumbnails are specific to PDF formats. The full parsed text and tables are displayed on the right.")
            else:
                st.info("Visual preview unavailable.")

        with text_col:
            st.markdown("#### 🔍 Text Content Inspector")
            st.text_area(
                "Document Content",
                value=content_to_show,
                height=520,
                label_visibility="collapsed"
            )

        with st.expander("⚙️ Extraction Metadata & Debug Info"):
            st.json(result.to_dict())

    elif result and not result.success:
        st.error(f"Extraction Error: {result.error}")
    else:
        st.info("Upload a document and click 'INITIALIZE NEURAL ATS ANALYSIS' to view visual thumbnail and parsed resume text.")


# ------------------------------------------------------------------------------
# TAB 3: Cover Letter Synthesizer
# ------------------------------------------------------------------------------
with tab3:
    st.markdown("### ✉️ Tailored Cover Letter Synthesizer")
    st.caption("Automatically synthesize a personalized, role-specific cover letter using candidate qualifications.")

    if analysis and result and result.success:
        c1, c2 = st.columns([1, 2], gap="medium")

        with c1:
            st.markdown("#### Configuration")
            tone = st.selectbox("Writing Tone", ["Professional & Confident", "Conversational & Dynamic", "Executive & Strategic"], index=0)
            hiring_manager = st.text_input("Hiring Manager / Team Name", value="Hiring Team")
            company_name = st.text_input("Target Company Name", value="Innovative Technologies Inc.")

            regen_btn = st.button("🔄 Refresh Letter Draft", use_container_width=True)
            if regen_btn:
                st.session_state["cover_letter_draft"] = (
                    f"Dear {hiring_manager} at {company_name},\n\n"
                    f"I am writing to express my strong enthusiasm for joining {company_name}. "
                    f"With deep expertise in {', '.join(analysis['matched_keywords'][:3]) if analysis['matched_keywords'] else 'software engineering'}, "
                    "I have consistently delivered scalable, mission-critical solutions.\n\n"
                    f"In review of the job requirements, my background directly aligns with your technical direction and high standard of engineering execution. "
                    "I look forward to discussing how my experience can support your team's goals.\n\n"
                    "Sincerely,\n"
                    "[Candidate Name]"
                )
                st.toast("Cover letter draft updated!", icon="✨")

        with c2:
            st.markdown("#### Draft Preview")
            draft_text = st.text_area(
                "Generated Cover Letter",
                value=st.session_state.get("cover_letter_draft", analysis["cover_letter"]),
                height=380,
                help="Edit or customize this letter draft before downloading."
            )

            dl_col1, dl_col2 = st.columns([1, 1])
            with dl_col1:
                st.download_button(
                    label="📥 Download Cover Letter (.txt)",
                    data=draft_text,
                    file_name="tailored_cover_letter.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            with dl_col2:
                if st.button("📋 Copy to Clipboard", use_container_width=True):
                    st.toast("Ready to copy! Select text and press Ctrl+C / Cmd+C", icon="📋")

    else:
        st.info("Upload a resume and execute analysis to automatically generate a tailored cover letter.")


# ------------------------------------------------------------------------------
# TAB 4: Interactive AI Copilot & Mock Interview Simulator
# ------------------------------------------------------------------------------
with tab4:
    st.markdown("### 💬 Interactive Career Coach & Mock Interview Simulator")
    st.caption("Switch between general advisory Q&A and a live, graded mock technical/behavioral interview.")

    if not result or not result.success or not analysis:
        st.info("Upload and analyze a resume to activate the interactive assistant and mock interviewer.")
    else:
        assistant_mode = st.radio(
            "Assistant Mode",
            ["💬 Career Coach & Q&A", "🎤 Live Mock Interview Simulator"],
            horizontal=True,
            help="Choose between conversational resume advising or a simulated, graded mock interview."
        )

        st.markdown("---")

        if assistant_mode == "🎤 Live Mock Interview Simulator":
            st.markdown("#### 🎤 Executive Mock Interview Session")
            st.caption("The agent acts as an executive technical hiring manager. Answer questions and receive instant scoring based on the STAR framework.")

            int_c1, int_c2 = st.columns([3, 1])
            with int_c2:
                if st.button("🔄 Restart Interview", use_container_width=True):
                    st.session_state["mock_interview_history"] = []
                    st.session_state["mock_question_index"] = 0
                    st.rerun()

            if not st.session_state["mock_interview_history"]:
                top_skill = analysis["matched_keywords"][0] if analysis["matched_keywords"] else "software system design"
                q1 = (
                    f"👋 **Welcome to your technical mock interview for the {st.session_state.get('role_seniority', 'Senior / Lead')} position!**\n\n"
                    "I have reviewed your resume and the target job description. Let's begin:\n\n"
                    f"🎯 **Question 1 (Core Architecture & Leadership)**:\n"
                    f"*'In your recent engineering experience, walk me through a challenging project where you leveraged **{top_skill}**. "
                    "What architectural tradeoffs did you navigate, and what quantifiable impact did it deliver to the business?'*\n\n"
                    "💬 *Type your answer below using the chat input. I will grade your response on the STAR framework, provide constructive feedback, and ask the next question.*"
                )
                st.session_state["mock_interview_history"] = [{"role": "assistant", "content": q1}]
                st.session_state["mock_question_index"] = 1

            for m in st.session_state["mock_interview_history"]:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

            cand_answer = st.chat_input("Type your interview response here (use Situation, Task, Action, Result)...")

            if cand_answer:
                st.session_state["mock_interview_history"].append({"role": "user", "content": cand_answer})
                with st.chat_message("user"):
                    st.markdown(cand_answer)

                with st.chat_message("assistant"):
                    with st.spinner("Grading your response against industry rubrics..."):
                        api_key = st.session_state.get("api_key", "").strip()
                        engine_choice = st.session_state.get("model_choice", "")
                        mock_eval = None

                        if "Gemini" in engine_choice and api_key and _HAS_GOOGLE_GENAI:
                            mock_eval = call_official_gemini_chat(
                                api_key=api_key,
                                resume_text=result.text,
                                job_desc=st.session_state.get("job_description", ""),
                                chat_history=st.session_state["mock_interview_history"],
                                user_prompt=cand_answer,
                                is_mock_interview=True
                            )

                        if not mock_eval:
                            q_idx = st.session_state["mock_question_index"]
                            missing_kw = analysis["missing_keywords"][0] if analysis["missing_keywords"] else "system resilience"
                            matched_kw = analysis["matched_keywords"][min(1, len(analysis["matched_keywords"])-1)] if analysis["matched_keywords"] else "API performance"

                            ans_words = len(cand_answer.split())
                            has_metrics = bool(re.search(r'\d+%|\$\d+|\d+x|\d+ [a-zA-Z]+', cand_answer))
                            grade = min(9.5, max(6.0, 7.0 + (1.2 if ans_words > 40 else 0) + (1.0 if has_metrics else 0)))

                            next_q_idx = q_idx + 1
                            st.session_state["mock_question_index"] = next_q_idx

                            mock_eval = (
                                f"### 📝 Evaluation & STAR Score: **{grade:.1f} / 10**\n\n"
                                f"**🌟 What Went Well**:\n"
                                f"- Good technical articulation and clear context setting.\n"
                                f"- {'Solid inclusion of quantifiable metrics!' if has_metrics else 'Clear communication of personal contribution.'}\n\n"
                                f"**⚡ Improvement Opportunities**:\n"
                                f"- {'Ensure you explicitly state the final business metric (revenue, latency, or time saved).' if not has_metrics else 'Consider mentioning the failure modes you anticipated.'}\n"
                                "- Anchor more firmly in the **STAR method** (Situation → Task → Action → Result).\n\n"
                                f"**💡 Exemplary Senior Phrasing**:\n"
                                f"> *'When faced with high traffic bottlenecks, I led the redesign of our {matched_kw} layer, reducing latency by 40% while maintaining 99.99% SLA during peak load.'*\n\n"
                                "---\n\n"
                                f"🎯 **Question {next_q_idx} (Domain Bridging & Reliability)**:\n"
                                f"*'The job description emphasizes **{missing_kw}**. Can you tell me about a time you had to quickly adopt an unfamiliar technology to solve a production issue, and what safeguards you put in place?'*"
                            )

                        st.markdown(mock_eval)
                        st.session_state["mock_interview_history"].append({"role": "assistant", "content": mock_eval})

        else:
            # General Career Coach & Q&A
            st.markdown("##### 💡 Suggested Career Coach Prompts")
            p_col1, p_col2, p_col3, p_col4 = st.columns(4)

            selected_prompt = None
            with p_col1:
                if st.button("✨ Rewrite Top Bullets", use_container_width=True):
                    selected_prompt = "Rewrite 2 of my experience bullet points using high-impact action verbs and the STAR framework."
            with p_col2:
                if st.button("🎯 Top Interview Questions", use_container_width=True):
                    selected_prompt = "What are the 3 most challenging technical and behavioral interview questions I should expect for this role?"
            with p_col3:
                if st.button("🔍 Address Skill Gaps", use_container_width=True):
                    selected_prompt = "How should I address my missing keywords and technical skill gaps during an interview?"
            with p_col4:
                if st.button("📈 90%+ ATS Advice", use_container_width=True):
                    selected_prompt = "What specific changes will raise my ATS compatibility score to above 90%?"

            chat_container = st.container()
            with chat_container:
                for msg in st.session_state["chat_messages"]:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

            user_input = st.chat_input("Ask anything about your resume, bullet rewrites, or interview prep...")
            prompt_to_run = selected_prompt or user_input

            if prompt_to_run:
                st.session_state["chat_messages"].append({"role": "user", "content": prompt_to_run})
                with st.chat_message("user"):
                    st.markdown(prompt_to_run)

                with st.chat_message("assistant"):
                    with st.spinner("Analyzing resume context..."):
                        api_key = st.session_state.get("api_key", "").strip()
                        engine_choice = st.session_state.get("model_choice", "")
                        ai_reply = None

                        if "Gemini" in engine_choice and api_key and _HAS_GOOGLE_GENAI:
                            ai_reply = call_official_gemini_chat(
                                api_key=api_key,
                                resume_text=result.text,
                                job_desc=st.session_state.get("job_description", ""),
                                chat_history=st.session_state["chat_messages"],
                                user_prompt=prompt_to_run,
                                is_mock_interview=False
                            )

                        if not ai_reply:
                            lower_q = prompt_to_run.lower()
                            matched_kw = ", ".join(analysis["matched_keywords"][:4]) or "core technical competencies"
                            missing_kw = ", ".join(analysis["missing_keywords"][:3]) or "advanced domain keywords"

                            if "rewrite" in lower_q or "bullet" in lower_q:
                                ai_reply = (
                                    "### ✍️ High-Impact Bullet Point Rewrites\n\n"
                                    "Here is how you can transform standard duties into high-impact, quantifiable achievements using the **STAR Method**:\n\n"
                                    f"1. **Before**: *'Worked on software components and backend services.'*\n"
                                    f"   - **Rewrite**: **'Architected and deployed scalable {matched_kw.split(',')[0]} microservices**, reducing API latency by 35% across 2M+ monthly active requests.\n\n"
                                    f"2. **Before**: *'Collaborated with teams on feature releases.'*\n"
                                    f"   - **Rewrite**: **'Spearheaded cross-functional delivery** of mission-critical features, integrating CI/CD pipelines to accelerate release velocity by 40%.\n\n"
                                    "💡 *Recruiter Tip: Notice how each bullet starts with a past-tense power verb and ends with a measurable business outcome.*"
                                )
                            elif "interview" in lower_q or "question" in lower_q:
                                ai_reply = (
                                    "### 🎯 Targeted Interview Questions for This Role\n\n"
                                    f"Based on your profile and the target job description, prepare for these three questions:\n\n"
                                    f"1. **Technical Architecture**: *'Can you walk me through a challenging problem you solved using **{matched_kw.split(',')[0]}**, and why you chose your specific architecture?'*\n\n"
                                    f"2. **Gap Bridging**: *'The job requires **{missing_kw.split(',')[0] if missing_kw else 'distributed systems'}**. What experience do you have with related tools, and how quickly can you onboard?'*\n\n"
                                    "3. **Behavioral Leadership**: *'Tell me about a time when business priorities shifted right before a major release. How did you adapt your engineering deliverables?'*"
                                )
                            elif "gap" in lower_q or "missing" in lower_q:
                                ai_reply = (
                                    "### 🔍 Action Plan for Bridging Skill Gaps\n\n"
                                    f"Your missing target keywords are: **{missing_kw}**.\n\n"
                                    "- **Direct Experience Alternative**: If you have used equivalent tools or foundational libraries, highlight them explicitly (e.g., *'Built ETL pipelines with Pandas and SQL before adopting Snowflake'*).\n"
                                    "- **Project-Based Demonstration**: Build a quick weekend proof-of-concept repository utilizing these tools and link it in your portfolio/GitHub.\n"
                                    "- **Interview Talking Point**: Emphasize fast ramp-up capability: *'While my primary stack was centered on X, I have frequently transitioned between frameworks within weeks.'*"
                                )
                            elif "90" in lower_q or "score" in lower_q or "raise" in lower_q:
                                ai_reply = (
                                    "### 📈 How to Elevate Your ATS Score to 90%+\n\n"
                                    f"1. **Incorporate Missing Keywords**: Naturally integrate **{missing_kw}** into your project descriptions and skills matrix.\n"
                                    f"2. **Optimize Word Count**: Ensure total resume length sits comfortably between 450 and 850 words (currently **{analysis['word_count']}** words).\n"
                                    f"3. **Standardize Section Headers**: Use conventional titles like `Professional Experience`, `Technical Skills`, and `Education` so parsers never drop a section.\n"
                                    f"4. **Increase Action Verb Ratio**: Replace passive phrasing with verbs like *Architected*, *Optimized*, and *Spearheaded*."
                                )
                            else:
                                ai_reply = (
                                    f"Based on your resume (`{result.file_name}`) and current ATS score of **{analysis['ats_score']}%**:\n\n"
                                    f"- **Top Strengths**: Strong alignment in **{matched_kw}** with crisp formatting.\n"
                                    f"- **High-Value Recommendation**: Adding contextual mentions of **{missing_kw}** will directly boost recruiter scannability and keyword density.\n\n"
                                    "Feel free to ask me to draft specific bullet points or switch to **Mock Interview Simulator** mode to practice live interview questions!"
                                )

                        st.markdown(ai_reply)
                        st.session_state["chat_messages"].append({"role": "assistant", "content": ai_reply})
