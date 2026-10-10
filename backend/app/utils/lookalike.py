import re
import unicodedata
from rapidfuzz import fuzz, distance

# Common homoglyphs and visually similar character mappings (confusables)
HOMOGLYPH_MAP = {
    '0': 'o', '1': 'l', '3': 'e', '4': 'a', '5': 's', '8': 'b',
    '@': 'a', '$': 's', '!': 'i', '|': 'l',
    # Cyrillic homoglyphs commonly used in typo-squatting
    'а': 'a', 'с': 'c', 'е': 'e', 'о': 'o', 'р': 'p', 'х': 'x', 'у': 'y',
    'і': 'i', 'ј': 'j', 'ѕ': 's', 'ԁ': 'd', 'ԛ': 'q', 'ԝ': 'w',
    # Greek
    'α': 'a', 'ο': 'o', 'ρ': 'p', 'υ': 'u', 'ν': 'v'
}

SUSPICIOUS_SUFFIXES = [
    "support", "care", "customercare", "help", "official", "security",
    "secure", "verify", "verification", "desk", "helpdesk", "team",
    "service", "services", "online", "login", "signin", "portal",
    "rewards", "reward", "claims", "refund", "kyc", "alert", "fraud"
]

def normalize_text(text: str) -> str:
    """Strip accents and lower case"""
    if not text:
        return ""
    text = text.lower().strip()
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')

def detect_homoglyphs(text: str) -> tuple[str, list[dict]]:
    """Detects Unicode and character homoglyphs and normalizes them."""
    found = []
    normalized_chars = []
    
    # Check for multi-character illusions: 'rn' -> 'm', 'vv' -> 'w'
    temp_text = text.lower()
    if 'rn' in temp_text:
        found.append({'type': 'visual_illusion', 'original': 'rn', 'resembles': 'm'})
    if 'vv' in temp_text:
        found.append({'type': 'visual_illusion', 'original': 'vv', 'resembles': 'w'})

    for idx, ch in enumerate(text.lower()):
        if ch in HOMOGLYPH_MAP:
            sub = HOMOGLYPH_MAP[ch]
            found.append({
                'index': idx,
                'char': ch,
                'resembles': sub,
                'type': 'homoglyph_substitution'
            })
            normalized_chars.append(sub)
        else:
            normalized_chars.append(ch)
            
    return "".join(normalized_chars), found

def check_character_swap(str1: str, str2: str) -> bool:
    """Checks if str2 is formed by a single or double adjacent character swap of str1."""
    s1 = re.sub(r'[^a-z0-9]', '', str1.lower())
    s2 = re.sub(r'[^a-z0-9]', '', str2.lower())
    if len(s1) != len(s2) or s1 == s2:
        return False
    
    damerau_dist = distance.DamerauLevenshtein.distance(s1, s2)
    # Distance of 1 with identical length means transposition or single substitution
    if damerau_dist == 1:
        # Verify it's a swap, i.e., sorted characters are identical
        return sorted(s1) == sorted(s2)
    return False

def check_added_words(candidate: str, brand_name: str) -> list[str]:
    """Identifies added words like 'support', 'helpdesk', 'care' only when candidate actually resembles the brand."""
    cand_clean = re.sub(r'[^a-z0-9]', '', candidate.lower())
    brand_clean = re.sub(r'[^a-z0-9]', '', brand_name.lower())
    
    cand_norm = re.sub(r'[^a-z0-9\s]', ' ', candidate.lower())
    brand_norm = re.sub(r'[^a-z0-9\s]', ' ', brand_name.lower())
    
    cand_tokens = set(cand_norm.split())
    brand_tokens = set([t for t in brand_norm.split() if len(t) >= 3])
    
    # Critical Guard: candidate MUST contain the brand name or share core brand tokens
    # Otherwise an unrelated handle like 'alluarjunonline' is NOT a brand lookalike!
    has_brand_presence = (
        (brand_clean in cand_clean) or
        bool(cand_tokens.intersection(brand_tokens)) or
        (fuzz.partial_ratio(brand_clean, cand_clean) >= 75 and len(brand_clean) >= 4)
    )
    if not has_brand_presence:
        return []
    
    extra = cand_tokens - brand_tokens
    matched_suspicious = [w for w in extra if w in SUSPICIOUS_SUFFIXES or any(s in w for s in SUSPICIOUS_SUFFIXES)]
    return matched_suspicious

def analyze_lookalike(candidate_name: str, brand_name: str, brand_aliases: list[str] = None) -> dict:
    """
    Multi-faceted look-alike name analysis evaluating:
    - RapidFuzz similarity ratios
    - Character transpositions/swaps
    - Homoglyphs & visual illusions
    - Added words / customer support claims
    - Spacing and punctuation variants
    """
    if not candidate_name or not brand_name:
        return {
            "similarity_score": 0.0,
            "lookalike_type": "NONE",
            "is_suspicious_match": False,
            "details": {}
        }
    
    targets = [brand_name] + (brand_aliases or [])
    best_result = None
    best_score = -1.0
    
    for target in targets:
        # Raw comparisons
        c_raw = candidate_name.strip()
        t_raw = target.strip()
        
        # Normalized alphanumeric
        c_clean = re.sub(r'[^a-z0-9]', '', c_raw.lower())
        t_clean = re.sub(r'[^a-z0-9]', '', t_raw.lower())
        
        # Homoglyph detection
        c_homo_norm, homoglyphs = detect_homoglyphs(c_raw)
        c_homo_clean = re.sub(r'[^a-z0-9]', '', c_homo_norm.lower())
        
        # Swaps
        swap_detected = check_character_swap(t_clean, c_clean) or check_character_swap(t_clean, c_homo_clean)
        
        # Added words
        added_words = check_added_words(c_raw, t_raw)
        
        # Spacing/Separator check: if alphanumeric only matches exactly, but separators differ
        spacing_variant = (c_clean == t_clean and c_raw.lower() != t_raw.lower())
        
        # Fuzz ratios
        ratio = fuzz.ratio(c_clean, t_clean)
        token_sort = fuzz.token_sort_ratio(c_raw.lower(), t_raw.lower())
        partial = fuzz.partial_ratio(t_clean, c_clean) if t_clean and c_clean else 0
        
        # Calculate composite similarity
        # If clean strings match exactly:
        if c_clean == t_clean:
            score = 100.0
            lookalike_type = "EXACT_OR_SPACING_VARIANT" if spacing_variant else "EXACT"
            explanation = "Exact match or punctuation/spacing variation of brand name."
        elif swap_detected:
            score = 94.0
            lookalike_type = "CHARACTER_SWAP"
            explanation = f"Detected character transposition/swap imitating '{target}'."
        elif len(homoglyphs) > 0 and (c_homo_clean == t_clean or fuzz.ratio(c_homo_clean, t_clean) > 85):
            score = 96.0
            lookalike_type = "HOMOGLYPH_SUBSTITUTION"
            chars = ", ".join([f"'{h.get('char')}'" for h in homoglyphs[:3]])
            explanation = f"Detected look-alike / homoglyph substitution ({chars}) mimicking '{target}'."
        elif added_words:
            # e.g., "ABC Bank Support"
            score = max(88.0, float(partial))
            lookalike_type = "ADDED_WORDS"
            explanation = f"Detected brand name with high-risk added keywords: {', '.join(added_words)}."
        elif ratio >= 80 or token_sort >= 82:
            score = float(max(ratio, token_sort))
            lookalike_type = "FUZZY_SIMILARITY"
            explanation = f"High fuzzy phonetic/orthographic similarity ({int(score)}%) with '{target}'."
        elif partial >= 85 and len(t_clean) >= 4 and t_clean in c_clean:
            score = float(partial) * 0.92
            lookalike_type = "SUBSTRING_IMPERSONATION"
            explanation = f"Brand name '{target}' is embedded within suspicious string '{candidate_name}'."
        else:
            score = float(max(ratio, token_sort * 0.7))
            lookalike_type = "LOW_SIMILARITY"
            explanation = "Minimal name resemblance to official brand."
            
        result = {
            "target_evaluated": target,
            "similarity_score": round(min(100.0, score), 1),
            "lookalike_type": lookalike_type,
            "is_suspicious_match": score >= 70.0,
            "has_character_swap": swap_detected,
            "has_homoglyphs": len(homoglyphs) > 0,
            "homoglyphs_detected": homoglyphs,
            "added_words": added_words,
            "spacing_variant": spacing_variant,
            "fuzz_metrics": {
                "ratio": round(ratio, 1),
                "token_sort_ratio": round(token_sort, 1),
                "partial_ratio": round(partial, 1)
            },
            "explanation": explanation
        }
        
        if score > best_score:
            best_score = score
            best_result = result
            
    return best_result or {
        "similarity_score": 0.0,
        "lookalike_type": "NONE",
        "is_suspicious_match": False,
        "explanation": "No match."
    }
