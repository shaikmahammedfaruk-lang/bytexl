import os
import re
import uuid
import secrets
import hashlib
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import bcrypt
import jwt
import aiohttp
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings
from app.database import get_db

logger = logging.getLogger("brandshield.auth")

security = HTTPBearer(auto_error=False)

# --- PASSWORD HASHING ---

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

# --- PASSWORD STRENGTH VALIDATOR ---

def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must include at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must include at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must include at least one digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must include at least one special character."
    return True, ""

# --- JWT TOKENS ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception) as e:
        logger.debug(f"JWT decode error: {e}")
        return None

# --- TOKENS FOR RESET & VERIFICATION ---

def generate_secure_token() -> str:
    return secrets.token_urlsafe(32)

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

# --- AUTH DEPENDENCIES ---

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db = Depends(get_db)
) -> Optional[Dict[str, Any]]:
    """Extracts and verifies the authenticated user from the Authorization header."""
    if not credentials:
        return None
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    if db is not None:
        from bson import ObjectId
        query = {"_id": ObjectId(user_id)} if ObjectId.is_valid(user_id) else {"_id": user_id}
        user = await db.users.find_one(query)
        if user:
            user["id"] = str(user.pop("_id"))
            return user
            
    return None

async def require_current_user(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Dependency that raises 401 if user is unauthenticated."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in to access this resource.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

# --- EMAIL DISPATCH SERVICE ---

def send_email_notification(to_email: str, subject: str, html_content: str, text_content: str) -> bool:
    """Sends email via configured SMTP server or logs to console in development."""
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.info(f"\n[DEV EMAIL DISPATCH SIMULATOR]\nTo: {to_email}\nSubject: {subject}\nContent:\n{text_content}\n")
        return False
        
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = to_email

        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        msg.attach(part1)
        msg.attach(part2)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())
        logger.info(f"Successfully sent email to {to_email} via SMTP")
        return True
    except Exception as e:
        logger.error(f"Failed to send email via SMTP to {to_email}: {e}")
        return False

# --- GOOGLE OAUTH TOKEN VERIFICATION ---

async def verify_google_id_token(id_token: str) -> Dict[str, Any]:
    """
    Verifies a Google OAuth ID token using Google's public tokeninfo API.
    Returns user profile dict if valid, raises HTTPException otherwise.
    """
    url = "https://oauth2.googleapis.com/tokeninfo"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params={"id_token": id_token}, timeout=10) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.warning(f"Google tokeninfo rejected token: {error_text}")
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid Google authentication token. Please sign in again."
                    )
                data = await resp.json()
                
                if data.get("aud") != settings.GOOGLE_CLIENT_ID:
                    logger.warning(f"Google token audience mismatch: {data.get('aud')} != {settings.GOOGLE_CLIENT_ID}")
                    raise HTTPException(
                        status_code=400,
                        detail="Google token audience mismatch. Unauthorized client ID."
                    )

                if data.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
                    raise HTTPException(status_code=400, detail="Invalid Google token issuer.")

                email = data.get("email")
                if not email or data.get("email_verified") not in (True, "true"):
                    raise HTTPException(
                        status_code=400,
                        detail="Google account must provide a verified email address."
                    )

                subject = data.get("sub")
                if not subject:
                    raise HTTPException(status_code=400, detail="Google account did not return a valid subject.")
                    
                return {
                    "sub": subject,
                    "email": email.lower(),
                    "email_verified": data.get("email_verified", True),
                    "name": data.get("name", email.split('@')[0]),
                    "picture": data.get("picture")
                }
        except aiohttp.ClientError as e:
            logger.error(f"Network error verifying Google ID token: {e}")
            raise HTTPException(
                status_code=502,
                detail="Unable to reach Google OAuth verification servers. Please try again."
            )
