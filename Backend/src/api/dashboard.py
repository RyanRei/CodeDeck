from fastapi import APIRouter, Cookie, HTTPException
from bson import ObjectId
import jwt
from src.db.client import MongoDBClient
from src.codeDeck.settings import settings

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"

router = APIRouter(prefix="/dashboard", tags=["dashboard"])



@router.get("/dashboard/{username}")
async def user_dashboard(username: str, access_token: str = Cookie(None)):
    db = MongoDBClient().mongodb
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        logged_in_user_id = payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 3. Fetch user from DB
    logged_in_user = await db["users"].find_one({"_id": ObjectId(logged_in_user_id)})
    if not logged_in_user:
        raise HTTPException(status_code=404, detail="User not found")

    # 4. Check if URL username matches logged-in user
    if logged_in_user["username"] != username:
        raise HTTPException(status_code=403, detail="Access forbidden")

    # 5. Return dashboard data specific to this user
    dashboard_data = {
        "username": logged_in_user["username"],
        "stats": "User-specific stats here",
        "projects": []  # fetch user projects from DB if needed
    }
    return dashboard_data
