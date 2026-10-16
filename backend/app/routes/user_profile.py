# import logging
# from datetime import datetime, timezone
# from typing import Optional
# from fastapi import APIRouter, HTTPException, Depends
# from pydantic import BaseModel, EmailStr, Field
# from app.database import get_db

# logger = logging.getLogger("brandshield.user")
# router = APIRouter(prefix="/user", tags=["User Profile"])

# # In-memory fallback if MongoDB is not accessible
# DEFAULT_USER = {
#     "_id": "usr_default_01",
#     "id": "usr_default_01",
#     "username": "secops_analyst",
#     "email": "analyst@brandshield.ai",
#     "password": "BrandShield@2026",
#     "full_name": "Security Operations Analyst",
#     "role": "Tier 2 SOC Lead",
#     "organization": "Global SOC Ops",
#     "phone": "+1 (555) 019-2834",
#     "department": "Cyber Digital Risk Protection",
#     "created_at": datetime.now(timezone.utc).isoformat(),
#     "last_login": datetime.now(timezone.utc).isoformat(),
#     "is_active": True
# }

# class UserProfileUpdate(BaseModel):
#     username: Optional[str] = None
#     email: Optional[str] = None
#     password: Optional[str] = None
#     full_name: Optional[str] = None
#     phone: Optional[str] = None
#     department: Optional[str] = None
#     organization: Optional[str] = None

# class CreateAccountRequest(BaseModel):
#     username: str = Field(..., min_length=3)
#     email: str = Field(...)
#     password: str = Field(..., min_length=6)
#     full_name: Optional[str] = None
#     role: Optional[str] = "SOC Analyst"
#     organization: Optional[str] = "Global SOC Ops"

# class ForgotPasswordRequest(BaseModel):
#     email: str
#     new_password: Optional[str] = None
#     verification_code: Optional[str] = None

# from app.services.auth_service import get_current_user
# from app.routes.auth import serialize_user

# @router.get("/profile")
# async def get_profile(
#     current_user: Optional[dict] = Depends(get_current_user),
#     db = Depends(get_db)
# ):
#     """Fetch authenticated user profile or fallback."""
#     if current_user:
#         return serialize_user(current_user)
        
#     try:
#         if db is not None:
#             user = await db.users.find_one({"is_active": True})
#             if user:
#                 return serialize_user(user)
#     except Exception as e:
#         logger.warning(f"DB read failed in get_profile: {e}. Using fallback.")
    
#     return serialize_user(DEFAULT_USER)

# @router.put("/profile")
# async def update_profile(
#     payload: UserProfileUpdate,
#     current_user: Optional[dict] = Depends(get_current_user),
#     db = Depends(get_db)
# ):
#     """Update user profile details for authenticated user."""
#     updates = {k: v for k, v in payload.dict().items() if v is not None}
#     updates["updated_at"] = datetime.now(timezone.utc).isoformat()
#     if "password" in updates and updates["password"]:
#         from app.services.auth_service import hash_password
#         updates["password_hash"] = hash_password(updates["password"])
#         updates["password_changed_at"] = updates["updated_at"]
    
#     try:
#         if db is not None:
#             if current_user:
#                 from bson import ObjectId
#                 uid = current_user["id"]
#                 q = {"_id": ObjectId(uid)} if ObjectId.is_valid(uid) else {"_id": uid}
#                 res = await db.users.find_one_and_update(
#                     q,
#                     {"$set": updates},
#                     return_document=True
#                 )
#             else:
#                 res = await db.users.find_one_and_update(
#                     {"is_active": True},
#                     {"$set": updates},
#                     return_document=True
#                 )
#             if res:
#                 return serialize_user(res)
#     except Exception as e:
#         logger.warning(f"DB update failed in update_profile: {e}")
        
#     # Update in-memory fallback
#     DEFAULT_USER.update(updates)
#     return serialize_user(DEFAULT_USER)

# @router.post("/create-account")
# async def create_account(payload: CreateAccountRequest, db = Depends(get_db)):
#     """Create a new user account and set it as the active profile."""
#     now = datetime.now(timezone.utc).isoformat()
#     new_user = {
#         "username": payload.username.strip(),
#         "email": payload.email.strip().lower(),
#         "password": payload.password,
#         "full_name": payload.full_name or payload.username,
#         "role": payload.role or "SOC Analyst",
#         "organization": payload.organization or "Global SOC Ops",
#         "phone": "+1 (555) 012-3456",
#         "department": "Digital Risk Protection",
#         "created_at": now,
#         "last_login": now,
#         "is_active": True
#     }
    
#     try:
#         if db is not None:
#             # Set other users to inactive
#             await db.users.update_many({}, {"$set": {"is_active": False}})
#             res = await db.users.insert_one(new_user)
#             new_user["id"] = str(res.inserted_id)
#             new_user.pop("_id", None)
#             return {
#                 "success": True,
#                 "message": f"Account '{new_user['username']}' successfully created and activated.",
#                 "user": new_user
#             }
#     except Exception as e:
#         logger.warning(f"DB insert failed in create_account: {e}")

#     # Fallback
#     DEFAULT_USER.clear()
#     DEFAULT_USER.update(new_user)
#     DEFAULT_USER["id"] = f"usr_{int(datetime.now().timestamp())}"
#     return {
#         "success": True,
#         "message": f"Account '{new_user['username']}' successfully created.",
#         "user": DEFAULT_USER
#     }

# @router.post("/forgot-password")
# async def forgot_password(payload: ForgotPasswordRequest, db = Depends(get_db)):
#     """Handle password reset / forgot password flow."""
#     target_email = payload.email.strip().lower()
    
#     try:
#         if db is not None:
#             user = await db.users.find_one({"email": {"$regex": f"^{target_email}$", "$options": "i"}})
#             if not user:
#                 # If exact email not found, check active user
#                 user = await db.users.find_one({"is_active": True})
            
#             if user:
#                 if payload.new_password:
#                     await db.users.update_one(
#                         {"_id": user["_id"]},
#                         {"$set": {"password": payload.new_password, "updated_at": datetime.now(timezone.utc).isoformat()}}
#                     )
#                     return {
#                         "success": True,
#                         "message": f"Password for {user.get('email', target_email)} has been successfully reset!",
#                         "username": user.get("username"),
#                         "email": user.get("email"),
#                         "new_password": payload.new_password
#                     }
#                 else:
#                     return {
#                         "success": True,
#                         "message": f"Verification code sent to {target_email}. Use code 'DRP-9842' or enter your new password to complete reset.",
#                         "verification_code": "DRP-9842",
#                         "username": user.get("username")
#                     }
#     except Exception as e:
#         logger.warning(f"DB failed in forgot_password: {e}")
        
#     # In-memory fallback
#     if payload.new_password:
#         DEFAULT_USER["password"] = payload.new_password
#         return {
#             "success": True,
#             "message": f"Password for {DEFAULT_USER['email']} has been successfully reset!",
#             "username": DEFAULT_USER["username"],
#             "email": DEFAULT_USER["email"],
#             "new_password": payload.new_password
#         }
#     return {
#         "success": True,
#         "message": f"Verification code sent to {target_email}. Use code 'DRP-9842' or enter your new password to complete reset.",
#         "verification_code": "DRP-9842",
#         "username": DEFAULT_USER["username"]
#     }


import logging
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import get_db
from app.services.auth_service import get_current_user
from app.routes.auth import serialize_user

logger = logging.getLogger("brandshield.user")

router = APIRouter(prefix="/user", tags=["User Profile"])


class UserProfileUpdate(BaseModel):
    # Only ordinary profile fields can be changed here.
    # Password, role, account status, and email changes require
    # separate secure flows.
    username: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    organization: Optional[str] = None


class CreateAccountRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = None
    organization: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: str
    new_password: Optional[str] = None
    verification_code: Optional[str] = None


def require_user(current_user: Optional[dict]) -> dict:
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please sign in.",
        )
    return current_user


def get_user_id(user: dict) -> str:
    user_id = user.get("_id") or user.get("id")

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid user session.",
        )

    return str(user_id)


def get_user_query(user_id: str) -> dict:
    if ObjectId.is_valid(user_id):
        return {"_id": ObjectId(user_id)}

    return {"_id": user_id}


@router.get("/profile")
async def get_profile(
    current_user: Optional[dict] = Depends(get_current_user),
    db=Depends(get_db),
):
    """Return only the signed-in user's profile."""
    user = require_user(current_user)

    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable. Please try again later.",
        )

    user_id = get_user_id(user)

    try:
        stored_user = await db.users.find_one(get_user_query(user_id))
    except Exception:
        logger.exception("Unable to load authenticated user profile")
        raise HTTPException(
            status_code=503,
            detail="Unable to load your profile right now.",
        )

    if not stored_user:
        raise HTTPException(
            status_code=404,
            detail="User profile not found.",
        )

    return serialize_user(stored_user)


@router.put("/profile")
async def update_profile(
    payload: UserProfileUpdate,
    current_user: Optional[dict] = Depends(get_current_user),
    db=Depends(get_db),
):
    """Update safe profile fields for the signed-in user only."""
    user = require_user(current_user)

    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable. Please try again later.",
        )

    user_id = get_user_id(user)
    updates = {
        key: value
        for key, value in payload.dict(exclude_unset=True).items()
        if value is not None
    }

    if "username" in updates:
        updates["username"] = updates["username"].strip()
        if len(updates["username"]) < 3:
            raise HTTPException(
                status_code=400,
                detail="Username must contain at least 3 characters.",
            )

    if "full_name" in updates and updates["full_name"] is not None:
        updates["full_name"] = updates["full_name"].strip()

    if not updates:
        raise HTTPException(
            status_code=400,
            detail="No profile changes were provided.",
        )

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    try:
        result = await db.users.update_one(
            get_user_query(user_id),
            {"$set": updates},
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=404,
                detail="User profile not found.",
            )

        updated_user = await db.users.find_one(get_user_query(user_id))

    except HTTPException:
        raise
    except Exception:
        logger.exception("Unable to update authenticated user profile")
        raise HTTPException(
            status_code=500,
            detail="Unable to update your profile right now.",
        )

    return serialize_user(updated_user)


@router.post("/create-account")
async def create_account(
    payload: CreateAccountRequest,
):
    """
    Disabled intentionally.

    Use the application's secure registration flow instead.
    This endpoint must not deactivate other users or store plaintext passwords.
    """
    raise HTTPException(
        status_code=501,
        detail=(
            "Account creation through this endpoint is disabled. "
            "Use the configured secure registration flow."
        ),
    )


@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
):
    """
    Disabled intentionally until a verified password-reset flow is configured.
    Never return passwords or fixed verification codes from an API.
    """
    raise HTTPException(
        status_code=501,
        detail=(
            "Password reset through this endpoint is not configured. "
            "Use the application's verified password-reset flow."
        ),
    )