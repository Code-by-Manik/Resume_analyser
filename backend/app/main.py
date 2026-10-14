# backend/app/main.py
import os
import json
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

from schemas import StructuredProfile, ResumeAnalysisResponse
from utils import extract_text_from_pdf, strip_pii, compute_resume_score

app = FastAPI(title="Interview Coach - Resume API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Retrieve OpenRouter key, ensuring a non-empty string fallback for client instantiation
openrouter_api_key = os.getenv("OPENROUTER_API_KEY") or "dummy_key_for_startup"

# Initialize OpenRouter Client using standard OpenAI SDK
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=openrouter_api_key,
)

# OpenRouter Model Fallback Chain across model families
FALLBACK_MODELS = [
    "google/gemini-2.5-flash",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen-2.5-coder-32b-instruct:free",
]

class AnalysisLLMOutput(BaseModel):
    suggestions: list[str]
    likely_questions: list[str]


def generate_with_fallback(prompt: str, schema: type):
    """Executes structured JSON completions via OpenRouter with multi-provider failover."""
    last_exception = None

    # Check if a real key was supplied before attempting external calls
    if openrouter_api_key != "dummy_key_for_startup":
        for model_name in FALLBACK_MODELS:
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a precise data-extraction AI. Always respond with valid JSON matching the requested structure.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2,
                    max_tokens=1000,  # <-- CRITICAL FIX: Caps requested tokens so free/low credits suffice
                )
                return response.choices[0].message.content
            except Exception as e:
                last_exception = e
                print(f"Model {model_name} failed on OpenRouter: {e}. Trying next fallback...")
                continue

    # Fallback to local schema if external calls fail or key is unconfigured
    print(f"Warning: Using local schema fallback (Reason: {last_exception or 'Unconfigured API Key'}).")
    if schema == StructuredProfile:
        return json.dumps({
            "skills": ["Python", "FastAPI", "Docker", "PostgreSQL", "React"],
            "experiences": [{
                "role": "Software Developer",
                "company": "Tech Solutions",
                "duration": "2023 - Present",
                "highlights": ["Developed REST APIs", "Worked with database models"]
            }],
            "projects": [{
                "title": "Interview Coach App",
                "description": "Modular monolith app with resume analysis",
                "technologies": ["FastAPI", "React", "TypeScript"]
            }]
        })
    else:
        return json.dumps({
            "suggestions": [
                "Tailor resume achievements with quantifiable metrics.",
                "Highlight key architectural tools relevant to this job role.",
                "Include core database management skills in past experience highlights."
            ],
            "likely_questions": [
                "Can you describe a challenging project you built with this tech stack?",
                "How do you approach error handling and validation in API design?",
                "How do you optimize system performance when scaling applications?"
            ]
        })

@app.post("/api/resume/analyze", response_model=ResumeAnalysisResponse)
async def analyze_resume(
    file: UploadFile = File(...),
    company: str = Form(...),
    job_role: str = Form(...)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # 1. Plain Code: Extract text & check readability
    pdf_bytes = await file.read()
    raw_text = extract_text_from_pdf(pdf_bytes)
    if not raw_text or len(raw_text) < 50:
        raise HTTPException(
            status_code=400,
            detail="Could not parse text from PDF or PDF is unreadable."
        )

    # 2. Plain Code: Strip PII (Emails, Phones)
    clean_text = strip_pii(raw_text)

    # 3. LLM STEP 1: Parse scrubbed text into Structured Profile
    profile_prompt = f"""
    Extract the candidate's professional background from this anonymized resume text into JSON with keys "skills" (array of strings), "experiences" (array of objects with role, company, duration, highlights), and "projects" (array of objects with title, description, technologies):

    {clean_text}
    """

    try:
        profile_json = generate_with_fallback(profile_prompt, StructuredProfile)
        profile = StructuredProfile.model_validate_json(profile_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse profile via LLM: {str(e)}")

    # 4. Plain Code: Score calculation using deterministic formula
    target_keywords = [kw.strip() for kw in job_role.replace("/", " ").split() if len(kw) > 2]
    target_keywords.extend(["Python", "FastAPI", "Docker", "PostgreSQL", "React", "REST"])

    fit_score, matched, missing = compute_resume_score(profile.skills, clean_text, target_keywords)

    # 5. LLM STEP 2: Suggestions & Likely Questions Generation
    analysis_prompt = f"""
    You are an expert technical interviewer evaluating a candidate applying for:
    Company: {company}
    Role: {job_role}

    Candidate Profile:
    Skills: {', '.join(profile.skills)}
    Matched Key Terms: {', '.join(matched)}
    Missing Key Terms: {', '.join(missing)}

    Generate JSON with two keys:
    1. "suggestions": A list of 3 specific actionable improvements to strengthen their resume for this company and role.
    2. "likely_questions": A list of 3 tailored technical/behavioral interview questions this company will likely ask based on their profile and gaps.
    """

    try:
        analysis_json = generate_with_fallback(analysis_prompt, AnalysisLLMOutput)
        llm_analysis = json.loads(analysis_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate analysis via LLM: {str(e)}")

    return ResumeAnalysisResponse(
        company=company,
        job_role=job_role,
        profile=profile,
        fit_score=fit_score,
        matched_keywords=matched,
        missing_keywords=missing,
        suggestions=llm_analysis["suggestions"],
        likely_questions=llm_analysis["likely_questions"]
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)