from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from contextlib import asynccontextmanager
from .api.authentication import router as auth_router
from fastapi.middleware.cors import CORSMiddleware

from .db.dbutil import get_mongoDb
from .api.geeksforgeeks import router as g4g_router
from .api.codeforces import router as cf_router
from .api.codingPlatform import router as cp_router

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import os
from dotenv import load_dotenv
import asyncio
import logging
# Import the loader
from src.schemas.problem_loader import load_problems, problem_db, Problem, TestCase

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


origins = [
    "http://localhost:3000",  # frontend URL
]

@asynccontextmanager
async def lifespan(app: FastAPI):
   """
   Handles application startup and shutdown events.
   """
   # Load problems into memory
   current_dir = os.path.dirname(os.path.abspath(__file__))
   file_path = os.path.join(current_dir, "schemas", "problems.jsonl")
   load_problems(file_path)
    
   # Initialize MongoDB connection
   mongodb = await get_mongoDb()
   app.mongodb = mongodb
    
   yield
    
   # Clean up resources if needed on shutdown
   # (e.g., close database connections)

app=FastAPI(lifespan=lifespan)
app.include_router(auth_router)
app.include_router(g4g_router)
app.include_router(cf_router)
app.include_router(cp_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Application": "CodeDeck"}











