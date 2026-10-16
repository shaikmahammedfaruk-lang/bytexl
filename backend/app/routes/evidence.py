import logging

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.routes.access_control import (
    brand_child_filter,
    is_shared_demo_brand,
    readable_brand_children_filter,
    readable_brand_filter,
)
from app.services.auth_service import require_current_user
from app.services.evidence_service import generate_evidence_package

logger = logging.getLogger("brandshield.routes.evidence")

router = APIRouter(
    prefix="/evidence",
    tags=["Evidence Center"],
)


def get_user_id(user: dict) -> str:
    user_id = user.get("id") or user.get("_id")
    return str(user_id) if user_id else ""


async def get_authorized_threat(
    db,
    threat_id: str,
    user_id: str,
):
    """Find a threat only when its associated brand is readable."""
    if not ObjectId.is_valid(threat_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid threat ID",
        )

    brands = await db.brands.find(
        readable_brand_filter(user_id),
        {"_id": 1, "owner_id": 1, "is_demo": 1, "is_shared": 1},
    ).to_list(length=5000)
    threat_scope = readable_brand_children_filter(brands, user_id)
    threat = await db.threats.find_one({
        "$and": [
            {"_id": ObjectId(threat_id)},
            threat_scope,
        ]
    })

    if not threat:
        raise HTTPException(
            status_code=404,
            detail="Threat not found",
        )

    brand_id = threat.get("brand_id")

    if not brand_id or not ObjectId.is_valid(brand_id):
        raise HTTPException(
            status_code=404,
            detail="Associated brand not found",
        )

    brand = await db.brands.find_one({
        "_id": ObjectId(brand_id),
        **readable_brand_filter(user_id),
    })

    if not brand:
        raise HTTPException(
            status_code=404,
            detail="Associated brand not found",
        )

    is_owner = str(brand.get("owner_id", "")) == user_id
    is_shared_demo = is_shared_demo_brand(brand)

    if is_owner:
        threat_owner_id = threat.get("owner_id")
        if threat_owner_id and str(threat_owner_id) != user_id:
            raise HTTPException(status_code=404, detail="Threat not found")
    elif not (
        "owner_id" in threat
        and threat.get("owner_id") is None
        and threat.get("is_demo") is True
        and threat.get("is_shared") is True
    ):
        raise HTTPException(status_code=404, detail="Threat not found")

    if not is_owner and not is_shared_demo:
        # Do not reveal whether another user's threat exists.
        raise HTTPException(
            status_code=404,
            detail="Threat not found",
        )

    return threat, brand, is_owner


def serialize_doc(doc: dict) -> dict:
    """Convert MongoDB document IDs to JSON-friendly strings."""
    if not doc:
        return doc

    result = dict(doc)

    if "_id" in result:
        result["id"] = str(result.pop("_id"))

    return result


@router.post("/{threat_id}/generate")
async def create_evidence_report(
    threat_id: str,
    current_user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(current_user)

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid user session",
        )

    threat, brand, is_owner = await get_authorized_threat(
        db,
        threat_id,
        user_id,
    )

    # Generating evidence writes a new record, so only the brand
    # owner may create it. Shared demo records are read-only.
    if not is_owner:
        raise HTTPException(
            status_code=403,
            detail="Evidence generation is disabled for shared demo data.",
        )

    evidence_doc = generate_evidence_package(threat, brand)

    # Store the threat ID consistently as a string.
    evidence_doc = dict(evidence_doc)
    evidence_doc["threat_id"] = str(threat["_id"])
    evidence_doc["brand_id"] = str(brand["_id"])
    evidence_doc["owner_id"] = user_id

    result = await db.evidence.insert_one(evidence_doc)
    evidence_doc["_id"] = result.inserted_id

    return serialize_doc(evidence_doc)


@router.get("/{threat_id}")
async def get_latest_evidence(
    threat_id: str,
    current_user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(current_user)

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid user session",
        )

    threat, brand, is_owner = await get_authorized_threat(
        db,
        threat_id,
        user_id,
    )

    # Scope evidence lookup to this authorized threat.
    doc = await db.evidence.find_one(
        {
            "threat_id": str(threat["_id"]),
            **brand_child_filter(brand, user_id),
        },
        sort=[("_id", -1)],
    )

    if doc:
        # For private records, verify that legacy evidence belongs
        # to this user's brand before returning it.
        evidence_brand_id = doc.get("brand_id")

        if evidence_brand_id and str(evidence_brand_id) != str(brand["_id"]):
            raise HTTPException(
                status_code=404,
                detail="Evidence not found",
            )

        return serialize_doc(doc)

    # Never create new evidence automatically for shared demo records.
    if not is_owner:
        raise HTTPException(
            status_code=404,
            detail="No evidence package exists for this demo threat.",
        )

    # Generate evidence only for a threat whose brand the user owns.
    return await create_evidence_report(
        threat_id,
        current_user=current_user,
    )