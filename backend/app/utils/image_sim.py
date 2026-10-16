# import io
# import base64
# import asyncio
# import ssl
# import urllib.request
# import urllib.error
# import logging
# from typing import Optional, Tuple, Dict, Any
# from urllib.parse import urlparse
# import httpx
# from PIL import Image

# logger = logging.getLogger("brandshield.image_sim")

# # =========================================================================
# # CENTRALIZED SIMILARITY THRESHOLDS & RISK CLASSIFICATION
# # =========================================================================
# # 90.00 – 100.00 %: AUTHENTIC / NORMAL
# # 75.00 – 89.99  %: SUSPICIOUS IMAGE OR LOGO / MEDIUM
# # 50.00 – 74.99  %: SUSPICIOUS IMAGE OR LOGO / HIGH
# # 0.00  – 49.99  %: SUSPICIOUS IMAGE OR LOGO / CRITICAL
# SIMILARITY_THRESHOLDS = {
#     "AUTHENTIC": 90.00,
#     "MEDIUM": 75.00,
#     "HIGH": 50.00,
#     "CRITICAL": 0.00
# }

# def classify_similarity(sim_pct: float) -> Tuple[str, str]:
#     """
#     Returns (match_status, risk_severity) according to centralized thresholds.
#     """
#     if sim_pct >= SIMILARITY_THRESHOLDS["AUTHENTIC"]:
#         return "AUTHENTIC", "NORMAL"
#     elif sim_pct >= SIMILARITY_THRESHOLDS["MEDIUM"]:
#         return "SUSPICIOUS IMAGE OR LOGO", "MEDIUM"
#     elif sim_pct >= SIMILARITY_THRESHOLDS["HIGH"]:
#         return "SUSPICIOUS IMAGE OR LOGO", "HIGH"
#     else:
#         return "SUSPICIOUS IMAGE OR LOGO", "CRITICAL"


# def calculate_dhash(image: Image.Image, hash_size: int = 8) -> int:
#     """
#     Computes difference hash (dHash) of an image:
#     Resizes to (hash_size + 1, hash_size) in grayscale, compares adjacent horizontal pixels,
#     and returns a 64-bit integer.
#     """
#     try:
#         img = image.convert('L').resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
#         pixels = list(img.getdata())
#         difference = []
#         for row in range(hash_size):
#             for col in range(hash_size):
#                 pixel_left = pixels[row * (hash_size + 1) + col]
#                 pixel_right = pixels[row * (hash_size + 1) + col + 1]
#                 difference.append(pixel_left > pixel_right)
#         decimal_val = 0
#         for index, val in enumerate(difference):
#             if val:
#                 decimal_val += 2 ** index
#         return decimal_val
#     except Exception as e:
#         logger.error(f"Error computing dhash: {e}")
#         return 0


# def hamming_distance(h1: int, h2: int) -> int:
#     """Calculates bit difference between two 64-bit integer hashes."""
#     x = h1 ^ h2
#     return bin(x).count('1')


# def compute_sim_from_hashes(h1: int, h2: int, max_bits: int = 64) -> float:
#     """
#     Computes perceptual similarity percentage (0.00 to 100.00) based on Hamming distance.
#     0 bits difference = 100.00% similarity.
#     """
#     dist = hamming_distance(h1, h2)
#     sim = max(0.0, 100.0 - (dist / float(max_bits)) * 100.0)
#     return round(sim, 2)


# async def fetch_image(url: str, timeout: float = 10.0) -> Tuple[Optional[Image.Image], Optional[str]]:
#     """
#     Safely fetches and decodes an image from a live URL or data URI.
#     Returns (PIL.Image, None) on success, or (None, error_str) on failure.
#     DOES NOT use mock fallbacks or silent placeholders.
#     """
#     if not url or not isinstance(url, str):
#         return None, "Image URL is empty or missing."
    
#     clean_url = url.strip()

#     # Support base64 data URIs
#     if clean_url.startswith("data:image/"):
#         try:
#             if "," in clean_url:
#                 _, b64_part = clean_url.split(",", 1)
#             else:
#                 b64_part = clean_url
#             raw_bytes = base64.b64decode(b64_part)
#             img = Image.open(io.BytesIO(raw_bytes))
#             img.load()
#             return img, None
#         except Exception as e:
#             return None, f"Failed to decode base64 image data URI: {str(e)}"

#     if not clean_url.startswith(('http://', 'https://')):
#         return None, f"Invalid URL scheme: '{clean_url}'. URL must begin with http:// or https://"

#     # Detect if user entered an HTML webpage link rather than an image URL
#     path_lower = urlparse(clean_url).path.lower()
#     if path_lower.endswith(('.htm', '.html', '.php', '.asp', '.aspx', '.jsp')):
#         return None, f"URL points to a webpage document ({path_lower.split('.')[-1]}), not a direct image file. Please provide a direct image URL ending in .png, .jpg, .svg, or .webp"

#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
#         "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
#         "Accept-Language": "en-US,en;q=0.9"
#     }

#     raw_content = None
#     fetch_err = None

#     # Tier 1: Try async httpx client
#     try:
#         async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers, verify=False) as client:
#             resp = await client.get(clean_url)
#             if resp.status_code == 200:
#                 content_type = resp.headers.get("content-type", "").lower()
#                 if "text/html" in content_type:
#                     return None, f"URL returned HTML webpage content instead of an image file ({clean_url}). Please provide a direct image URL."
#                 raw_content = resp.content
#             else:
#                 fetch_err = f"HTTP {resp.status_code} ({resp.reason_phrase})"
#     except Exception as e:
#         fetch_err = str(e)

#     # Tier 2: If httpx failed or was blocked by WAF (403/429), fallback to urllib
#     if raw_content is None:
#         def _urllib_fetch_img(target: str):
#             ctx = ssl.create_default_context()
#             ctx.check_hostname = False
#             ctx.verify_mode = ssl.CERT_NONE
#             req = urllib.request.Request(target, headers=headers)
#             try:
#                 with urllib.request.urlopen(req, context=ctx, timeout=timeout) as r:
#                     c_type = r.headers.get("content-type", "").lower()
#                     if "text/html" in c_type:
#                         return None, "URL returned HTML webpage content instead of an image file"
#                     return r.read(), None
#             except urllib.error.HTTPError as he:
#                 return None, f"HTTP {he.code} ({he.reason})"
#             except Exception as ex:
#                 return None, str(ex)

#         try:
#             u_bytes, u_err = await asyncio.to_thread(_urllib_fetch_img, clean_url)
#             if u_bytes:
#                 raw_content = u_bytes
#             elif u_err:
#                 fetch_err = u_err
#         except Exception as e:
#             fetch_err = str(e)

#     if raw_content is None:
#         return None, f"Could not retrieve image from {clean_url}: {fetch_err or 'Connection failed'}"

#     try:
#         img = Image.open(io.BytesIO(raw_content))
#         img.load()  # Verify complete image stream can be decoded
#         return img, None
#     except Exception as decode_err:
#         return None, f"Failed to decode image data from {clean_url}: {str(decode_err)}"


# async def compare_logos(
#     official_logo_url: str | None,
#     candidate_logo_url: str | None,
#     fallback_hint: Optional[float] = None
# ) -> Dict[str, Any]:
#     """
#     Compares two real images using perceptual difference hashing (dHash).
#     Fetches actual images from both supplied URLs.
#     Computes real dHash for each image, computes Hamming bit distance,
#     and calculates similarity percentage.
#     Classifies result into:
#       - match_status: 'AUTHENTIC' (>= 90.00%) or 'SUSPICIOUS IMAGE OR LOGO' (< 90.00%)
#       - risk_severity: 'NORMAL', 'MEDIUM', 'HIGH', 'CRITICAL'
#     Returns clear failure state if either image cannot be retrieved or decoded (unless fallback_hint is provided).
#     """
#     if not candidate_logo_url or not candidate_logo_url.strip():
#         if fallback_hint is not None:
#             m_stat, r_sev = classify_similarity(fallback_hint)
#             return {
#                 "success": True,
#                 "similarity_score": fallback_hint,
#                 "similarity_pct": fallback_hint,
#                 "match_status": m_stat,
#                 "risk_severity": r_sev,
#                 "hamming_distance": int(round((100.0 - fallback_hint) * 0.64)),
#                 "dhash_candidate": "0000000000000000",
#                 "dhash_official": "0000000000000000",
#                 "is_identical": False,
#                 "candidate_image_url": "",
#                 "official_image_url": official_logo_url or "",
#                 "tags": ["Estimated Perceptual Likeness"],
#                 "explanation": f"Estimated visual correlation based on brand signals ({fallback_hint:.1f}%)."
#             }
#         return {
#             "success": False,
#             "error": "Candidate Suspicious Image / Logo URL is required."
#         }

#     if not official_logo_url or not official_logo_url.strip():
#         if fallback_hint is not None:
#             m_stat, r_sev = classify_similarity(fallback_hint)
#             return {
#                 "success": True,
#                 "similarity_score": fallback_hint,
#                 "similarity_pct": fallback_hint,
#                 "match_status": m_stat,
#                 "risk_severity": r_sev,
#                 "hamming_distance": int(round((100.0 - fallback_hint) * 0.64)),
#                 "dhash_candidate": "0000000000000000",
#                 "dhash_official": "0000000000000000",
#                 "is_identical": False,
#                 "candidate_image_url": candidate_logo_url or "",
#                 "official_image_url": "",
#                 "tags": ["Estimated Perceptual Likeness"],
#                 "explanation": f"Estimated visual correlation based on brand signals ({fallback_hint:.1f}%)."
#             }
#         return {
#             "success": False,
#             "error": "Official Brand Trademark Logo URL is required."
#         }

#     cand_url = candidate_logo_url.strip()
#     off_url = official_logo_url.strip()

#     # 1. Fetch Candidate Image
#     img_cand, err_cand = await fetch_image(cand_url)
#     if err_cand:
#         if fallback_hint is not None:
#             m_stat, r_sev = classify_similarity(fallback_hint)
#             return {
#                 "success": True,
#                 "similarity_score": fallback_hint,
#                 "similarity_pct": fallback_hint,
#                 "match_status": m_stat,
#                 "risk_severity": r_sev,
#                 "hamming_distance": int(round((100.0 - fallback_hint) * 0.64)),
#                 "dhash_candidate": "0000000000000000",
#                 "dhash_official": "0000000000000000",
#                 "is_identical": False,
#                 "candidate_image_url": cand_url,
#                 "official_image_url": off_url,
#                 "tags": ["Fallback Heuristic Approximation"],
#                 "explanation": f"Candidate image unreachable; estimated likeness applied ({fallback_hint:.1f}%)."
#             }
#         return {
#             "success": False,
#             "error": f"Failed to load candidate image: {err_cand}",
#             "failed_url": cand_url,
#             "target": "candidate"
#         }

#     # 2. Fetch Official Brand Logo
#     img_off, err_off = await fetch_image(off_url)
#     if err_off:
#         if fallback_hint is not None:
#             m_stat, r_sev = classify_similarity(fallback_hint)
#             return {
#                 "success": True,
#                 "similarity_score": fallback_hint,
#                 "similarity_pct": fallback_hint,
#                 "match_status": m_stat,
#                 "risk_severity": r_sev,
#                 "hamming_distance": int(round((100.0 - fallback_hint) * 0.64)),
#                 "dhash_candidate": "0000000000000000",
#                 "dhash_official": "0000000000000000",
#                 "is_identical": False,
#                 "candidate_image_url": cand_url,
#                 "official_image_url": off_url,
#                 "tags": ["Fallback Heuristic Approximation"],
#                 "explanation": f"Official brand logo unreachable; estimated likeness applied ({fallback_hint:.1f}%)."
#             }
#         return {
#             "success": False,
#             "error": f"Failed to load official brand logo: {err_off}",
#             "failed_url": off_url,
#             "target": "official"
#         }

#     # 3. Compute Perceptual Hashes (dHash) on actual decoded images
#     h_cand = calculate_dhash(img_cand)
#     h_off = calculate_dhash(img_off)
#     dist = hamming_distance(h_cand, h_off)
#     sim_pct = compute_sim_from_hashes(h_cand, h_off)

#     match_status, risk_severity = classify_similarity(sim_pct)
#     is_identical = (dist == 0)

#     # 4. Generate Diagnostic Security Tags
#     tags = []
#     if match_status == "AUTHENTIC":
#         tags.append("Authentic Brand Asset Alignment")
#         tags.append(f"{dist}-Bit Perceptual Distance")
#         if is_identical:
#             tags.append("Exact Cryptographic Asset Match")
#     else:
#         if sim_pct >= 75.0:
#             tags.append("High Likeness / Potential Trademark Infringement")
#             tags.append("Cropped or Modified Asset")
#         elif sim_pct >= 50.0:
#             tags.append("Moderate Visual Resemblance")
#         else:
#             tags.append("Dissimilar Asset Geometry")
#             tags.append("Low Perceptual Correlation")

#     return {
#         "success": True,
#         "similarity_pct": sim_pct,
#         "similarity_score": sim_pct,
#         "match_status": match_status,
#         "risk_severity": risk_severity,
#         "hamming_distance": dist,
#         "dhash_candidate": f"{h_cand:016x}",
#         "dhash_official": f"{h_off:016x}",
#         "is_identical": is_identical,
#         "is_direct_copy": (sim_pct >= 90.0) and not is_identical,
#         "is_cropped_or_recolored": (75.0 <= sim_pct < 90.0),
#         "candidate_image_url": cand_url,
#         "official_image_url": off_url,
#         "tags": tags,
#         "thresholds": SIMILARITY_THRESHOLDS,
#         "explanation": f"Perceptual dHash analysis indicates {sim_pct:.2f}% visual likeness with {dist} bits Hamming distance. Status: {match_status} (Severity: {risk_severity})."
#     }
  


import io
import base64
import logging
from typing import Optional, Tuple, Dict, Any
from urllib.parse import urlparse
from PIL import Image

from app.utils.safe_http import SafeFetchError, fetch_public_url

logger = logging.getLogger("brandshield.image_sim")

# =========================================================================
# CENTRALIZED SIMILARITY THRESHOLDS & RISK CLASSIFICATION
# =========================================================================
SIMILARITY_THRESHOLDS = {
    "AUTHENTIC": 90.00,
    "MEDIUM": 75.00,
    "HIGH": 50.00,
    "CRITICAL": 0.00
}

def classify_similarity(sim_pct: float) -> Tuple[str, str]:
    """
    Returns (match_status, risk_severity) according to centralized thresholds.
    """
    if sim_pct >= SIMILARITY_THRESHOLDS["AUTHENTIC"]:
        return "AUTHENTIC", "NORMAL"
    elif sim_pct >= SIMILARITY_THRESHOLDS["MEDIUM"]:
        return "SUSPICIOUS IMAGE OR LOGO", "MEDIUM"
    elif sim_pct >= SIMILARITY_THRESHOLDS["HIGH"]:
        return "SUSPICIOUS IMAGE OR LOGO", "HIGH"
    else:
        return "SUSPICIOUS IMAGE OR LOGO", "CRITICAL"


def calculate_dhash(image: Image.Image, hash_size: int = 8) -> int:
    """
    Computes difference hash (dHash) of an image:
    Resizes to (hash_size + 1, hash_size) in grayscale, compares adjacent horizontal pixels,
    and returns a 64-bit integer.
    """
    try:
        img = image.convert('L').resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
        pixels = list(img.getdata())
        difference = []
        for row in range(hash_size):
            for col in range(hash_size):
                pixel_left = pixels[row * (hash_size + 1) + col]
                pixel_right = pixels[row * (hash_size + 1) + col + 1]
                difference.append(pixel_left > pixel_right)
        decimal_val = 0
        for index, val in enumerate(difference):
            if val:
                decimal_val += 2 ** index
        return decimal_val
    except Exception as e:
        logger.error(f"Error computing dhash: {e}")
        return 0


def hamming_distance(h1: int, h2: int) -> int:
    """Calculates bit difference between two 64-bit integer hashes."""
    x = h1 ^ h2
    return bin(x).count('1')


def compute_sim_from_hashes(h1: int, h2: int, max_bits: int = 64) -> float:
    """
    Computes perceptual similarity percentage (0.00 to 100.00) based on Hamming distance.
    0 bits difference = 100.00% similarity.
    """
    dist = hamming_distance(h1, h2)
    sim = max(0.0, 100.0 - (dist / float(max_bits)) * 100.0)
    return round(sim, 2)


async def fetch_image(url: str, timeout: float = 10.0) -> Tuple[Optional[Image.Image], Optional[str]]:
    """
    Safely fetches and decodes an image from a live URL or data URI.
    Returns (PIL.Image, None) on success, or (None, error_str) on failure.
    """
    if not url or not isinstance(url, str):
        return None, "Image URL is empty or missing."
    
    clean_url = url.strip()
    if len(clean_url) > 14 * 1024 * 1024:
        return None, "Image input is too large."

    # Support base64 data URIs
    if clean_url.startswith("data:image/"):
        try:
            if "," not in clean_url:
                return None, "Invalid image data URI."
            _, b64_part = clean_url.split(",", 1)
            raw_bytes = base64.b64decode(b64_part, validate=True)
            if len(raw_bytes) > 10 * 1024 * 1024:
                return None, "Image input is too large."
            img = Image.open(io.BytesIO(raw_bytes))
            img.load()
            return img, None
        except Exception:
            return None, "Failed to decode image data URI."

    if not clean_url.startswith(('http://', 'https://')):
        return None, f"Invalid URL scheme: '{clean_url}'. URL must begin with http:// or https://"

    path_lower = urlparse(clean_url).path.lower()
    if path_lower.endswith(('.htm', '.html', '.php', '.asp', '.aspx', '.jsp')):
        return None, f"URL points to a webpage document ({path_lower.split('.')[-1]}), not a direct image file."

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        response = await fetch_public_url(
            clean_url,
            timeout=timeout,
            headers=headers,
            max_bytes=10 * 1024 * 1024,
        )
    except SafeFetchError as exc:
        return None, str(exc)

    if response.status_code != 200:
        return None, f"Image request failed with HTTP {response.status_code}."

    if "text/html" in response.content_type.lower():
        return None, "URL returned HTML webpage content instead of an image file."

    try:
        img = Image.open(io.BytesIO(response.body))
        img.load()
        return img, None
    except Exception:
        return None, "Failed to decode image data."


async def compare_logos(
    official_logo_url: Optional[str],
    candidate_logo_url: Optional[str],
    fallback_hint: Optional[float] = None
) -> Dict[str, Any]:
    """
    Compares two real images using perceptual difference hashing (dHash).
    """
    if not candidate_logo_url or not candidate_logo_url.strip():
        if fallback_hint is not None:
            m_stat, r_sev = classify_similarity(fallback_hint)
            return {
                "success": True,
                "similarity_score": fallback_hint,
                "similarity_pct": fallback_hint,
                "match_status": m_stat,
                "risk_severity": r_sev,
                "hamming_distance": int(round((100.0 - fallback_hint) * 0.64)),
                "dhash_candidate": "0000000000000000",
                "dhash_official": "0000000000000000",
                "is_identical": False,
                "candidate_image_url": "",
                "official_image_url": official_logo_url or "",
                "tags": ["Estimated Perceptual Likeness"],
                "explanation": f"Estimated visual correlation based on brand signals ({fallback_hint:.1f}%)."
            }
        return {
            "success": False,
            "error": "Candidate Suspicious Image / Logo URL is required."
        }

    if not official_logo_url or not official_logo_url.strip():
        if fallback_hint is not None:
            m_stat, r_sev = classify_similarity(fallback_hint)
            return {
                "success": True,
                "similarity_score": fallback_hint,
                "similarity_pct": fallback_hint,
                "match_status": m_stat,
                "risk_severity": r_sev,
                "hamming_distance": int(round((100.0 - fallback_hint) * 0.64)),
                "dhash_candidate": "0000000000000000",
                "dhash_official": "0000000000000000",
                "is_identical": False,
                "candidate_image_url": candidate_logo_url or "",
                "official_image_url": "",
                "tags": ["Estimated Perceptual Likeness"],
                "explanation": f"Estimated visual correlation based on brand signals ({fallback_hint:.1f}%)."
            }
        return {
            "success": False,
            "error": "Official Brand Trademark Logo URL is required."
        }

    cand_url = candidate_logo_url.strip()
    off_url = official_logo_url.strip()

    # 1. Fetch Candidate Image
    img_cand, err_cand = await fetch_image(cand_url)
    if err_cand:
        if fallback_hint is not None:
            m_stat, r_sev = classify_similarity(fallback_hint)
            return {
                "success": True,
                "similarity_score": fallback_hint,
                "similarity_pct": fallback_hint,
                "match_status": m_stat,
                "risk_severity": r_sev,
                "hamming_distance": int(round((100.0 - fallback_hint) * 0.64)),
                "dhash_candidate": "0000000000000000",
                "dhash_official": "0000000000000000",
                "is_identical": False,
                "candidate_image_url": cand_url,
                "official_image_url": off_url,
                "tags": ["Fallback Heuristic Approximation"],
                "explanation": f"Candidate image unreachable; estimated likeness applied ({fallback_hint:.1f}%)."
            }
        return {
            "success": False,
            "error": f"Failed to load candidate image: {err_cand}",
            "failed_url": cand_url,
            "target": "candidate"
        }

    # 2. Fetch Official Brand Logo
    img_off, err_off = await fetch_image(off_url)
    if err_off:
        if fallback_hint is not None:
            m_stat, r_sev = classify_similarity(fallback_hint)
            return {
                "success": True,
                "similarity_score": fallback_hint,
                "similarity_pct": fallback_hint,
                "match_status": m_stat,
                "risk_severity": r_sev,
                "hamming_distance": int(round((100.0 - fallback_hint) * 0.64)),
                "dhash_candidate": "0000000000000000",
                "dhash_official": "0000000000000000",
                "is_identical": False,
                "candidate_image_url": cand_url,
                "official_image_url": off_url,
                "tags": ["Fallback Heuristic Approximation"],
                "explanation": f"Official brand logo unreachable; estimated likeness applied ({fallback_hint:.1f}%)."
            }
        return {
            "success": False,
            "error": f"Failed to load official brand logo: {err_off}",
            "failed_url": off_url,
            "target": "official"
        }

    # 3. Compute Perceptual Hashes (dHash) on actual decoded images
    h_cand = calculate_dhash(img_cand)
    h_off = calculate_dhash(img_off)
    dist = hamming_distance(h_cand, h_off)
    sim_pct = compute_sim_from_hashes(h_cand, h_off)

    match_status, risk_severity = classify_similarity(sim_pct)
    is_identical = (dist == 0)

    # 4. Generate Diagnostic Security Tags
    tags = []
    if match_status == "AUTHENTIC":
        tags.append("Authentic Brand Asset Alignment")
        tags.append(f"{dist}-Bit Perceptual Distance")
        if is_identical:
            tags.append("Exact Cryptographic Asset Match")
    else:
        if sim_pct >= 75.0:
            tags.append("High Likeness / Potential Trademark Infringement")
            tags.append("Cropped or Modified Asset")
        elif sim_pct >= 50.0:
            tags.append("Moderate Visual Resemblance")
        else:
            tags.append("Dissimilar Asset Geometry")
            tags.append("Low Perceptual Correlation")

    return {
        "success": True,
        "similarity_pct": sim_pct,
        "similarity_score": sim_pct,
        "match_status": match_status,
        "risk_severity": risk_severity,
        "hamming_distance": dist,
        "dhash_candidate": f"{h_cand:016x}",
        "dhash_official": f"{h_off:016x}",
        "is_identical": is_identical,
        "is_direct_copy": (sim_pct >= 90.0) and not is_identical,
        "is_cropped_or_recolored": (75.0 <= sim_pct < 90.0),
        "candidate_image_url": cand_url,
        "official_image_url": off_url,
        "tags": tags,
        "thresholds": SIMILARITY_THRESHOLDS,
        "explanation": f"Perceptual dHash analysis indicates {sim_pct:.2f}% visual likeness with {dist} bits Hamming distance. Status: {match_status} (Severity: {risk_severity})."
    }