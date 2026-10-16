# import logging
# from typing import List, Optional
# from fastapi import APIRouter, HTTPException, Query
# from bson import ObjectId
# from app.database import get_db
# from app.models.schemas import CampaignResponse
# from app.services.correlation_engine import correlate_threats_into_campaigns

# logger = logging.getLogger("brandshield.routes.campaigns")
# router = APIRouter(prefix="/campaigns", tags=["Cross-Platform Threat Campaigns"])

# def serialize_doc(doc: dict) -> dict:
#     if not doc:
#         return doc
#     doc["id"] = str(doc.pop("_id"))
#     return doc

# @router.get("", response_model=List[CampaignResponse])
# async def list_campaigns(brand_id: Optional[str] = None):
#     db = get_db()
#     query = {}
#     if brand_id and ObjectId.is_valid(brand_id):
#         query["brand_id"] = brand_id

#     cursor = db.campaigns.find(query).sort("campaign_risk", -1)
#     items = await cursor.to_list(length=50)

#     # If no campaigns yet, run correlation
#     if not items and brand_id:
#         items = await correlate_threats_into_campaigns(db, brand_id)

#     return [serialize_doc(i) for i in items]

# @router.get("/{id}", response_model=CampaignResponse)
# async def get_campaign(id: str):
#     db = get_db()
#     if not ObjectId.is_valid(id):
#         raise HTTPException(status_code=400, detail="Invalid campaign ID")

#     campaign = await db.campaigns.find_one({"_id": ObjectId(id)})
#     if not campaign:
#         raise HTTPException(status_code=404, detail="Campaign not found")
#     return serialize_doc(campaign)

# @router.post("/recorrelate/{brand_id}")
# async def force_recorrelate(brand_id: str):
#     db = get_db()
#     if not ObjectId.is_valid(brand_id):
#         raise HTTPException(status_code=400, detail="Invalid brand ID")

#     campaigns = await correlate_threats_into_campaigns(db, brand_id)
#     return {"status": "success", "correlated_campaigns": len(campaigns)}




import logging
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
from app.models.schemas import CampaignResponse
from app.services.correlation_engine import correlate_threats_into_campaigns

logger = logging.getLogger("brandshield.routes.campaigns")
router = APIRouter(
    prefix="/campaigns",
    tags=["Cross-Platform Threat Campaigns"],
)


# ---------------------------------------------------------
# AUTHENTICATION AND BRAND OWNERSHIP
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


async def get_readable_brand(db, brand_id: str, user_id: str) -> dict:
    if not ObjectId.is_valid(brand_id):
        raise HTTPException(status_code=400, detail="Invalid brand ID")

    brand = await db.brands.find_one({
        "_id": ObjectId(brand_id),
        **readable_brand_filter(user_id),
    })

    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    return brand


async def get_owned_brand(db, brand_id: str, user_id: str) -> dict:
    if not ObjectId.is_valid(brand_id):
        raise HTTPException(status_code=400, detail="Invalid brand ID")

    brand = await db.brands.find_one({
        "_id": ObjectId(brand_id),
        "owner_id": user_id,
    })

    if not brand:
        raise HTTPException(
            status_code=404,
            detail="Brand not found or you do not own it",
        )

    return brand


async def get_authorized_campaign(
    db,
    campaign_id: str,
    user_id: str,
    writable: bool = False,
) -> dict:
    if not ObjectId.is_valid(campaign_id):
        raise HTTPException(status_code=400, detail="Invalid campaign ID")

    campaign = await db.campaigns.find_one({
        "_id": ObjectId(campaign_id)
    })

    if not campaign:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found",
        )

    brand_id = str(campaign.get("brand_id", ""))

    if not ObjectId.is_valid(brand_id):
        raise HTTPException(
            status_code=404,
            detail="Campaign not found",
        )

    if writable:
        brand = await get_owned_brand(db, brand_id, user_id)
    else:
        brand = await get_readable_brand(db, brand_id, user_id)

    if not is_brand_child_visible(brand, user_id, campaign):
        raise HTTPException(
            status_code=404,
            detail="Campaign not found",
        )

    return campaign


def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc

    doc["id"] = str(doc.pop("_id"))
    return doc


# ---------------------------------------------------------
# LIST CAMPAIGNS
# ---------------------------------------------------------

@router.get("", response_model=List[CampaignResponse])
async def list_campaigns(
    brand_id: Optional[str] = None,
    user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(user)

    if brand_id:
        brand = await get_readable_brand(db, brand_id, user_id)
        query = brand_child_filter(brand, user_id)
    else:
        cursor = db.brands.find(
            readable_brand_filter(user_id),
            {"_id": 1, "owner_id": 1, "is_demo": 1, "is_shared": 1},
        )
        brands = await cursor.to_list(length=5000)
        query = readable_brand_children_filter(brands, user_id)

    cursor = db.campaigns.find(query).sort("campaign_risk", -1)
    items = await cursor.to_list(length=200)

    # Generate campaigns only for a brand the current user owns.
    if not items and brand_id:
        brand = await get_readable_brand(db, brand_id, user_id)

        if str(brand.get("owner_id", "")) == user_id:
            items = await correlate_threats_into_campaigns(
                db,
                str(brand["_id"]),
                user_id,
            )

    return [serialize_doc(item) for item in items]


# ---------------------------------------------------------
# GET ONE CAMPAIGN
# ---------------------------------------------------------

@router.get("/{id}", response_model=CampaignResponse)
async def get_campaign(
    id: str,
    user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(user)

    campaign = await get_authorized_campaign(db, id, user_id)
    return serialize_doc(campaign)


# ---------------------------------------------------------
# RECORRELATE CAMPAIGNS
# Only the owner of a private brand can trigger this action.
# ---------------------------------------------------------

@router.post("/recorrelate/{brand_id}")
async def force_recorrelate(
    brand_id: str,
    user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(user)

    brand = await get_owned_brand(db, brand_id, user_id)

    campaigns = await correlate_threats_into_campaigns(
        db,
        str(brand["_id"]),
        user_id,
    )

    return {
        "status": "success",
        "correlated_campaigns": len(campaigns),
    }