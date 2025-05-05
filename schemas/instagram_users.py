from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class InstagramUser(BaseModel):
    username: str

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=30, pattern="^[a-zA-Z0-9_.]+$")
    email: EmailStr
    full_name: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=150)
    profile_pic: Optional[str] = None
    is_private: Optional[bool] = False
    followers_count: int = Field(0, ge=0)
    following_count: int = Field(0, ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)