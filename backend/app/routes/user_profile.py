
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