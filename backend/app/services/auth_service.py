# import os
# import re
# import uuid
# import secrets
# import hashlib
# import logging
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from datetime import datetime, timedelta, timezone
# from typing import Optional, Dict, Any

# import bcrypt
# import jwt
# import aiohttp
# from fastapi import HTTPException, status, Depends
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# from app.config import settings
# from app.database import get_db

# logger = logging.getLogger("brandshield.auth")

# security = HTTPBearer(auto_error=False)

# # --- PASSWORD HASHING ---

# def hash_password(password: str) -> str:
#     salt = bcrypt.gensalt(rounds=12)
#     return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     try:
#         return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
#     except Exception:
#         return False

# # --- PASSWORD STRENGTH VALIDATOR ---

# def validate_password_strength(password: str) -> tuple[bool, str]:
#     if len(password) < 8:
#         return False, "Password must be at least 8 characters long."
#     if not re.search(r"[A-Z]", password):
#         return False, "Password must include at least one uppercase letter."
#     if not re.search(r"[a-z]", password):
#         return False, "Password must include at least one lowercase letter."
#     if not re.search(r"[0-9]", password):
#         return False, "Password must include at least one digit."
#     if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
#         return False, "Password must include at least one special character."
#     return True, ""

# # --- JWT TOKENS ---

# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.now(timezone.utc) + expires_delta
#     else:
#         expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
#     encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
#     return encoded_jwt

# def decode_access_token(token: str) -> Optional[dict]:
#     try:
#         payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
#         return payload
#     except (jwt.PyJWTError, Exception) as e:
#         logger.debug(f"JWT decode error: {e}")
#         return None

# # --- TOKENS FOR RESET & VERIFICATION ---

# def generate_secure_token() -> str:
#     return secrets.token_urlsafe(32)

# def hash_token(token: str) -> str:
#     return hashlib.sha256(token.encode('utf-8')).hexdigest()

# # --- AUTH DEPENDENCIES ---

# async def get_current_user(
#     credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
#     db = Depends(get_db)
# ) -> Optional[Dict[str, Any]]:
#     """Extracts and verifies the authenticated user from the Authorization header."""
#     if not credentials:
#         return None
#     token = credentials.credentials
#     payload = decode_access_token(token)
#     if not payload:
#         return None
#     user_id = payload.get("sub")
#     if not user_id:
#         return None
    
#     if db is not None:
#         from bson import ObjectId
#         query = {"_id": ObjectId(user_id)} if ObjectId.is_valid(user_id) else {"_id": user_id}
#         user = await db.users.find_one(query)
#         if user:
#             user["id"] = str(user.pop("_id"))
#             return user
            
#     return None

# async def require_current_user(
#     current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
# ) -> Dict[str, Any]:
#     """Dependency that raises 401 if user is unauthenticated."""
#     if not current_user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Authentication required. Please sign in to access this resource.",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     return current_user

# # --- EMAIL DISPATCH SERVICE ---

# def send_email_notification(to_email: str, subject: str, html_content: str, text_content: str) -> bool:
#     """Sends email via configured SMTP server or logs to console in development."""
#     if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
#         logger.info(f"\n[DEV EMAIL DISPATCH SIMULATOR]\nTo: {to_email}\nSubject: {subject}\nContent:\n{text_content}\n")
#         return False
        
#     try:
#         msg = MIMEMultipart("alternative")
#         msg["Subject"] = subject
#         msg["From"] = settings.EMAIL_FROM
#         msg["To"] = to_email

#         part1 = MIMEText(text_content, "plain")
#         part2 = MIMEText(html_content, "html")
#         msg.attach(part1)
#         msg.attach(part2)

#         with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
#             server.starttls()
#             server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
#             server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())
#         logger.info(f"Successfully sent email to {to_email} via SMTP")
#         return True
#     except Exception as e:
#         logger.error(f"Failed to send email via SMTP to {to_email}: {e}")
#         return False

# # --- GOOGLE OAUTH TOKEN VERIFICATION ---

# async def verify_google_id_token(id_token: str) -> Dict[str, Any]:
#     """
#     Verifies a Google OAuth ID token using Google's public tokeninfo API.
#     Returns user profile dict if valid, raises HTTPException otherwise.
#     """
#     url = "https://oauth2.googleapis.com/tokeninfo"
#     async with aiohttp.ClientSession() as session:
#         try:
#             async with session.get(url, params={"id_token": id_token}, timeout=10) as resp:
#                 if resp.status != 200:
#                     error_text = await resp.text()
#                     logger.warning(f"Google tokeninfo rejected token: {error_text}")
#                     raise HTTPException(
#                         status_code=400,
#                         detail="Invalid Google authentication token. Please sign in again."
#                     )
#                 data = await resp.json()
                
#                 if data.get("aud") != settings.GOOGLE_CLIENT_ID:
#                     logger.warning(f"Google token audience mismatch: {data.get('aud')} != {settings.GOOGLE_CLIENT_ID}")
#                     raise HTTPException(
#                         status_code=400,
#                         detail="Google token audience mismatch. Unauthorized client ID."
#                     )

#                 if data.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
#                     raise HTTPException(status_code=400, detail="Invalid Google token issuer.")

#                 email = data.get("email")
#                 if not email or data.get("email_verified") not in (True, "true"):
#                     raise HTTPException(
#                         status_code=400,
#                         detail="Google account must provide a verified email address."
#                     )

#                 subject = data.get("sub")
#                 if not subject:
#                     raise HTTPException(status_code=400, detail="Google account did not return a valid subject.")
                    
#                 return {
#                     "sub": subject,
#                     "email": email.lower(),
#                     "email_verified": data.get("email_verified", True),
#                     "name": data.get("name", email.split('@')[0]),
#                     "picture": data.get("picture")
#                 }
#         except aiohttp.ClientError as e:
#             logger.error(f"Network error verifying Google ID token: {e}")
#             raise HTTPException(
#                 status_code=502,
#                 detail="Unable to reach Google OAuth verification servers. Please try again."
#             )



# import logging
# import re
# import secrets
# import hashlib
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from datetime import datetime, timedelta, timezone
# from typing import Optional, Dict, Any

# import bcrypt
# import jwt
# import aiohttp
# from fastapi import HTTPException, status, Depends
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# from app.config import settings
# from app.database import get_db


# logger = logging.getLogger("brandshield.auth")
# security = HTTPBearer(auto_error=False)


# # -------------------- PASSWORD HASHING --------------------

# def hash_password(password: str) -> str:
#     """Hash a password using bcrypt."""
#     if not isinstance(password, str) or not password:
#         raise ValueError("Password must not be empty.")

#     # bcrypt only uses up to 72 bytes. Reject longer input instead of
#     # silently treating different passwords as identical.
#     if len(password.encode("utf-8")) > 72:
#         raise ValueError("Password must not exceed 72 UTF-8 bytes.")

#     salt = bcrypt.gensalt(rounds=12)
#     return bcrypt.hashpw(
#         password.encode("utf-8"),
#         salt,
#     ).decode("utf-8")


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     """Verify a password without exposing hashing errors."""
#     try:
#         if not isinstance(plain_password, str) or not isinstance(
#             hashed_password, str
#         ):
#             return False

#         if len(plain_password.encode("utf-8")) > 72:
#             return False

#         return bcrypt.checkpw(
#             plain_password.encode("utf-8"),
#             hashed_password.encode("utf-8"),
#         )
#     except (ValueError, TypeError, UnicodeError):
#         return False
#     except Exception:
#         logger.warning("Password verification failed.")
#         return False


# # -------------------- PASSWORD STRENGTH --------------------

# def validate_password_strength(password: str) -> tuple[bool, str]:
#     if not isinstance(password, str):
#         return False, "Password must be a string."

#     if len(password) < 8:
#         return False, "Password must be at least 8 characters long."

#     if len(password.encode("utf-8")) > 72:
#         return False, "Password must not exceed 72 UTF-8 bytes."

#     if not re.search(r"[A-Z]", password):
#         return False, "Password must include at least one uppercase letter."

#     if not re.search(r"[a-z]", password):
#         return False, "Password must include at least one lowercase letter."

#     if not re.search(r"[0-9]", password):
#         return False, "Password must include at least one digit."

#     if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
#         return False, "Password must include at least one special character."

#     return True, ""


# # -------------------- JWT TOKENS --------------------

# def create_access_token(
#     data: dict,
#     expires_delta: Optional[timedelta] = None,
# ) -> str:
#     """Create a signed access token."""
#     if not settings.JWT_SECRET_KEY:
#         logger.error("JWT secret is not configured.")
#         raise RuntimeError("Authentication signing is not configured.")

#     algorithm = settings.JWT_ALGORITHM
#     if not algorithm or algorithm.lower() == "none":
#         logger.error("An unsafe JWT algorithm is configured.")
#         raise RuntimeError("Authentication signing is not configured.")

#     to_encode = data.copy()
#     now = datetime.now(timezone.utc)

#     if expires_delta is not None:
#         expire = now + expires_delta
#     else:
#         expire = now + timedelta(
#             minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
#         )

#     to_encode["iat"] = now
#     to_encode["exp"] = expire

#     return jwt.encode(
#         to_encode,
#         settings.JWT_SECRET_KEY,
#         algorithm=algorithm,
#     )


# def decode_access_token(token: str) -> Optional[dict]:
#     """Decode and validate a signed JWT. Invalid tokens return None."""
#     try:
#         if not token or not settings.JWT_SECRET_KEY:
#             return None

#         algorithm = settings.JWT_ALGORITHM
#         if not algorithm or algorithm.lower() == "none":
#             logger.error("Unsafe JWT algorithm configuration.")
#             return None

#         payload = jwt.decode(
#             token,
#             settings.JWT_SECRET_KEY,
#             algorithms=[algorithm],
#             options={
#                 "require": ["exp", "iat", "sub"],
#             },
#         )

#         subject = payload.get("sub")
#         if not isinstance(subject, str) or not subject.strip():
#             return None

#         return payload

#     except jwt.PyJWTError:
#         # Do not log token contents or detailed token parsing errors.
#         return None
#     except Exception:
#         logger.warning("JWT validation could not be completed.")
#         return None


# # -------------------- RESET AND VERIFICATION TOKENS --------------------

# def generate_secure_token() -> str:
#     return secrets.token_urlsafe(32)


# def hash_token(token: str) -> str:
#     return hashlib.sha256(token.encode("utf-8")).hexdigest()


# # -------------------- AUTHENTICATION DEPENDENCIES --------------------

# async def get_current_user(
#     credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
#     db=Depends(get_db),
# ) -> Optional[Dict[str, Any]]:
#     """Return an active database user for a valid bearer token."""
#     if credentials is None:
#         return None

#     if credentials.scheme.lower() != "bearer":
#         return None

#     payload = decode_access_token(credentials.credentials)
#     if not payload:
#         return None

#     user_id = payload.get("sub")
#     if not user_id:
#         return None

#     if db is None:
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="Authentication database is unavailable.",
#         )

#     try:
#         from bson import ObjectId

#         if ObjectId.is_valid(user_id):
#             query = {"_id": ObjectId(user_id)}
#         else:
#             query = {"_id": user_id}

#         user = await db.users.find_one(query)

#     except Exception:
#         logger.exception("Unable to retrieve authenticated user.")
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="Unable to verify your account right now.",
#         )

#     if not user:
#         return None

#     if user.get("is_active", True) is not True:
#         return None

#     user["_id"] = user["_id"]
#     user["id"] = str(user["_id"])

#     # Return a copy so callers cannot accidentally mutate the DB result.
#     return dict(user)


# async def require_current_user(
#     current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
# ) -> Dict[str, Any]:
#     """Reject requests without a valid active account."""
#     if not current_user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Authentication required. Please sign in again.",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     return current_user


# # -------------------- EMAIL DISPATCH --------------------

# def send_email_notification(
#     to_email: str,
#     subject: str,
#     html_content: str,
#     text_content: str,
# ) -> bool:
#     """Send email using configured SMTP. Never log reset links or secrets."""
#     if not (
#         settings.SMTP_HOST
#         and settings.SMTP_USER
#         and settings.SMTP_PASSWORD
#         and settings.EMAIL_FROM
#     ):
#         logger.warning("SMTP is not configured; email was not sent.")
#         return False

#     message = MIMEMultipart("alternative")
#     message["Subject"] = subject
#     message["From"] = settings.EMAIL_FROM
#     message["To"] = to_email
#     message.attach(MIMEText(text_content, "plain", "utf-8"))
#     message.attach(MIMEText(html_content, "html", "utf-8"))

#     try:
#         with smtplib.SMTP(
#             settings.SMTP_HOST,
#             settings.SMTP_PORT,
#             timeout=15,
#         ) as server:
#             server.ehlo()
#             server.starttls()
#             server.ehlo()
#             server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
#             server.sendmail(
#                 settings.EMAIL_FROM,
#                 [to_email],
#                 message.as_string(),
#             )

#         logger.info("Email delivery completed.")
#         return True

#     except Exception as exc:
#         logger.error(
#             "Email delivery failed (%s).",
#             type(exc).__name__,
#         )
#         return False


# # -------------------- GOOGLE ID TOKEN VERIFICATION --------------------

# async def verify_google_id_token(id_token: str) -> Dict[str, Any]:
#     """
#     Verify a Google ID token with Google's tokeninfo endpoint.

#     For a production deployment, consider verifying the token signature
#     locally against Google's published signing keys.
#     """
#     if not settings.GOOGLE_CLIENT_ID:
#         raise HTTPException(
#             status_code=503,
#             detail="Google sign-in is not configured.",
#         )

#     if not id_token or len(id_token) > 10000:
#         raise HTTPException(
#             status_code=400,
#             detail="Invalid Google authentication token.",
#         )

#     url = "https://oauth2.googleapis.com/tokeninfo"
#     timeout = aiohttp.ClientTimeout(total=10)

#     try:
#         async with aiohttp.ClientSession(timeout=timeout) as session:
#             async with session.get(
#                 url,
#                 params={"id_token": id_token},
#             ) as response:
#                 if response.status != 200:
#                     raise HTTPException(
#                         status_code=401,
#                         detail="Invalid Google authentication token. Sign in again.",
#                     )

#                 data = await response.json(content_type=None)

#     except HTTPException:
#         raise
#     except (aiohttp.ClientError, TimeoutError):
#         logger.warning("Google token verification service is unavailable.")
#         raise HTTPException(
#             status_code=502,
#             detail="Unable to verify Google sign-in right now. Please try again.",
#         )
#     except Exception:
#         logger.exception("Unexpected Google token verification failure.")
#         raise HTTPException(
#             status_code=502,
#             detail="Google sign-in verification failed.",
#         )

#     if not isinstance(data, dict):
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid Google authentication token.",
#         )

#     if data.get("aud") != settings.GOOGLE_CLIENT_ID:
#         raise HTTPException(
#             status_code=401,
#             detail="Google token audience mismatch.",
#         )

#     if data.get("iss") not in (
#         "accounts.google.com",
#         "https://accounts.google.com",
#     ):
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid Google token issuer.",
#         )

#     email = data.get("email")
#     email_verified = data.get("email_verified")

#     if not email or email_verified not in (True, "true"):
#         raise HTTPException(
#             status_code=401,
#             detail="A verified Google email address is required.",
#         )

#     subject = data.get("sub")
#     if not isinstance(subject, str) or not subject:
#         raise HTTPException(
#             status_code=401,
#             detail="Google did not return a valid account identifier.",
#         )

#     return {
#         "sub": subject,
#         "email": email.strip().lower(),
#         "email_verified": True,
#         "name": data.get("name") or email.split("@")[0],
#         "picture": data.get("picture"),
#     }


import hashlib
import logging
import re
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

import aiohttp
import bcrypt
import jwt
from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.database import get_db


logger = logging.getLogger("brandshield.auth")
security = HTTPBearer(auto_error=False)
LEGACY_DEFAULT_ACCOUNT_EMAIL = "analyst@brandshield.ai"


def is_legacy_default_account(email: Optional[str]) -> bool:
    return (
        isinstance(email, str)
        and email.strip().lower() == LEGACY_DEFAULT_ACCOUNT_EMAIL
    )


# --------------------------------------------------
# PASSWORD HASHING
# --------------------------------------------------

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    if not isinstance(password, str) or not password:
        raise ValueError("Password must not be empty.")

    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password must not exceed 72 UTF-8 bytes.")

    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(
        password.encode("utf-8"),
        salt,
    ).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password without exposing hashing errors."""
    try:
        if not isinstance(plain_password, str):
            return False

        if not isinstance(hashed_password, str):
            return False

        if len(plain_password.encode("utf-8")) > 72:
            return False

        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError, UnicodeError):
        return False
    except Exception:
        logger.warning("Password verification failed.")
        return False


# --------------------------------------------------
# PASSWORD STRENGTH
# --------------------------------------------------

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password length and character requirements."""
    if not isinstance(password, str):
        return False, "Password must be a string."

    if len(password) < 8:
        return False, "Password must be at least 8 characters long."

    if len(password.encode("utf-8")) > 72:
        return False, "Password must not exceed 72 UTF-8 bytes."

    if not re.search(r"[A-Z]", password):
        return False, "Password must include at least one uppercase letter."

    if not re.search(r"[a-z]", password):
        return False, "Password must include at least one lowercase letter."

    if not re.search(r"[0-9]", password):
        return False, "Password must include at least one digit."

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must include at least one special character."

    return True, ""


# --------------------------------------------------
# JWT TOKENS
# --------------------------------------------------

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed access token."""
    secret = settings.JWT_SECRET_KEY
    algorithm = settings.JWT_ALGORITHM

    if not secret:
        logger.error("JWT signing secret is not configured.")
        raise RuntimeError("Authentication signing is not configured.")

    # Only permit the configured secure algorithm.
    if algorithm != "HS256":
        logger.error("Unsupported JWT signing algorithm configured.")
        raise RuntimeError("Authentication signing is not configured.")

    now = datetime.now(timezone.utc)
    expires_at = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload = dict(data)
    payload["iat"] = now
    payload["exp"] = expires_at

    return jwt.encode(
        payload,
        secret,
        algorithm=algorithm,
    )


def decode_access_token(token: str) -> Optional[dict]:
    """Validate a signed JWT and return its payload."""
    try:
        if not token or not settings.JWT_SECRET_KEY:
            return None

        algorithm = settings.JWT_ALGORITHM
        if algorithm != "HS256":
            logger.error("Unsupported JWT signing algorithm configured.")
            return None

        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"],
            options={
                "require": ["exp", "iat", "sub"],
            },
        )

        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject.strip():
            return None

        return payload

    except jwt.PyJWTError:
        # Never log access tokens or token contents.
        return None
    except Exception:
        logger.warning("JWT validation could not be completed.")
        return None


# --------------------------------------------------
# RESET AND VERIFICATION TOKENS
# --------------------------------------------------

def generate_secure_token() -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash a token before storing it in the database."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# --------------------------------------------------
# AUTHENTICATION DEPENDENCIES
# --------------------------------------------------

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db=Depends(get_db),
) -> Optional[Dict[str, Any]]:
    """
    Resolve a valid bearer token to an active database user.

    A valid token alone is insufficient: the user must still exist
    and must not be disabled.
    """
    if credentials is None:
        return None

    if credentials.scheme.lower() != "bearer":
        return None

    payload = decode_access_token(credentials.credentials)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id.strip():
        return None

    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication database is unavailable.",
        )

    try:
        if ObjectId.is_valid(user_id):
            query = {"_id": ObjectId(user_id)}
        else:
            # Support only legacy string IDs when present in the database.
            query = {"_id": user_id}

        user = await db.users.find_one(query)

    except Exception:
        logger.error("Unable to retrieve the authenticated user.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to verify your account right now.",
        ) from None

    if not user:
        return None

    if user.get("is_active", True) is not True:
        return None

    if is_legacy_default_account(user.get("email")):
        return None

    user["id"] = str(user["_id"])

    # Return a copy to avoid callers accidentally modifying this object.
    return dict(user)


async def require_current_user(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Reject requests that do not have a valid active user."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return current_user


# --------------------------------------------------
# EMAIL DISPATCH
# --------------------------------------------------

def send_email_notification(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str,
) -> bool:
    """Send email using configured SMTP without logging secrets."""
    if not (
        settings.SMTP_HOST
        and settings.SMTP_USER
        and settings.SMTP_PASSWORD
        and settings.EMAIL_FROM
    ):
        logger.warning("SMTP is not configured; email was not sent.")
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.EMAIL_FROM
    message["To"] = to_email

    message.attach(MIMEText(text_content, "plain", "utf-8"))
    message.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        with smtplib.SMTP(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            timeout=15,
        ) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(
                settings.SMTP_USER,
                settings.SMTP_PASSWORD,
            )
            server.sendmail(
                settings.EMAIL_FROM,
                [to_email],
                message.as_string(),
            )

        logger.info("Email delivery completed.")
        return True

    except Exception as exc:
        logger.error(
            "Email delivery failed (%s).",
            type(exc).__name__,
        )
        return False


# --------------------------------------------------
# GOOGLE ID TOKEN VERIFICATION
# --------------------------------------------------

async def verify_google_id_token(id_token: str) -> Dict[str, Any]:
    """
    Validate a Google ID token using Google's tokeninfo endpoint.

    The token audience, issuer, verified email, and subject are checked.
    For higher-volume production deployments, use Google's supported
    ID-token verification library with signature verification.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured.",
        )

    if not isinstance(id_token, str) or not id_token or len(id_token) > 10000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google authentication token.",
        )

    url = "https://oauth2.googleapis.com/tokeninfo"
    timeout = aiohttp.ClientTimeout(total=10)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                url,
                params={"id_token": id_token},
            ) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid Google authentication token. Sign in again.",
                    )

                data = await response.json(content_type=None)

    except HTTPException:
        raise
    except (aiohttp.ClientError, TimeoutError):
        logger.warning("Google token verification service is unavailable.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to verify Google sign-in right now. Please try again.",
        ) from None
    except Exception:
        logger.error("Unexpected Google token verification failure.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Google sign-in verification failed.",
        ) from None

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google authentication token.",
        )

    if data.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google token audience mismatch.",
        )

    if data.get("iss") not in (
        "accounts.google.com",
        "https://accounts.google.com",
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token issuer.",
        )

    email = data.get("email")
    email_verified = data.get("email_verified")

    if not isinstance(email, str) or email_verified not in (True, "true"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A verified Google email address is required.",
        )

    subject = data.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google did not return a valid account identifier.",
        )

    return {
        "sub": subject,
        "email": email.strip().lower(),
        "email_verified": True,
        "name": data.get("name") or email.split("@")[0],
        "picture": data.get("picture"),
    }