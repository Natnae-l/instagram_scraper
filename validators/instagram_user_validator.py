from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserUpdate(BaseModel):
    username: Optional[str] = Field(
        None, min_length=3, max_length=30, pattern="^[a-zA-Z0-9_.]+$",)
    email: Optional[EmailStr] = None
    instagram_id: Optional[int] = None
    scrape: Optional[bool] = True
    full_name: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=150)
    profile_pic: Optional[str] = None
    is_private: Optional[bool] = False
    followers_count: Optional[int] = Field(0, ge=0)
    following_count: Optional[int] = Field(0, ge=0)
