# models/user_model.py
from pydantic import BaseModel, EmailStr

class UserAuth(BaseModel):
    username: str
    #email: EmailStr
    password: str  # plain text in request (will be hashed before saving)

class UserResponse(BaseModel):
    username: str
    #email: EmailStr
