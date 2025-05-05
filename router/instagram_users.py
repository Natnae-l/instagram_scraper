from fastapi import APIRouter, HTTPException

from config.db import instagram_users
from schemas.instagram_users import UserBase
from dto.instagram_users import UserListResponse, UserResponse

router = APIRouter()


@router.get("/", response_model=UserListResponse)
def get_users():
    data  =  list(instagram_users.find())
    for doc in data:
        doc["_id"] = str(doc["_id"])
    
    return {"data": data}

@router.post("/", response_model=UserResponse) 
async def create_users(user: UserBase):
    try:
        user_data = user.dict(exclude_unset=True)
        result = instagram_users.insert_one(user_data)
        
        inserted_user = instagram_users.find_one({"_id": result.inserted_id})
        if not inserted_user:
            raise HTTPException(status_code=500, detail="Failed to retrieve created user")
            
        inserted_user["_id"] = str(inserted_user["_id"])
        return {"data":UserBase(**inserted_user)}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))