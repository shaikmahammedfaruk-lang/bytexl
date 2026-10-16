# import re
# import logging
# from datetime import datetime, timezone
# from typing import Optional, Dict, Any
# from fastapi import APIRouter, HTTPException, Depends
# from pydantic import BaseModel, Field

# from app.database import get_db
# from app.services.auth_service import require_current_user
# from app.routes.auth import serialize_user, EMAIL_REGEX

# logger = logging.getLogger("brandshield.routes.users")
# router = APIRouter(prefix="/users", tags=["Users"])

# class UpdateProfileRequest(BaseModel):
#     full_name: Optional[str] = None
#     username: Optional[str] = None
#     phone: Optional[str] = None
#     organization: Optional[str] = None
#     department: Optional[str] = None
#     avatar_url: Optional[str] = None
#     email: Optional[str] = None

# @router.get("/me")
# async def get_current_user_profile(user: Dict[str, Any] = Depends(require_current_user)):
#     """Returns the authenticated user's current profile record."""
#     return serialize_user(user)

# @router.patch("/me")
# @router.put("/me")
# async def update_current_user_profile(
#     payload: UpdateProfileRequest,
#     current_user: Dict[str, Any] = Depends(require_current_user),
#     db = Depends(get_db)
# ):
#     """
#     Updates the authenticated user's editable profile fields.
#     User ID is securely resolved from the verified session token.
#     """
#     user_id = current_user["id"]
#     updates = {}

#     if payload.full_name is not None:
#         cleaned_name = payload.full_name.strip()
#         if len(cleaned_name) < 2:
#             raise HTTPException(status_code=400, detail="Full name must be at least 2 characters long.")
#         updates["full_name"] = cleaned_name

#     if payload.username is not None:
#         cleaned_username = payload.username.strip().lower()
#         if not re.match(r"^[a-zA-Z0-9_.-]{3,30}$", cleaned_username):
#             raise HTTPException(
#                 status_code=400,
#                 detail="Username must be 3-30 characters and contain only letters, numbers, underscores, dots, or dashes."
#             )
#         # Check uniqueness if username changed
#         if cleaned_username != current_user.get("username", "").lower():
#             if db is not None:
#                 from bson import ObjectId
#                 q_id = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
#                 existing = await db.users.find_one({"username": cleaned_username, "_id": {"$ne": q_id}})
#                 if existing:
#                     raise HTTPException(status_code=400, detail="This username is already taken. Please choose another handle.")
#             updates["username"] = cleaned_username

#     if payload.email is not None:
#         cleaned_email = payload.email.strip().lower()
#         if not re.match(EMAIL_REGEX, cleaned_email):
#             raise HTTPException(status_code=400, detail="Invalid email address format.")
#         if cleaned_email != current_user.get("email", "").lower():
#             if db is not None:
#                 from bson import ObjectId
#                 q_id = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
#                 existing = await db.users.find_one({"email": cleaned_email, "_id": {"$ne": q_id}})
#                 if existing:
#                     raise HTTPException(status_code=400, detail="An account with this email address is already registered.")
#             updates["email"] = cleaned_email
#             updates["email_verified"] = False  # Changed email requires re-verification

#     if payload.phone is not None:
#         updates["phone"] = payload.phone.strip()

#     if payload.organization is not None:
#         updates["organization"] = payload.organization.strip()

#     if payload.department is not None:
#         updates["department"] = payload.department.strip()

#     if payload.avatar_url is not None:
#         updates["avatar_url"] = payload.avatar_url.strip()

#     updates["updated_at"] = datetime.now(timezone.utc).isoformat()

#     if db is not None:
#         from bson import ObjectId
#         q_id = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
#         await db.users.update_one({"_id": q_id}, {"$set": updates})
#         updated_doc = await db.users.find_one({"_id": q_id})
#         if updated_doc:
#             return serialize_user(updated_doc)

#     merged = {**current_user, **updates}
#     return serialize_user(merged)



import re
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.database import get_db
from app.services.auth_service import require_current_user
from app.routes.auth import serialize_user

logger = logging.getLogger("brandshield.routes.users")
router = APIRouter(prefix="/users", tags=["Users"])

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=30)
    phone: Optional[str] = Field(None, max_length=30)
    organization: Optional[str] = Field(None, max_length=150)
    department: Optional[str] = Field(None, max_length=150)
    avatar_url: Optional[str] = Field(None, max_length=2048)
    email: Optional[str] = Field(None, max_length=254)


def get_user_query(user_id: str) -> dict:
    """Resolve the authenticated user's MongoDB ID safely."""
    if ObjectId.is_valid(user_id):
        return {"_id": ObjectId(user_id)}
    return {"_id": user_id}


def require_database(db):
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="User profile service is temporarily unavailable.",
        )


@router.get("/me")
async def get_current_user_profile(
    user: Dict[str, Any] = Depends(require_current_user),
):
    """Return the authenticated user's profile."""
    return serialize_user(user)


@router.patch("/me")
@router.put("/me")
async def update_current_user_profile(
    payload: UpdateProfileRequest,
    current_user: Dict[str, Any] = Depends(require_current_user),
    db=Depends(get_db),
):
    """Update only editable fields belonging to the authenticated user."""
    require_database(db)

    user_id = str(current_user.get("id", ""))
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Unable to identify the authenticated user.",
        )

    user_query = get_user_query(user_id)
    stored_user = await db.users.find_one(user_query)

    if not stored_user or stored_user.get("is_active", True) is not True:
        raise HTTPException(
            status_code=401,
            detail="Your account is unavailable. Please sign in again.",
        )

    updates = {}

    if payload.full_name is not None:
        cleaned_name = payload.full_name.strip()
        if len(cleaned_name) < 2:
            raise HTTPException(
                status_code=400,
                detail="Full name must contain at least 2 characters.",
            )
        updates["full_name"] = cleaned_name

    if payload.username is not None:
        cleaned_username = payload.username.strip().lower()

        if not re.fullmatch(r"[a-zA-Z0-9_.-]{3,30}", cleaned_username):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Username must be 3-30 characters and contain only "
                    "letters, numbers, underscores, dots, or dashes."
                ),
            )

        if cleaned_username != str(stored_user.get("username", "")).lower():
            existing = await db.users.find_one({
                "username": cleaned_username,
                "_id": {"$ne": stored_user["_id"]},
            })

            if existing:
                raise HTTPException(
                    status_code=409,
                    detail="This username is already taken.",
                )

            updates["username"] = cleaned_username

    if payload.email is not None:
        cleaned_email = payload.email.strip().lower()

        if not re.fullmatch(EMAIL_REGEX, cleaned_email):
            raise HTTPException(
                status_code=400,
                detail="Invalid email address format.",
            )

        if cleaned_email != str(stored_user.get("email", "")).lower():
            # The current verification flow does not securely support
            # changing an account's email address. Do not change it and
            # leave the user with an unverifiable or mismatched account.
            raise HTTPException(
                status_code=400,
                detail=(
                    "Email changes are not currently supported. "
                    "Keep your existing email address."
                ),
            )

    if payload.phone is not None:
        updates["phone"] = payload.phone.strip() or None

    if payload.organization is not None:
        updates["organization"] = payload.organization.strip() or None

    if payload.department is not None:
        updates["department"] = payload.department.strip() or None

    if payload.avatar_url is not None:
        cleaned_avatar = payload.avatar_url.strip()

        if cleaned_avatar and not (
            cleaned_avatar.startswith("https://")
            or cleaned_avatar.startswith("http://")
        ):
            raise HTTPException(
                status_code=400,
                detail="Avatar URL must use HTTP or HTTPS.",
            )

        updates["avatar_url"] = cleaned_avatar or None

    if not updates:
        return serialize_user(stored_user)

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    try:
        await db.users.update_one(
            {"_id": stored_user["_id"]},
            {"$set": updates},
        )

        updated_doc = await db.users.find_one(
            {"_id": stored_user["_id"]}
        )

    except Exception:
        logger.exception("Unable to update user profile.")
        raise HTTPException(
            status_code=503,
            detail="Unable to save your profile changes. Please try again.",
        )

    if not updated_doc:
        raise HTTPException(
            status_code=503,
            detail="Profile update could not be confirmed.",
        )

    return serialize_user(updated_doc)