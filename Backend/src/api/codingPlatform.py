# main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import asyncio
import logging

# Import the loader
from src.schemas.problem_loader import load_problems, problem_db, Problem, TestCase
from src.codeDeck.settings import settings

router = APIRouter(prefix="", tags=["codingPlatform"])
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Environment Variables ---
JUDGE0_URL = settings.JUDGE0_URL
JUDGE0_API_KEY = settings.JUDGE0_API_KEY
JUDGE0_RAPIDAPI_HOST = settings.JUDGE0_RAPIDAPI_HOST

# --- Models ---

class SubmissionRequest(BaseModel):
    source_code: str
    language_id: int
    stdin: Optional[str] = ""
    expected_output: Optional[str] = None
    cpu_time_limit: Optional[float] = 5
    memory_limit: Optional[int] = 128000

class SubmitCodeRequest(BaseModel):
    source_code: str
    language_id: int
    cpu_time_limit: Optional[float] = 5
    memory_limit: Optional[int] = 128000

class PublicTestCase(BaseModel):
    input: str
    output: str

# NEW: Model for the list view (lighter weight)
class ProblemSummary(BaseModel):
    id: int
    title: str
    difficulty: str

class ProblemResponse(BaseModel):
    id: int
    title: str # Added title here
    question: str
    difficulty: str
    public_cases: List[PublicTestCase]

class SubmitResultResponse(BaseModel):
    passed: int
    total: int
    message: str = "Submission processed"

class SubmissionResponse(BaseModel):
    token: str
    status: dict
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    compile_output: Optional[str] = None
    time: Optional[str] = None
    memory: Optional[int] = None
    message: Optional[str] = None

class LanguageResponse(BaseModel):
    id: int
    name: str
    judge0_id: int
    

async def call_judge0_api(endpoint: str, method: str = "GET", data: dict = None):
    headers = {"Content-Type": "application/json"}

    if "rapidapi.com" in JUDGE0_URL:
        headers["X-RapidAPI-Key"] = JUDGE0_API_KEY
        headers["X-RapidAPI-Host"] = JUDGE0_RAPIDAPI_HOST
    elif JUDGE0_API_KEY:
        headers["X-Auth-Token"] = JUDGE0_API_KEY

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{JUDGE0_URL}{endpoint}"
        try:
            if method == "GET":
                resp = await client.get(url, headers=headers)
            else:
                resp = await client.post(url, json=data, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Judge0 API error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Judge0 API Error: {e.response.text}")
        except Exception as e:
            logger.error(f"Error calling Judge0: {e}")
            raise HTTPException(status_code=500, detail=f"Error connecting to Judge0: {str(e)}")


# --- NEW: Get All Problems Endpoint ---
@router.get("/problems", response_model=List[ProblemSummary], tags=["Problems"])
async def get_all_problems(skip: int = 0, limit: int = 50):
    """
    Get a list of problems with pagination.
    Returns ID, Title, and Difficulty only.
    """
    # Convert dict values to a list and sort by ID
    all_problems = sorted(problem_db.values(), key=lambda x: x['id'])
    
    # Apply pagination
    paged_problems = all_problems[skip : skip + limit]
    
    return [
        ProblemSummary(
            id=p['id'],
            title=p['title'],
            difficulty=p['difficulty']
        )
        for p in paged_problems
    ]

# --- Get Single Problem Endpoint ---
@router.get("/problem/{problem_id}", response_model=ProblemResponse, tags=["Problems"])
async def get_problem(problem_id: int):
    """
    Get a specific problem by its ID.
    """
    problem = problem_db.get(problem_id-1)
    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem with id {problem_id} not found.")
    
    return ProblemResponse(
        id=problem['id'],
        title=problem['title'], # Included in response
        question=problem['question'],
        difficulty=problem['difficulty'],
        public_cases=[
            PublicTestCase(input=case['input'], output=case['output'])
            for case in problem['public_cases']
        ]
    )

# --- Submit to Problem Endpoint ---
@router.post("/submit/{problem_id}", response_model=SubmitResultResponse, tags=["Problems"])
async def submit_to_problem(
    problem_id: int, 
    request: SubmitCodeRequest,
    subset: str = Query("all")
):
    """
    Submits code to a specific problem.
    """
    problem = problem_db.get(problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found.")

    if subset not in ["public", "all"]:
        subset = "all"

    if subset == "public":
        test_cases = problem['public_cases']
    else:
        hidden = problem.get('hidden_cases', [])
        test_cases = problem['public_cases'] + hidden

    if not test_cases:
        return SubmitResultResponse(passed=0, total=0, message="No test cases available for this selection.")

    tasks = []
    for case in test_cases:
        payload = {
            "source_code": request.source_code,
            "language_id": request.language_id,
            "stdin": case['input'],
            "expected_output": case['output'],
            "cpu_time_limit": request.cpu_time_limit,
            "memory_limit": request.memory_limit,
        }
        tasks.append(
            call_judge0_api(
                "/submissions?wait=true&base64_encoded=false",
                method="POST",
                data=payload
            )
        )

    try:
        results = await asyncio.gather(*tasks)
    except HTTPException as e:
        return SubmitResultResponse(
            passed=0, 
            total=len(test_cases), 
            message=f"Execution failed: {e.detail}"
        )

    passed_count = 0
    first_fail_message = ""
    for res in results:
        status_id = res.get("status", {}).get("id")
        if status_id == 3:
            passed_count += 1
        elif not first_fail_message:
            first_fail_message = res.get("status", {}).get("description", "Test case failed")

    return SubmitResultResponse(
        passed=passed_count,
        total=len(test_cases),
        message=first_fail_message if passed_count != len(test_cases) else "All selected test cases passed!"
    )

# --- Languages ---
@router.get("/languages", response_model=list[LanguageResponse], tags=["Languages"])
async def get_languages():
    try:
        languages = await call_judge0_api("/languages")
        result = []
        for lang in languages:
            result.append({
                "id": lang.get("id"),
                "name": lang.get("name"),
                "judge0_id": lang.get("id"),
            })
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching languages: {str(e)}")

# --- Execute (Raw) ---
@router.post("/execute", response_model=SubmissionResponse, tags=["Code Execution"])
async def execute_code(request: SubmissionRequest):
    try:
        payload = {
            "source_code": request.source_code,
            "language_id": request.language_id,
            "stdin": request.stdin if request.stdin else None,
            "expected_output": request.expected_output,
            "cpu_time_limit": request.cpu_time_limit,
            "memory_limit": request.memory_limit,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        result = await call_judge0_api(
            "/submissions?wait=true&base64_encoded=false",
            method="POST",
            data=payload
        )
        if "token" not in result and result.get("token"):
             result["token"] = result.get("token")
        
        return SubmissionResponse(
            token=result.get("token"),
            status=result.get("status"),
            stdout=result.get("stdout"),
            stderr=result.get("stderr"),
            compile_output=result.get("compile_output"),
            time=result.get("time"),
            memory=result.get("memory"),
            message=result.get("message"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing code: {str(e)}")

# --- Get Submission ---
@router.get("/submission/{token}", response_model=SubmissionResponse, tags=["Code Execution"])
async def get_submission(token: str):
    try:
        result = await call_judge0_api(f"/submissions/{token}?base64_encoded=false")
        return SubmissionResponse(
            token=result.get("token"),
            status=result.get("status"),
            stdout=result.get("stdout"),
            stderr=result.get("stderr"),
            compile_output=result.get("compile_output"),
            time=result.get("time"),
            memory=result.get("memory"),
            message=result.get("message"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching submission: {str(e)}")

@router.get("/debug-env")
async def debug_env():
    return {
    "JUDGE0_URL": JUDGE0_URL,
    "JUDGE0_API_KEY_set": bool(JUDGE0_API_KEY),
    "JUDGE0_RAPIDAPI_HOST": JUDGE0_RAPIDAPI_HOST
    }
