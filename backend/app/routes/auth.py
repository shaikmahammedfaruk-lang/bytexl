# import re
# import secrets
# import logging
# import uuid
# from datetime import datetime, timedelta, timezone
# from typing import Optional, List, Dict, Any
# from fastapi import APIRouter, HTTPException, Depends, status, Request
# from pydantic import BaseModel, EmailStr, Field
# from bson import ObjectId

# from app.database import get_db
# from app.config import settings
# from app.services.auth_service import (
#     hash_password,
#     verify_password,
#     validate_password_strength,
#     create_access_token,
#     generate_secure_token,
#     hash_token,
#     get_current_user,
#     require_current_user,
#     send_email_notification,
#     verify_google_id_token
# )

# logger = logging.getLogger("brandshield.routes.auth")
# router = APIRouter(prefix="/auth", tags=["Authentication"])

# def serialize_user(user: dict) -> dict:
#     if not user:
#         return {}
#     res = dict(user)
#     res["id"] = str(res.pop("_id", res.get("id", "")))
#     res.pop("password_hash", None)
#     res.pop("password", None)
#     res.pop("token_hash", None)
    
#     # Ensure expected profile keys exist with safe dynamic defaults
#     res.setdefault("full_name", "")
#     res.setdefault("username", "")
#     res.setdefault("email", "")
#     res.setdefault("role", "SOC Analyst")
#     res.setdefault("organization", None)
#     res.setdefault("department", None)
#     res.setdefault("phone", None)
#     res.setdefault("avatar_url", None)
#     res.setdefault("provider", "local")
#     res.setdefault("email_verified", False)
#     res.setdefault("two_factor_enabled", False)
#     res.setdefault("is_active", True)
#     res.setdefault("created_at", None)
#     res.setdefault("last_login", None)
#     res.setdefault("password_changed_at", None)
#     return res

# # --- REQUEST SCHEMAS ---

# EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

# class RegisterRequest(BaseModel):
#     full_name: str = Field(..., min_length=2, max_length=100)
#     email: str
#     password: str = Field(..., min_length=8)
#     confirm_password: str
#     terms_accepted: bool = Field(..., description="Must accept terms and privacy policy")

# class LoginRequest(BaseModel):
#     email: str
#     password: str

# class GoogleAuthRequest(BaseModel):
#     id_token: str = Field(..., min_length=1)

# class ForgotPasswordRequest(BaseModel):
#     email: str

# class ValidateTokenRequest(BaseModel):
#     token: str
#     email: str

# class ResetPasswordRequest(BaseModel):
#     token: str
#     email: str
#     new_password: str = Field(..., min_length=8)
#     confirm_password: str

# class ChangePasswordRequest(BaseModel):
#     current_password: str
#     new_password: str = Field(..., min_length=8)
#     confirm_password: str

# # --- ENDPOINTS ---

# @router.post("/register")
# async def register_user(payload: RegisterRequest, db = Depends(get_db)):
#     """Registers a new user account with secure password hashing and verification."""
#     if not payload.terms_accepted:
#         raise HTTPException(
#             status_code=400,
#             detail="You must accept the Terms of Service and Privacy Policy to create an account."
#         )

#     if payload.password != payload.confirm_password:
#         raise HTTPException(status_code=400, detail="Passwords do not match.")

#     is_strong, msg = validate_password_strength(payload.password)
#     if not is_strong:
#         raise HTTPException(status_code=400, detail=msg)

#     clean_email = payload.email.strip().lower()
#     if not re.match(EMAIL_REGEX, clean_email):
#         raise HTTPException(status_code=400, detail="Invalid email address format.")
    
#     # Check if user already exists
#     if db is not None:
#         existing_user = await db.users.find_one({"email": clean_email})
#         if existing_user:
#             raise HTTPException(
#                 status_code=400,
#                 detail="An account with this email address is already registered. Please sign in instead."
#             )

#     now = datetime.now(timezone.utc).isoformat()
#     pw_hash = hash_password(payload.password)
    
#     # Derive username from full name or email
#     base_user = re.sub(r'[^a-zA-Z0-9_]', '', payload.full_name.lower().replace(' ', '_')) or clean_email.split('@')[0]
#     username = f"{base_user}_{secrets.token_hex(2)}"

#     user_doc = {
#         "username": username,
#         "email": clean_email,
#         "password_hash": pw_hash,
#         "full_name": payload.full_name.strip(),
#         "role": "SOC Analyst",
#         "organization": "Global SOC Ops",
#         "department": "Digital Risk Protection",
#         "provider": "local",
#         "email_verified": not settings.REQUIRE_EMAIL_VERIFICATION,
#         "is_active": True,
#         "created_at": now,
#         "last_login": now
#     }

#     user_id = str(uuid.uuid4().hex[:12])
#     if db is not None:
#         ins = await db.users.insert_one(user_doc)
#         user_id = str(ins.inserted_id)
#         user_doc["id"] = user_id
#         user_doc["_id"] = ins.inserted_id
#     else:
#         user_doc["id"] = user_id

#     # Create verification token if required
#     verification_token = generate_secure_token()
#     token_hash = hash_token(verification_token)
    
#     if db is not None:
#         await db.email_verifications.insert_one({
#             "user_id": user_id,
#             "email": clean_email,
#             "token_hash": token_hash,
#             "created_at": datetime.now(timezone.utc),
#             "expires_at": datetime.now(timezone.utc) + timedelta(hours=24),
#             "used": False
#         })

#     # Dispatch verification email
#     verify_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}&email={clean_email}"
#     html_body = f"""
#     <div style="font-family: Arial, sans-serif; background: #070a12; color: #e2e8f0; padding: 24px; border-radius: 12px;">
#         <h2 style="color: #06b6d4;">Welcome to BrandShield AI</h2>
#         <p>Hi {payload.full_name},</p>
#         <p>Thank you for registering with BrandShield AI Digital Risk Protection. Please verify your email address to activate your security operations access:</p>
#         <p><a href="{verify_url}" style="display: inline-block; background: #06b6d4; color: #020617; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold;">Verify Email Address</a></p>
#         <p style="font-size: 11px; color: #64748b;">Link expires in 24 hours. If you did not create this account, please ignore this email.</p>
#     </div>
#     """
#     text_body = f"Welcome to BrandShield AI! Please verify your email by clicking: {verify_url}"
#     send_email_notification(clean_email, "Verify Your BrandShield AI Account", html_body, text_body)

#     # Issue JWT Token
#     access_token = create_access_token({"sub": user_id, "email": clean_email, "role": user_doc["role"]})

#     return {
#         "status": "success",
#         "message": "Account created successfully.",
#         "user": serialize_user(user_doc),
#         "token": access_token,
#         "email_verified": user_doc["email_verified"]
#     }

# @router.post("/login")
# async def login_user(payload: LoginRequest, request: Request, db = Depends(get_db)):
#     """Authenticates an existing user via email and password."""
#     clean_email = payload.email.strip().lower()

#     if db is not None:
#         user = await db.users.find_one({"email": clean_email})
#     else:
#         user = None

#     # Brute-force rate limiting check
#     client_ip = request.client.host if request.client else "unknown"
#     if db is not None:
#         cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
#         failed_count = await db.login_attempts.count_documents({
#             "email": clean_email,
#             "success": False,
#             "timestamp": {"$gte": cutoff}
#         })
#         if failed_count >= 5:
#             logger.warning(f"Rate limit triggered for {clean_email} from IP {client_ip}")
#             raise HTTPException(
#                 status_code=429,
#                 detail="Too many failed login attempts. Please wait 15 minutes or reset your password."
#             )

#     # Verify password against hash
#     is_valid = False
#     if user and user.get("password_hash"):
#         is_valid = verify_password(payload.password, user["password_hash"])

#     if not is_valid:
#         # Record failed attempt
#         if db is not None:
#             await db.login_attempts.insert_one({
#                 "email": clean_email,
#                 "ip": client_ip,
#                 "success": False,
#                 "timestamp": datetime.now(timezone.utc)
#             })
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid email or password. Please verify your credentials."
#         )

#     # Check active status
#     if not user.get("is_active", True):
#         raise HTTPException(
#             status_code=403,
#             detail="Your account has been deactivated. Please contact your SOC administrator."
#         )

#     # Record successful attempt and update last_login
#     now = datetime.now(timezone.utc).isoformat()
#     if db is not None:
#         await db.users.update_one({"_id": user["_id"]}, {"$set": {"last_login": now}})
#         await db.login_attempts.insert_one({
#             "email": clean_email,
#             "ip": client_ip,
#             "success": True,
#             "timestamp": datetime.now(timezone.utc)
#         })

#     user_id = str(user["_id"])
#     access_token = create_access_token({
#         "sub": user_id,
#         "email": user["email"],
#         "role": user.get("role", "SOC Analyst")
#     })

#     return {
#         "status": "success",
#         "message": "Signed in successfully.",
#         "user": serialize_user(user),
#         "token": access_token
#     }

# @router.post("/google")
# async def google_auth(payload: GoogleAuthRequest, db = Depends(get_db)):
#     """Authenticates or registers a user via Google OAuth."""
#     # Check if Google OAuth is configured
#     if not settings.GOOGLE_CLIENT_ID:
#         raise HTTPException(
#             status_code=400,
#             detail="Google sign-in is not configured. Set GOOGLE_CLIENT_ID in the backend environment."
#         )

#     google_profile = await verify_google_id_token(payload.id_token)

#     clean_email = google_profile["email"]
#     now = datetime.now(timezone.utc).isoformat()

#     if db is not None:
#         # Check by google_id or email
#         user = await db.users.find_one({"$or": [{"google_id": google_profile["sub"]}, {"email": clean_email}]})
#         if user:
#             if not user.get("is_active", True):
#                 raise HTTPException(
#                     status_code=403,
#                     detail="Your account has been deactivated. Please contact your SOC administrator."
#                 )
#             # Update user info with google_id
#             await db.users.update_one(
#                 {"_id": user["_id"]},
#                 {"$set": {
#                     "google_id": google_profile["sub"],
#                     "email_verified": True,
#                     "last_login": now
#                 }}
#             )
#             user_id = str(user["_id"])
#         else:
#             # Create new Google user
#             base_user = re.sub(r'[^a-zA-Z0-9_]', '', google_profile["name"].lower().replace(' ', '_'))
#             new_user = {
#                 "username": f"{base_user}_{secrets.token_hex(2)}",
#                 "email": clean_email,
#                 "password_hash": None,
#                 "full_name": google_profile["name"],
#                 "avatar_url": google_profile.get("picture"),
#                 "role": "SOC Analyst",
#                 "organization": "Global SOC Ops",
#                 "department": "Digital Risk Protection",
#                 "provider": "google",
#                 "google_id": google_profile["sub"],
#                 "email_verified": True,
#                 "is_active": True,
#                 "created_at": now,
#                 "last_login": now
#             }
#             ins = await db.users.insert_one(new_user)
#             user_id = str(ins.inserted_id)
#             new_user["_id"] = ins.inserted_id
#             user = new_user
#     else:
#         raise HTTPException(
#             status_code=503,
#             detail="Google sign-in is temporarily unavailable because the user database is not connected."
#         )

#     access_token = create_access_token({
#         "sub": user_id,
#         "email": clean_email,
#         "role": user.get("role", "SOC Analyst")
#     })

#     return {
#         "status": "success",
#         "message": f"Welcome, {user.get('full_name', 'Analyst')}!",
#         "user": serialize_user(user),
#         "token": access_token
#     }

# @router.get("/me")
# async def get_current_user_profile(user: Dict[str, Any] = Depends(require_current_user)):
#     """Returns the authenticated user's profile."""
#     return serialize_user(user)

# @router.post("/logout")
# async def logout_user():
#     """Logs out the user and clears session state."""
#     return {"status": "success", "message": "Successfully logged out."}

# @router.post("/change-password")
# async def change_password(
#     payload: ChangePasswordRequest,
#     current_user: Dict[str, Any] = Depends(require_current_user),
#     db = Depends(get_db)
# ):
#     """
#     Securely updates the authenticated user's password.
#     Requires current password verification and strength enforcement.
#     """
#     stored_hash = current_user.get("password_hash")
#     # Verify current password if user has one
#     if stored_hash:
#         if not verify_password(payload.current_password, stored_hash):
#             raise HTTPException(
#                 status_code=400,
#                 detail="Current password is incorrect. Please verify and try again."
#             )
#     elif current_user.get("provider") != "google":
#         raise HTTPException(
#             status_code=400,
#             detail="Current password verification failed."
#         )

#     if payload.new_password != payload.confirm_password:
#         raise HTTPException(status_code=400, detail="New password and confirmation do not match.")

#     if stored_hash and verify_password(payload.new_password, stored_hash):
#         raise HTTPException(status_code=400, detail="New password cannot be identical to your current password.")

#     is_strong, msg = validate_password_strength(payload.new_password)
#     if not is_strong:
#         raise HTTPException(status_code=400, detail=msg)

#     now = datetime.now(timezone.utc).isoformat()
#     new_hash = hash_password(payload.new_password)

#     if db is not None:
#         from bson import ObjectId
#         uid = current_user["id"]
#         q = {"_id": ObjectId(uid)} if ObjectId.is_valid(uid) else {"_id": uid}
#         await db.users.update_one(
#             q,
#             {"$set": {
#                 "password_hash": new_hash,
#                 "password_changed_at": now,
#                 "updated_at": now
#             }}
#         )

#     return {
#         "status": "success",
#         "message": "Password changed successfully. Your account credentials have been updated."
#     }

# @router.post("/forgot-password")
# async def request_password_reset(payload: ForgotPasswordRequest, db = Depends(get_db)):
#     """
#     Initiates password recovery by creating a secure token and sending an email.
#     Always returns generic success message to prevent account enumeration.
#     """
#     clean_email = payload.email.strip().lower()
#     if not re.match(EMAIL_REGEX, clean_email):
#         raise HTTPException(status_code=400, detail="Invalid email address format.")
    
#     if db is not None:
#         user = await db.users.find_one({"email": clean_email})
#     else:
#         user = None

#     token = generate_secure_token()
#     token_hash = hash_token(token)
#     expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

#     if user and db is not None:
#         # Invalidate any prior unused reset tokens
#         await db.password_resets.update_many(
#             {"email": clean_email, "used": False},
#             {"$set": {"used": True}}
#         )
        
#         # Save new token
#         await db.password_resets.insert_one({
#             "email": clean_email,
#             "user_id": str(user["_id"]),
#             "token_hash": token_hash,
#             "expires_at": expires_at,
#             "used": False,
#             "created_at": datetime.now(timezone.utc)
#         })

#     reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}&email={clean_email}"
    
#     html_body = f"""
#     <div style="font-family: Arial, sans-serif; background: #070a12; color: #e2e8f0; padding: 24px; border-radius: 12px;">
#         <h2 style="color: #06b6d4;">BrandShield AI Password Reset</h2>
#         <p>You recently requested a password reset for your BrandShield AI account.</p>
#         <p><a href="{reset_url}" style="display: inline-block; background: #06b6d4; color: #020617; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold;">Reset Your Password</a></p>
#         <p style="font-size: 11px; color: #64748b;">This link is valid for 1 hour and can only be used once. If you did not make this request, you can safely ignore this email.</p>
#     </div>
#     """
#     text_body = f"Reset your BrandShield AI password by clicking: {reset_url}"
    
#     sent_via_smtp = send_email_notification(clean_email, "BrandShield AI - Password Reset Instructions", html_body, text_body)

#     response_payload = {
#         "status": "success",
#         "message": "If an account with that email exists, password reset instructions have been sent."
#     }

#     # In development mode without SMTP configured, include token for convenience and testing
#     if not sent_via_smtp:
#         response_payload["dev_reset_url"] = reset_url
#         response_payload["dev_token"] = token
#         response_payload["dev_notice"] = "SMTP is not configured in backend/.env; using development reset URL."

#     return response_payload

# @router.post("/validate-reset-token")
# async def validate_reset_token(payload: ValidateTokenRequest, db = Depends(get_db)):
#     """Verifies that a password reset token is valid, active, and not expired."""
#     clean_email = payload.email.strip().lower()
#     t_hash = hash_token(payload.token.strip())

#     if db is not None:
#         record = await db.password_resets.find_one({
#             "email": clean_email,
#             "token_hash": t_hash,
#             "used": False
#         })
#         if not record:
#             return {"valid": False, "message": "Invalid or expired reset token."}
            
#         exp = record.get("expires_at")
#         if isinstance(exp, str):
#             exp = datetime.fromisoformat(exp)
#         if exp and exp.tzinfo is None:
#             exp = exp.replace(tzinfo=timezone.utc)
            
#         if exp and datetime.now(timezone.utc) > exp:
#             return {"valid": False, "message": "Password reset token has expired. Please request a new one."}
            
#         return {"valid": True, "message": "Token is valid."}

#     return {"valid": True, "message": "Token accepted."}

# @router.post("/reset-password")
# async def reset_password(payload: ResetPasswordRequest, db = Depends(get_db)):
#     """Completes the password reset process, hashes the new password, and invalidates the token."""
#     if payload.new_password != payload.confirm_password:
#         raise HTTPException(status_code=400, detail="New password and confirm password do not match.")

#     is_strong, msg = validate_password_strength(payload.new_password)
#     if not is_strong:
#         raise HTTPException(status_code=400, detail=msg)

#     clean_email = payload.email.strip().lower()
#     t_hash = hash_token(payload.token.strip())

#     if db is not None:
#         record = await db.password_resets.find_one({
#             "email": clean_email,
#             "token_hash": t_hash,
#             "used": False
#         })
#         if not record:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Invalid or expired reset token. Please request a new password reset link."
#             )

#         exp = record.get("expires_at")
#         if isinstance(exp, str):
#             exp = datetime.fromisoformat(exp)
#         if exp and exp.tzinfo is None:
#             exp = exp.replace(tzinfo=timezone.utc)

#         if exp and datetime.now(timezone.utc) > exp:
#             raise HTTPException(
#                 status_code=400,
#                 detail="This password reset token has expired. Please request a new one."
#             )

#         # Hash new password and update user record
#         pw_hash = hash_password(payload.new_password)
#         await db.users.update_one(
#             {"email": clean_email},
#             {"$set": {
#                 "password_hash": pw_hash,
#                 "updated_at": datetime.now(timezone.utc).isoformat()
#             }}
#         )

#         # Mark token as used
#         await db.password_resets.update_one(
#             {"_id": record["_id"]},
#             {"$set": {"used": True, "used_at": datetime.now(timezone.utc)}}
#         )

#     return {
#         "status": "success",
#         "message": "Your password has been successfully updated. You can now sign in with your new password."
#     }

# @router.get("/verify-email")
# async def verify_email(token: str, email: str, db = Depends(get_db)):
#     """Verifies a user's email address via link."""
#     clean_email = email.strip().lower()
#     t_hash = hash_token(token.strip())

#     if db is not None:
#         record = await db.email_verifications.find_one({
#             "email": clean_email,
#             "token_hash": t_hash,
#             "used": False
#         })
#         if not record:
#             raise HTTPException(status_code=400, detail="Invalid or expired email verification token.")

#         await db.users.update_one(
#             {"email": clean_email},
#             {"$set": {"email_verified": True}}
#         )
#         await db.email_verifications.update_one(
#             {"_id": record["_id"]},
#             {"$set": {"used": True}}
#         )

#     return {"status": "success", "message": "Email verified successfully."}






import re
import secrets
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from bson import ObjectId

from app.database import get_db
from app.config import settings
from app.services.auth_service import (
    hash_password,
    verify_password,
    is_legacy_default_account,
    validate_password_strength,
    create_access_token,
    generate_secure_token,
    hash_token,
    require_current_user,
    send_email_notification,
    verify_google_id_token,
)

logger = logging.getLogger("brandshield.routes.auth")
router = APIRouter(prefix="/auth", tags=["Authentication"])

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


def require_database(db):
    """Fail closed whenever authentication needs persistent storage."""
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Authentication services are temporarily unavailable.",
        )


def normalize_email(email: str) -> str:
    clean_email = email.strip().lower()
    if not re.fullmatch(EMAIL_REGEX, clean_email):
        raise HTTPException(status_code=400, detail="Invalid email address format.")
    return clean_email


def user_id_query(user_id: str) -> dict:
    """Support Mongo ObjectId IDs and legacy string IDs."""
    if ObjectId.is_valid(user_id):
        return {"_id": ObjectId(user_id)}
    return {"_id": user_id}


def serialize_user(user: dict) -> dict:
    if not user:
        return {}

    result = dict(user)
    result["id"] = str(result.pop("_id", result.get("id", "")))

    # Never return password or reset/verification secrets.
    for key in (
        "password_hash",
        "password",
        "token_hash",
        "google_id",
    ):
        result.pop(key, None)

    result.setdefault("full_name", "")
    result.setdefault("username", "")
    result.setdefault("email", "")
    result.setdefault("role", "SOC Analyst")
    result.setdefault("organization", None)
    result.setdefault("department", None)
    result.setdefault("phone", None)
    result.setdefault("avatar_url", None)
    result.setdefault("provider", "local")
    result.setdefault("email_verified", False)
    result.setdefault("two_factor_enabled", False)
    result.setdefault("is_active", True)
    result.setdefault("created_at", None)
    result.setdefault("last_login", None)
    result.setdefault("password_changed_at", None)

    return result


# -------------------- REQUEST SCHEMAS --------------------

class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: str
    password: str = Field(..., min_length=8)
    confirm_password: str
    terms_accepted: bool


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., min_length=1)


class ForgotPasswordRequest(BaseModel):
    email: str


class ValidateTokenRequest(BaseModel):
    token: str
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    email: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str


# -------------------- REGISTER --------------------

@router.post("/register")
async def register_user(payload: RegisterRequest, db=Depends(get_db)):
    require_database(db)

    if not payload.terms_accepted:
        raise HTTPException(
            status_code=400,
            detail="You must accept the Terms of Service and Privacy Policy.",
        )

    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")

    is_strong, message = validate_password_strength(payload.password)
    if not is_strong:
        raise HTTPException(status_code=400, detail=message)

    clean_email = normalize_email(payload.email)

    if is_legacy_default_account(clean_email):
        raise HTTPException(
            status_code=400,
            detail="This built-in account is unavailable. Please use another email address.",
        )

    if await db.users.find_one({"email": clean_email}):
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists. Please sign in.",
        )

    now = datetime.now(timezone.utc).isoformat()
    full_name = payload.full_name.strip()
    base_username = (
        re.sub(r"[^a-zA-Z0-9_]", "", full_name.lower().replace(" ", "_"))
        or clean_email.split("@")[0]
    )
    username = f"{base_username}_{secrets.token_hex(3)}"

    email_verification_required = bool(
        getattr(settings, "REQUIRE_EMAIL_VERIFICATION", False)
    )

    user_doc = {
        "username": username,
        "email": clean_email,
        "password_hash": hash_password(payload.password),
        "full_name": full_name,
        "role": "SOC Analyst",
        "organization": "Global SOC Ops",
        "department": "Digital Risk Protection",
        "provider": "local",
        "email_verified": not email_verification_required,
        "is_active": True,
        "created_at": now,
        "last_login": None,
    }

    try:
        inserted = await db.users.insert_one(user_doc)
    except Exception:
        logger.exception("Unable to create user account")
        raise HTTPException(
            status_code=503,
            detail="Unable to create your account right now. Please try again.",
        )

    user_doc["_id"] = inserted.inserted_id
    user_id = str(inserted.inserted_id)

    if email_verification_required:
        verification_token = generate_secure_token()
        verification_hash = hash_token(verification_token)
        current_time = datetime.now(timezone.utc)

        await db.email_verifications.insert_one({
            "user_id": user_id,
            "email": clean_email,
            "token_hash": verification_hash,
            "created_at": current_time,
            "expires_at": current_time + timedelta(hours=24),
            "used": False,
        })

        verify_url = (
            f"{settings.FRONTEND_URL}/verify-email"
            f"?token={verification_token}&email={clean_email}"
        )

        html_body = f"""
        <div style="font-family: Arial, sans-serif;">
            <h2>Welcome to BrandShield AI</h2>
            <p>Hello, {full_name}</p>
            <p>Verify your email address to activate your account.</p>
            <p><a href="{verify_url}">Verify Email Address</a></p>
            <p>This link expires in 24 hours.</p>
        </div>
        """
        text_body = (
            "Welcome to BrandShield AI. Verify your email using this link: "
            + verify_url
        )

        try:
            sent = send_email_notification(
                clean_email,
                "Verify Your BrandShield AI Account",
                html_body,
                text_body,
            )
        except Exception:
            logger.exception("Unable to send verification email")
            sent = False

        if not sent:
            logger.warning("Verification email was not sent for a new account")

        # Do not issue an authenticated token before required verification.
        return {
            "status": "success",
            "message": (
                "Account created. If the verification email was sent, "
                "please follow its instructions before signing in."
            ),
            "user": serialize_user(user_doc),
            "token": None,
            "email_verified": False,
        }

    access_token = create_access_token({
        "sub": user_id,
        "email": clean_email,
        "role": user_doc["role"],
    })

    return {
        "status": "success",
        "message": "Account created successfully.",
        "user": serialize_user(user_doc),
        "token": access_token,
        "email_verified": True,
    }


# -------------------- LOGIN --------------------

@router.post("/login")
async def login_user(
    payload: LoginRequest,
    request: Request,
    db=Depends(get_db),
):
    require_database(db)
    clean_email = normalize_email(payload.email)

    user = await db.users.find_one({"email": clean_email})

    client_ip = request.client.host if request.client else "unknown"
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)

    failed_count = await db.login_attempts.count_documents({
        "email": clean_email,
        "success": False,
        "timestamp": {"$gte": cutoff},
    })

    if failed_count >= 5:
        logger.warning("Login rate limit reached for IP %s", client_ip)
        raise HTTPException(
            status_code=429,
            detail="Too many failed login attempts. Please wait 15 minutes.",
        )

    password_is_valid = bool(
        user
        and not is_legacy_default_account(clean_email)
        and user.get("password_hash")
        and verify_password(payload.password, user["password_hash"])
    )

    if not password_is_valid:
        await db.login_attempts.insert_one({
            "email": clean_email,
            "ip": client_ip,
            "success": False,
            "timestamp": datetime.now(timezone.utc),
        })
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Your account is deactivated.")

    if (
        getattr(settings, "REQUIRE_EMAIL_VERIFICATION", False)
        and not user.get("email_verified", False)
    ):
        raise HTTPException(
            status_code=403,
            detail="Please verify your email before signing in.",
        )

    now = datetime.now(timezone.utc).isoformat()
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": now}},
    )
    await db.login_attempts.insert_one({
        "email": clean_email,
        "ip": client_ip,
        "success": True,
        "timestamp": datetime.now(timezone.utc),
    })

    user["last_login"] = now
    access_token = create_access_token({
        "sub": str(user["_id"]),
        "email": user["email"],
        "role": user.get("role", "SOC Analyst"),
    })

    return {
        "status": "success",
        "message": "Signed in successfully.",
        "user": serialize_user(user),
        "token": access_token,
    }


# -------------------- GOOGLE SIGN-IN --------------------

@router.post("/google")
async def google_auth(payload: GoogleAuthRequest, db=Depends(get_db)):
    require_database(db)

    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=503,
            detail="Google sign-in is not configured.",
        )

    google_profile = await verify_google_id_token(payload.id_token)
    clean_email = normalize_email(google_profile["email"])
    if is_legacy_default_account(clean_email):
        raise HTTPException(
            status_code=401,
            detail="Invalid Google authentication credentials.",
        )

    now = datetime.now(timezone.utc).isoformat()

    user = await db.users.find_one({
        "$or": [
            {"google_id": google_profile["sub"]},
            {"email": clean_email},
        ]
    })

    if user:
        if not user.get("is_active", True):
            raise HTTPException(status_code=403, detail="Your account is deactivated.")

        # Do not silently link a local account to Google based only on matching email.
        if (
            user.get("provider") == "local"
            and user.get("google_id") != google_profile["sub"]
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "An account already exists for this email. "
                    "Sign in using your existing method before linking accounts."
                ),
            )

        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "google_id": google_profile["sub"],
                "email_verified": True,
                "last_login": now,
            }},
        )
        user["google_id"] = google_profile["sub"]
        user["email_verified"] = True
        user["last_login"] = now
        user_id = str(user["_id"])

    else:
        full_name = google_profile.get("name") or clean_email.split("@")[0]
        base_username = (
            re.sub(r"[^a-zA-Z0-9_]", "", full_name.lower().replace(" ", "_"))
            or clean_email.split("@")[0]
        )

        new_user = {
            "username": f"{base_username}_{secrets.token_hex(3)}",
            "email": clean_email,
            "password_hash": None,
            "full_name": full_name,
            "avatar_url": google_profile.get("picture"),
            "role": "SOC Analyst",
            "organization": "Global SOC Ops",
            "department": "Digital Risk Protection",
            "provider": "google",
            "google_id": google_profile["sub"],
            "email_verified": True,
            "is_active": True,
            "created_at": now,
            "last_login": now,
        }

        inserted = await db.users.insert_one(new_user)
        new_user["_id"] = inserted.inserted_id
        user = new_user
        user_id = str(inserted.inserted_id)

    access_token = create_access_token({
        "sub": user_id,
        "email": clean_email,
        "role": user.get("role", "SOC Analyst"),
    })

    return {
        "status": "success",
        "message": f"Welcome, {user.get('full_name', 'Analyst')}!",
        "user": serialize_user(user),
        "token": access_token,
    }


# -------------------- CURRENT USER --------------------

@router.get("/me")
async def get_current_user_profile(
    user: Dict[str, Any] = Depends(require_current_user),
):
    return serialize_user(user)


@router.post("/logout")
async def logout_user():
    # This API uses stateless JWTs. The frontend must discard its token.
    # Server-side token revocation requires a separate denylist/session design.
    return {
        "status": "success",
        "message": "Logged out. Please discard the access token on the client.",
    }


# -------------------- CHANGE PASSWORD --------------------

@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: Dict[str, Any] = Depends(require_current_user),
    db=Depends(get_db),
):
    require_database(db)

    if payload.new_password != payload.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="New password and confirmation do not match.",
        )

    is_strong, message = validate_password_strength(payload.new_password)
    if not is_strong:
        raise HTTPException(status_code=400, detail=message)

    user_id = str(current_user.get("id", current_user.get("_id", "")))
    stored_user = await db.users.find_one(user_id_query(user_id))

    if not stored_user:
        raise HTTPException(status_code=401, detail="Authenticated user was not found.")

    stored_hash = stored_user.get("password_hash")

    # Google-only accounts must use a secure password-setup/reset flow.
    if not stored_hash:
        raise HTTPException(
            status_code=400,
            detail="This account has no local password. Use the password-reset flow.",
        )

    if not verify_password(payload.current_password, stored_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    if verify_password(payload.new_password, stored_hash):
        raise HTTPException(
            status_code=400,
            detail="New password must differ from the current password.",
        )

    now = datetime.now(timezone.utc).isoformat()
    result = await db.users.update_one(
        {"_id": stored_user["_id"]},
        {"$set": {
            "password_hash": hash_password(payload.new_password),
            "password_changed_at": now,
            "updated_at": now,
        }},
    )

    if result.matched_count != 1:
        raise HTTPException(status_code=503, detail="Unable to update the password.")

    return {"status": "success", "message": "Password changed successfully."}


# -------------------- FORGOT PASSWORD --------------------

@router.post("/forgot-password")
async def request_password_reset(
    payload: ForgotPasswordRequest,
    db=Depends(get_db),
):
    clean_email = normalize_email(payload.email)
    generic_response = {
        "status": "success",
        "message": (
            "If an account with that email exists, password reset "
            "instructions will be sent."
        ),
    }

    # Do not create reset links or claim success if persistent storage is down.
    require_database(db)

    user = await db.users.find_one({"email": clean_email})
    if not user or not user.get("is_active", True):
        return generic_response

    token = generate_secure_token()
    token_hash = hash_token(token)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=1)

    await db.password_resets.update_many(
        {"email": clean_email, "used": False},
        {"$set": {"used": True, "invalidated_at": now}},
    )

    await db.password_resets.insert_one({
        "email": clean_email,
        "user_id": str(user["_id"]),
        "token_hash": token_hash,
        "expires_at": expires_at,
        "used": False,
        "created_at": now,
    })

    reset_url = (
        f"{settings.FRONTEND_URL}/reset-password"
        f"?token={token}&email={clean_email}"
    )

    html_body = f"""
    <div style="font-family: Arial, sans-serif;">
        <h2>BrandShield AI Password Reset</h2>
        <p>Use the link below to reset your password.</p>
        <p><a href="{reset_url}">Reset Your Password</a></p>
        <p>This link expires in one hour and can only be used once.</p>
    </div>
    """
    text_body = "Reset your BrandShield AI password using this link: " + reset_url

    try:
        sent = send_email_notification(
            clean_email,
            "BrandShield AI - Password Reset Instructions",
            html_body,
            text_body,
        )
    except Exception:
        logger.exception("Password reset email delivery failed")
        sent = False

    if not sent:
        # Never return a reset token or reset URL in an API response.
        logger.warning("Password reset email could not be delivered")

    return generic_response


# -------------------- VALIDATE RESET TOKEN --------------------

@router.post("/validate-reset-token")
async def validate_reset_token(
    payload: ValidateTokenRequest,
    db=Depends(get_db),
):
    require_database(db)
    clean_email = normalize_email(payload.email)
    token_hash = hash_token(payload.token.strip())

    record = await db.password_resets.find_one({
        "email": clean_email,
        "token_hash": token_hash,
        "used": False,
    })

    if not record:
        return {"valid": False, "message": "Invalid or expired reset token."}

    expires_at = record.get("expires_at")
    if isinstance(expires_at, str):
        try:
            expires_at = datetime.fromisoformat(expires_at)
        except ValueError:
            return {"valid": False, "message": "Invalid or expired reset token."}

    if expires_at is None:
        return {"valid": False, "message": "Invalid or expired reset token."}

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) >= expires_at:
        return {"valid": False, "message": "Password reset token has expired."}

    return {"valid": True, "message": "Token is valid."}


# -------------------- RESET PASSWORD --------------------

@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    db=Depends(get_db),
):
    require_database(db)

    if payload.new_password != payload.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="New password and confirmation do not match.",
        )

    is_strong, message = validate_password_strength(payload.new_password)
    if not is_strong:
        raise HTTPException(status_code=400, detail=message)

    clean_email = normalize_email(payload.email)
    token_hash = hash_token(payload.token.strip())  