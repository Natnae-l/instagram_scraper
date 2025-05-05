from fastapi import APIRouter, HTTPException, status
from bson import ObjectId
from config.db import instagram_users,instagram_posts
from schemas.instagram_users import UserBase
from dto.instagram_users import  UserResponse
from validators.instagram_user_validator import UserUpdate
from config.logger import logger

router = APIRouter()


@router.get("/", response_model=list[dict])
def get_users():
    data  =  list(instagram_users.find())
    for doc in data:
        doc["_id"] = str(doc["_id"])
    
    return data

@router.post("/", response_model=UserResponse) 
async def create_users(user: UserBase):
    try:
        user_data = user.dict(exclude_unset=True)
        result = instagram_users.insert_one(user_data)
        
        inserted_user = instagram_users.find_one({"_id": result.inserted_id})
        if not inserted_user:
            raise HTTPException(status_code=404, detail="Failed to retrieve created user")
            
        inserted_user["_id"] = str(inserted_user["_id"])
        
        return {"data":UserBase(**inserted_user)}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{user_id}" )
async def update_user(user_id: str, update_data: UserUpdate):
    try:
        update_fields = {}
        for field, value in update_data.dict(exclude_unset=True).items():
            if value is not None:
                update_fields[field] = value
                
        result = instagram_users.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": update_fields},
            return_document=True
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post with ID {user_id} not found"
            )
        
        result["_id"] = str(result["_id"])
        return {"data": result}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user"
        )

@router.delete("/{user_id}", response_model=dict)
async def delete_user(
    user_id: str,
):
    try:
        logger.info(f"Attempting to delete user with ID: {user_id}")
        try:
            obj_id = ObjectId(user_id)
        except:
            logger.error(f"Invalid user ID format: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        # First check if user exists
        existing_user = instagram_users.find_one({"_id": obj_id})
        
        if not existing_user:
            logger.warning(f"User not found with ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        existing_user['_id']=str(existing_user["_id"])
        
        # Perform deletion
        result = instagram_users.delete_one({"_id": obj_id})
        
        if result.deleted_count == 1:
            logger.info(f"Successfully deleted user with ID: {user_id}")
            
            # Optional: Also delete associated posts
            instagram_posts.delete_many({"instagram_id": existing_user.get("instagram_id")})
            
            
            return {
                "status": "success",
                "message": f"User {user_id} deleted successfully",
                "deleted_user": existing_user,
            }
        else:
            logger.error(f"Failed to delete user with ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User could not be deleted"
            )
            
    except HTTPException:
        raise  # Re-raise FastAPI HTTP exceptions
        
    except Exception as e:
        logger.critical(f"Error deleting user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting user: {str(e)}"
        )