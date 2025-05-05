from pydantic import BaseModel
from typing import List

from schemas.instagram_users import UserBase

class UserListResponse(BaseModel):
    data: List[UserBase]

class UserResponse(BaseModel):
    data: UserBase

    

