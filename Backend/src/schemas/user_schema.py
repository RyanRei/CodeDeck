# schemas/user_schema.py
from pydantic import BaseModel, Field
from bson import ObjectId
from src.utils.validator import PyObjectId

class UserSchema(BaseModel):
    id: PyObjectId = Field(default=None, alias="_id")
    username: str
    #email: str
    password_hash: str

    class Config:
        populate_by_name = True
