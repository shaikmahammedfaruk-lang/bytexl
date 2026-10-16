
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId

from app.database import get_db
from app.routes.access_control import (
    brand_child_filter,
    is_brand_child_visible,
    readable_brand_children_filter,
    readable_brand_filter as access_readable_brand_filter,
)
from app.services.auth_service import require_current_user
from app.models.schemas import InvestigationCreate, InvestigationResponse

logger = logging.getLogger("brandshield.routes.investigations")
router = APIRouter(
    prefix="/investigations",
    tags=["AI Threat Investigator"],
)


# ---------------------------------------------------------
# AUTHENTICATION AND ACCESS CONTROL
# ---------------------------------------------------------

def get_user_id(user: dict) -> str:
    user_id = user.get("id") or user.get("_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authenticated user ID not found",
        )

    return str(user_id)


def readable_brand_filter(user_id: str) -> dict:
    return access_readable_brand_filter(user_id)


async def get_brand_for_read(db, brand_id: str, user_id: str) -> dict:
    if not ObjectId.is_valid(str(brand_id)):
        raise HTTPException(
            status_code=404,
            detail="Investigation not found",
        )

    brand = await db.brands.find_one({
        "_id": ObjectId(str(brand_id)),
        **readable_brand_filter(user_id),
    })

    if not brand:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found",
        )

    return brand


async def get_owned_brand(db, brand_id: str, user_id: str) -> dict:
    if not ObjectId.is_valid(str(brand_id)):
        raise HTTPException(status_code=404, detail="Threat not found")

    brand = await db.brands.find_one({
        "_id": ObjectId(str(brand_id)),
        "owner_id": user_id,
    })

    if not brand:
        raise HTTPException(
            status_code=404,
            detail="Threat not found or you do not own its brand",
        )

    return brand


async def get_authorized_investigation(
    db,
    investigation_id: str,
    user_id: str,
) -> dict:
    if not ObjectId.is_valid(investigation_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid investigation ID",
        )

    brands = await db.brands.find(
        readable_brand_filter(user_id),
        {"_id": 1, "owner_id": 1, "is_demo": 1, "is_shared": 1},
    ).to_list(length=5000)
    investigation_scope = readable_brand_children_filter(
        brands,
        user_id,
    )
    investigation = await db.investigations.find_one({
        "$and": [
            {"_id": ObjectId(investigation_id)},
            investigation_scope,
        ]
    })

    if not investigation:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found",
        )

    brand_id = investigation.get("brand_id")

    if not brand_id:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found",
        )

    brand = await get_brand_for_read(db, str(brand_id), user_id)
    if not is_brand_child_visible(brand, user_id, investigation):
        raise HTTPException(
            status_code=404,
            detail="Investigation not found",
        )

    return investigation


# ---------------------------------------------------------
# RESPONSE SERIALIZATION
# ---------------------------------------------------------

def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc

    doc["id"] = str(doc.pop("_id"))
    return doc


# ---------------------------------------------------------
# CREATE INVESTIGATION
# Only the owner of a private brand may start one.
# ---------------------------------------------------------

@router.post("", response_model=InvestigationResponse)
async def create_investigation(
    inv_in: InvestigationCreate,
    user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(user)

    threat_id = str(inv_in.threat_id)

    if not ObjectId.is_valid(threat_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid threat ID",
        )

    owned_brands = await db.brands.find(
        {"owner_id": user_id},
        {"_id": 1, "owner_id": 1, "is_demo": 1, "is_shared": 1},
    ).to_list(length=5000)
    threat_scope = readable_brand_children_filter(
        owned_brands,
        user_id,
    )
    threat = await db.threats.find_one({
        "$and": [
            {"_id": ObjectId(threat_id)},
            threat_scope,
        ]
    })

    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")

    brand_id = str(threat.get("brand_id", ""))

    # Only the owner may initiate an investigation or change threat status.
    brand = await get_owned_brand(db, brand_id, user_id)
    if not is_brand_child_visible(brand, user_id, threat):
        raise HTTPException(status_code=404, detail="Threat not found")
    brand_name = brand.get("name") or "Brand"

    # Return an existing investigation only after authorizing the threat.
    existing = await db.investigations.find_one({
        "threat_id": threat_id,
        "brand_id": str(brand["_id"]),
        "$or": [
            {"owner_id": user_id},
            {"owner_id": {"$exists": False}},
        ],
    })

    if existing:
        if str(existing.get("brand_id", "")) != str(brand["_id"]):
            raise HTTPException(
                status_code=404,
                detail="Investigation not found",
            )
        return serialize_doc(existing)

    now = datetime.utcnow()
    case_num = (
        f"INV-{now.strftime('%Y')}-"
        f"{str(int(now.timestamp()))[-4:]}"
    )

    factors = threat.get("detection_factors") or {}

    evidence_items = [
        {
            "type": "Infringing URL",
            "detail": threat.get("url"),
        },
        {
            "type": "Name Resemblance",
            "detail": (
                f"{factors.get('name_similarity', 0)}% similarity "
                f"({factors.get('lookalike_type')})"
            ),
        },
        {
            "type": "Logo Analysis",
            "detail": (
                f"{factors.get('logo_similarity', 0)}% visual alignment "
                f"with {brand_name} trademark"
            ),
        },
        {
            "type": "Targeting Triggers",
            "detail": (
                ", ".join(factors.get("targeting_phrases", []))
                or "Synthetic profile imitating support desk"
            ),
        },
    ]

    recommended_actions = [
        f"Generate certified evidence package for "
        f"{threat.get('platform')} takedown submission",
        "Correlate threat indicators with cross-platform campaign syndicate",
        "Assign SecOps analyst to monitor infrastructure mutations",
    ]

    detected_time = threat.get("detected_time") or now

    if hasattr(detected_time, "isoformat"):
        detected_time_text = detected_time.isoformat()
    else:
        detected_time_text = str(detected_time)

    timeline = [
        {
            "time": detected_time_text,
            "event": "Threat discovered by BrandShield crawler",
        },
        {
            "time": now.isoformat(),
            "event": (
                f"Automated AI Investigation initiated under Case {case_num}"
            ),
        },
    ]

    investigation_doc = {
        "threat_id": threat_id,
        "brand_id": str(brand["_id"]),
        "owner_id": user_id,
        "case_number": case_num,
        "title": (
            inv_in.title
            or f"Investigation: {threat.get('threat_type')} "
               f"on {threat.get('platform')}"
        ),
        "status": "OPEN",
        "analyst": inv_in.analyst or "Senior Threat Analyst",
        "summary": (
            f"High-confidence {threat.get('threat_type')} identified "
            f"posing a potential threat to {brand_name} customers. "
            f"Risk score {threat.get('risk_score')}/100 with customer "
            f"impact score of {threat.get('customer_impact_score')}/100."
        ),
        "evidence_items": evidence_items,
        "recommended_actions": recommended_actions,
        "timeline": timeline,
        "created_at": now,
    }

    # Store the investigation for the authenticated brand owner.
    result = await db.investigations.insert_one(investigation_doc)

    # Update only the threat that was authorized above.
    await db.threats.update_one(
        {
            "_id": ObjectId(threat_id),
            "brand_id": str(brand["_id"]),
            "$or": [
                {"owner_id": user_id},
                {"owner_id": {"$exists": False}},
            ],
        },
        {
            "$set": {
                "status": "UNDER_INVESTIGATION",
                "updated_at": now,
            }
        },
    )

    investigation_doc["id"] = str(result.inserted_id)
    return investigation_doc


# ---------------------------------------------------------
# LIST INVESTIGATIONS
# ---------------------------------------------------------

@router.get("", response_model=List[InvestigationResponse])
async def list_investigations(
    brand_id: Optional[str] = None,
    user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(user)

    if brand_id:
        if not ObjectId.is_valid(brand_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid brand ID",
            )

        brand = await get_brand_for_read(db, brand_id, user_id)
        query = brand_child_filter(brand, user_id)
    else:
        cursor = db.brands.find(
            readable_brand_filter(user_id),
            {"_id": 1, "owner_id": 1, "is_demo": 1, "is_shared": 1},
        )
        brands = await cursor.to_list(length=5000)
        query = readable_brand_children_filter(brands, user_id)

    cursor = db.investigations.find(query).sort("created_at", -1)
    items = await cursor.to_list(length=500)

    return [serialize_doc(item) for item in items]


# ---------------------------------------------------------
# GET ONE INVESTIGATION
# ---------------------------------------------------------

@router.get("/{id}", response_model=InvestigationResponse)
async def get_investigation(
    id: str,
    user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(user)

    investigation = await get_authorized_investigation(
        db,
        id,
        user_id,
    )

    return serialize_doc(investigation)