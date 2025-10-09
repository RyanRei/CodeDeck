from fastapi import APIRouter, HTTPException, status,Response
from src.models.user_model import UserAuth
from src.schemas.user_schema import UserSchema
from src.db.client import MongoDBClient
from passlib.hash import bcrypt
import jwt
from src.codeDeck.settings import settings
from datetime import datetime, timedelta
from bson import ObjectId
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
async def register_user(user: UserAuth):
    db = MongoDBClient().mongodb

   
    existing_user = await db["users"].find_one({"username": user.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
            
        )

    hashed_pw = bcrypt.hash(user.password)

    user_doc = UserSchema(
        username=user.username,
        password_hash=hashed_pw
    )

    # 4. Convert to dict and insert
    user_dict = user_doc.model_dump(by_alias=True, exclude_none=True)
    await db["users"].insert_one(user_dict)

    # 5. Return success message
    return {"message": "User registered successfully"}




@router.post("/login")
async def login_user(user: UserAuth,response:Response):
    db = MongoDBClient().mongodb
    existing_user = await db["users"].find_one({"username": user.username})
    
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or Password is incorrect"
        )
    
    loggedUser=UserSchema(**existing_user)
    if not bcrypt.verify(user.password,loggedUser.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=" Password is incorrect"
    )
    
    payload={
        "sub":str(loggedUser.id),
        "username":loggedUser.username,
        "expiry": (datetime.now() + timedelta(hours=6)).timestamp()
    }

    jwt_token=jwt.encode(payload=payload,key=settings.JWT_SECRET_KEY,algorithm="HS256")
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        secure=False,  # True in production with HTTPS
        samesite="lax",
        max_age=30 * 60
    )

    return {"message": "Login successful"}
#jwt.encode(payload, SECRET_KEY, algorithm="HS256") → to sign a token

#jwt.decode(token, SECRET_KEY, algorithms=["HS256"])