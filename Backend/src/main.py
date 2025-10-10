from fastapi import FastAPI
from contextlib import asynccontextmanager
from .api.authentication import router as auth_router
from fastapi.middleware.cors import CORSMiddleware

from .db.dbutil import get_mongoDb
from .api.geeksforgeeks import router as g4g_router
from .api.codeforces import router as cf_router

origins = [
    "http://localhost:3000",  # frontend URL
]

@asynccontextmanager
async def lifespan(app: FastAPI):
   mongodb=await get_mongoDb()
   app.mongodb=mongodb
   yield

app=FastAPI(lifespan=lifespan)
app.include_router(auth_router)
app.include_router(g4g_router)
app.include_router(cf_router)




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











