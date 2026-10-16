# import os
# import re
# import uuid
# import logging
# from pathlib import Path
# from datetime import datetime
# from typing import List, Optional
# from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
# from bson import ObjectId
# from app.database import get_db
# from app.models.schemas import (
#     BrandCreate, BrandUpdate, BrandResponse,
#     OfficialAssetCreate, OfficialAssetUpdate, OfficialAssetResponse,
#     BrandWizardSyncRequest
# )

# logger = logging.getLogger("brandshield.routes.brands")
# router = APIRouter(prefix="/brands", tags=["Brands"])

# def serialize_doc(doc: dict) -> dict:
#     if not doc:
#         return doc
#     doc["id"] = str(doc.pop("_id"))
#     if "created_at" not in doc or doc["created_at"] is None:
#         doc["created_at"] = doc.get("updated_at") or datetime.utcnow()
#     if doc.get("official_social_links") is None:
#         doc["official_social_links"] = []
#     if doc.get("official_app_links") is None:
#         doc["official_app_links"] = []
#     if doc.get("brand_keywords") is None:
#         doc["brand_keywords"] = []
#     if doc.get("brand_aliases") is None:
#         doc["brand_aliases"] = []
#     return doc

# @router.post("", response_model=BrandResponse)
# async def create_brand(brand_in: BrandCreate):
#     db = get_db()
#     existing = await db.brands.find_one({"name": brand_in.name})
#     if existing:
#         raise HTTPException(status_code=400, detail="Brand with this name already exists")
    
#     brand_dict = brand_in.model_dump()
#     brand_dict["is_archived"] = False
#     brand_dict["created_at"] = datetime.utcnow()
#     brand_dict["updated_at"] = datetime.utcnow()

#     res = await db.brands.insert_one(brand_dict)
#     brand_dict["id"] = str(res.inserted_id)
#     return brand_dict

# @router.get("", response_model=List[BrandResponse])
# async def list_brands(include_archived: bool = Query(False)):
#     db = get_db()
#     query = {} if include_archived else {"is_archived": {"$ne": True}}
#     cursor = db.brands.find(query).sort("created_at", -1)
#     brands = await cursor.to_list(length=100)

#     result = []
#     for b in brands:
#         b_id = str(b["_id"])
#         # Counts
#         off_count = await db.official_assets.count_documents({"brand_id": b_id})
#         threat_count = await db.threats.count_documents({"brand_id": b_id, "is_official_safe": {"$ne": True}, "status": {"$ne": "RESOLVED"}})
        
#         item = serialize_doc(b)
#         item["official_assets_count"] = off_count
#         item["active_threats_count"] = threat_count
#         result.append(item)
#     return result

# @router.get("/{id}", response_model=BrandResponse)
# async def get_brand(id: str):
#     db = get_db()
#     if not ObjectId.is_valid(id):
#         raise HTTPException(status_code=400, detail="Invalid brand ID format")
    
#     brand = await db.brands.find_one({"_id": ObjectId(id)})
#     if not brand:
#         raise HTTPException(status_code=404, detail="Brand not found")
    
#     b_id = str(brand["_id"])
#     off_count = await db.official_assets.count_documents({"brand_id": b_id})
#     threat_count = await db.threats.count_documents({"brand_id": b_id, "is_official_safe": {"$ne": True}, "status": {"$ne": "RESOLVED"}})
    
#     item = serialize_doc(brand)
#     item["official_assets_count"] = off_count
#     item["active_threats_count"] = threat_count
#     return item

# @router.put("/{id}", response_model=BrandResponse)
# async def update_brand(id: str, brand_in: BrandUpdate):
#     db = get_db()
#     if not ObjectId.is_valid(id):
#         raise HTTPException(status_code=400, detail="Invalid brand ID")
    
#     update_data = {k: v for k, v in brand_in.model_dump().items() if v is not None}
#     if not update_data:
#         raise HTTPException(status_code=400, detail="No fields provided for update")
    
#     if "name" in update_data:
#         existing = await db.brands.find_one({"name": update_data["name"], "_id": {"$ne": ObjectId(id)}})
#         if existing:
#             raise HTTPException(status_code=400, detail="Brand with this name already exists")
    
#     update_data["updated_at"] = datetime.utcnow()
#     res = await db.brands.find_one_and_update(
#         {"_id": ObjectId(id)},
#         {"$set": update_data},
#         return_document=True
#     )
#     if not res:
#         raise HTTPException(status_code=404, detail="Brand not found")
#     item = serialize_doc(res)
#     item["official_assets_count"] = await db.official_assets.count_documents({"brand_id": id})
#     item["active_threats_count"] = await db.threats.count_documents({"brand_id": id, "is_official_safe": {"$ne": True}, "status": {"$ne": "RESOLVED"}})
#     return item

# @router.delete("/{id}")
# async def delete_brand(id: str, cascade: bool = Query(True)):
#     db = get_db()
#     if not ObjectId.is_valid(id):
#         raise HTTPException(status_code=400, detail="Invalid brand ID")
    
#     brand = await db.brands.find_one({"_id": ObjectId(id)})
#     if not brand:
#         raise HTTPException(status_code=404, detail="Brand not found")
        
#     off_count = await db.official_assets.count_documents({"brand_id": id})
#     threat_count = await db.threats.count_documents({"brand_id": id})
    
#     if not cascade and (off_count > 0 or threat_count > 0):
#         raise HTTPException(
#             status_code=400,
#             detail=f"Brand has {off_count} official assets and {threat_count} threat records. Enable cascade to delete all dependencies."
#         )
        
#     # Permanently delete brand and cascade delete dependent assets, threats, alerts, campaigns
#     await db.brands.delete_one({"_id": ObjectId(id)})
#     await db.official_assets.delete_many({"brand_id": id})
#     await db.threats.delete_many({"brand_id": id})
#     await db.alerts.delete_many({"brand_id": id})
#     await db.campaigns.delete_many({"brand_id": id})
    
#     return {
#         "status": "success",
#         "message": f"Brand '{brand.get('name')}' and all associated records ({off_count} assets, {threat_count} threats) permanently deleted",
#         "deleted_id": id
#     }

# # --- OFFICIAL ASSETS SUB-ROUTES ---

# @router.post("/{id}/official-assets", response_model=OfficialAssetResponse)
# async def add_official_asset(id: str, asset_in: OfficialAssetCreate):
#     db = get_db()
#     if not ObjectId.is_valid(id):
#         raise HTTPException(status_code=400, detail="Invalid brand ID")
    
#     brand = await db.brands.find_one({"_id": ObjectId(id)})
#     if not brand:
#         raise HTTPException(status_code=404, detail="Brand not found")
    
#     asset_dict = asset_in.model_dump()
#     asset_dict["brand_id"] = id
#     asset_dict["created_at"] = datetime.utcnow()

#     res = await db.official_assets.insert_one(asset_dict)
#     asset_dict["id"] = str(res.inserted_id)
#     return asset_dict

# @router.get("/{id}/official-assets", response_model=List[OfficialAssetResponse])
# async def list_official_assets(id: str):
#     db = get_db()
#     cursor = db.official_assets.find({"brand_id": id}).sort("created_at", -1)
#     assets = await cursor.to_list(length=100)
#     return [serialize_doc(a) for a in assets]

# @router.put("/{id}/official-assets/{asset_id}", response_model=OfficialAssetResponse)
# async def update_official_asset(id: str, asset_id: str, asset_in: OfficialAssetUpdate):
#     db = get_db()
#     if not ObjectId.is_valid(id) or not ObjectId.is_valid(asset_id):
#         raise HTTPException(status_code=400, detail="Invalid ID format")
        
#     update_data = {k: v for k, v in asset_in.model_dump().items() if v is not None}
#     if not update_data:
#         raise HTTPException(status_code=400, detail="No fields provided for update")
        
#     update_data["updated_at"] = datetime.utcnow()
#     res = await db.official_assets.find_one_and_update(
#         {"_id": ObjectId(asset_id), "brand_id": id},
#         {"$set": update_data},
#         return_document=True
#     )
#     if not res:
#         raise HTTPException(status_code=404, detail="Official asset not found")
#     return serialize_doc(res)

# @router.delete("/{id}/official-assets/{asset_id}")
# async def delete_official_asset(id: str, asset_id: str):
#     db = get_db()
#     if not ObjectId.is_valid(asset_id):
#         raise HTTPException(status_code=400, detail="Invalid asset ID")
    
#     res = await db.official_assets.delete_one({"_id": ObjectId(asset_id), "brand_id": id})
#     if res.deleted_count == 0:
#         raise HTTPException(status_code=404, detail="Official asset not found")
#     return {"status": "success", "message": "Official asset deleted"}

# # --- LOGO UPLOAD & MULTI-STEP WIZARD SYNC ---

# @router.post("/upload-logo")
# async def upload_brand_logo(file: UploadFile = File(...)):
#     """Uploads and saves a brand logo persistently to static storage."""
#     allowed_exts = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"}
#     ext = os.path.splitext(file.filename or "")[1].lower()
#     if ext not in allowed_exts:
#         raise HTTPException(status_code=400, detail="Invalid file type. Only PNG, JPG, JPEG, WEBP, and SVG are supported.")
    
#     contents = await file.read()
#     if len(contents) > 5 * 1024 * 1024:
#         raise HTTPException(status_code=400, detail="File too large. Maximum logo size is 5MB.")
    
#     safe_name = f"{uuid.uuid4().hex[:12]}{ext}"
#     static_logos_dir = Path(__file__).resolve().parent.parent / "static" / "logos"
#     static_logos_dir.mkdir(parents=True, exist_ok=True)
#     target_path = static_logos_dir / safe_name
    
#     with open(target_path, "wb") as f:
#         f.write(contents)
        
#     logo_url = f"/static/logos/{safe_name}"
#     return {
#         "status": "success",
#         "logo_url": logo_url,
#         "relative_url": logo_url,
#         "filename": safe_name
#     }

# @router.put("/{id}/wizard")
# async def sync_brand_wizard(id: str, wizard_in: BrandWizardSyncRequest):
#     """
#     Complete multi-step wizard synchronization:
#     1. Updates Brand info, website, category, description, keywords, aliases.
#     2. Updates logo_url persistently.
#     3. Synchronizes official social accounts, mobile apps, and domains (creates new, updates modified, deletes removed).
#     4. Updates brand ground-truth metadata (official_social_links, official_app_links, official_instagram_username).
#     """
#     db = get_db()
#     if not ObjectId.is_valid(id):
#         raise HTTPException(status_code=400, detail="Invalid brand ID format")
        
#     brand = await db.brands.find_one({"_id": ObjectId(id)})
#     if not brand:
#         raise HTTPException(status_code=404, detail="Brand not found")
        
#     cleaned_name = wizard_in.name.strip()
#     if not cleaned_name:
#         raise HTTPException(status_code=400, detail="Brand name cannot be empty")
        
#     existing_name = await db.brands.find_one({"name": cleaned_name, "_id": {"$ne": ObjectId(id)}})
#     if existing_name:
#         raise HTTPException(status_code=400, detail=f"Another brand named '{cleaned_name}' already exists.")

#     # Extract Instagram ground truth if present
#     ig_account = next(
#         (s for s in wizard_in.social_accounts if (s.platform or '').lower() == 'instagram'),
#         None
#     )
#     ig_user = None
#     ig_url = None
#     if ig_account:
#         ig_url = ig_account.url.strip() if ig_account.url else None
#         ig_user = (ig_account.identifier or '').strip().lstrip('@')
#         if not ig_user and ig_url:
#             match = re.search(r"instagram\.com/([^/?#]+)", ig_url, re.IGNORECASE)
#             if match:
#                 ig_user = match.group(1)

#     # 1. Update Brand ground truth document
#     brand_update_doc = {
#         "name": cleaned_name,
#         "website": wizard_in.website.strip() if wizard_in.website else None,
#         "industry": wizard_in.industry or "Other",
#         "description": wizard_in.description.strip() if wizard_in.description else None,
#         "logo_url": wizard_in.logo_url.strip() if wizard_in.logo_url else None,
#         "brand_keywords": [k.strip() for k in wizard_in.brand_keywords if k.strip()],
#         "brand_aliases": [a.strip() for a in wizard_in.brand_aliases if a.strip()],
#         "official_instagram_username": ig_user,
#         "official_instagram_url": ig_url,
#         "official_bio": wizard_in.description.strip() if wizard_in.description else None,
#         "official_instagram_logo": wizard_in.logo_url.strip() if wizard_in.logo_url else None,
#         "official_social_links": [s.url.strip() for s in wizard_in.social_accounts if s.url and s.url.strip()],
#         "official_app_links": [a.url.strip() for a in wizard_in.mobile_apps if a.url and a.url.strip()],
#         "updated_at": datetime.utcnow()
#     }
    
#     await db.brands.update_one({"_id": ObjectId(id)}, {"$set": brand_update_doc})
    
#     # 2. Synchronize Official Assets
#     existing_assets = await db.official_assets.find({"brand_id": id}).to_list(length=500)
#     existing_map = {str(a["_id"]): a for a in existing_assets}
    
#     retained_ids = set()
    
#     all_incoming = []
#     for item in wizard_in.social_accounts:
#         if item.url and item.url.strip():
#             d = item.model_dump()
#             d["asset_type"] = "social"
#             d["name"] = d.get("name") or f"{cleaned_name} {d.get('platform') or 'Social'}"
#             all_incoming.append(d)
            
#     for item in wizard_in.mobile_apps:
#         if item.url and item.url.strip():
#             d = item.model_dump()
#             d["asset_type"] = "app"
#             d["name"] = d.get("name") or f"{cleaned_name} App"
#             all_incoming.append(d)
            
#     for item in wizard_in.domains:
#         if item.url and item.url.strip():
#             d = item.model_dump()
#             d["asset_type"] = "domain"
#             d["platform"] = "Domain"
#             d["name"] = d.get("name") or "Official Domain"
#             all_incoming.append(d)
            
#     now = datetime.utcnow()
    
#     for asset_dict in all_incoming:
#         asset_id = asset_dict.get("id")
#         doc = {
#             "brand_id": id,
#             "name": asset_dict.get("name") or f"{cleaned_name} Asset",
#             "asset_type": asset_dict["asset_type"],
#             "platform": asset_dict.get("platform") or "Web",
#             "url": asset_dict["url"].strip(),
#             "identifier": asset_dict.get("identifier"),
#             "developer_name": asset_dict.get("developer_name"),
#             "package_id": asset_dict.get("package_id"),
#             "verification_status": asset_dict.get("verification_status") or "VERIFIED",
#             "is_active": asset_dict.get("is_active", True),
#             "updated_at": now
#         }
        
#         if asset_id and ObjectId.is_valid(asset_id) and asset_id in existing_map:
#             await db.official_assets.update_one({"_id": ObjectId(asset_id)}, {"$set": doc})
#             retained_ids.add(asset_id)
#         else:
#             doc["created_at"] = now
#             ins = await db.official_assets.insert_one(doc)
#             retained_ids.add(str(ins.inserted_id))
            
#     # Delete assets that were removed in the wizard
#     to_delete = [ObjectId(aid) for aid in existing_map.keys() if aid not in retained_ids]
#     if to_delete:
#         await db.official_assets.delete_many({"_id": {"$in": to_delete}})
        
#     # Return fresh brand and assets
#     fresh_brand = await db.brands.find_one({"_id": ObjectId(id)})
#     fresh_assets = await db.official_assets.find({"brand_id": id}).sort("created_at", -1).to_list(length=500)
    
#     serialized_brand = serialize_doc(fresh_brand)
#     serialized_brand["official_assets_count"] = len(fresh_assets)
#     serialized_brand["active_threats_count"] = await db.threats.count_documents({
#         "brand_id": id,
#         "is_official_safe": {"$ne": True},
#         "status": {"$ne": "RESOLVED"}
#     })
    
#     return {
#         "status": "success",
#         "message": f"Brand profile '{cleaned_name}' and {len(fresh_assets)} official assets successfully updated.",
#         "brand": serialized_brand,
#         "official_assets": [serialize_doc(a) for a in fresh_assets]
#     }
   

import os
import re
import uuid
import logging
import io
from pathlib import Path
from datetime import datetime
from typing import List

from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    Query,
    UploadFile,
    File,
)
from bson import ObjectId
from PIL import Image, UnidentifiedImageError

from app.database import get_db
from app.routes.access_control import (
    brand_child_filter,
    readable_brand_filter as access_readable_brand_filter,
    shared_demo_brand_filter,
)
from app.services.auth_service import require_current_user
from app.models.schemas import (
    BrandCreate,
    BrandUpdate,
    BrandResponse,
    OfficialAssetCreate,
    OfficialAssetUpdate,
    OfficialAssetResponse,
    BrandWizardSyncRequest,
)

logger = logging.getLogger("brandshield.routes.brands")
router = APIRouter(prefix="/brands", tags=["Brands"])


# ---------------------------------------------------------
# ACCOUNT ACCESS HELPERS
# ---------------------------------------------------------

def get_user_id(user: dict) -> str:
    """Get the verified user ID from the authentication dependency."""
    user_id = user.get("id") or user.get("_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authenticated user ID not found",
        )

    return str(user_id)


def readable_brand_filter(user_id: str) -> dict:
    """
    Users can read:
    1. Their own private brands.
    2. Brands explicitly marked as shared demo data.

    Unowned legacy records are NOT automatically shared.
    """
    return access_readable_brand_filter(user_id)


async def get_readable_brand(db, brand_id: str, user_id: str) -> dict:
    """Return a brand only if the user is allowed to read it."""
    if not ObjectId.is_valid(brand_id):
        raise HTTPException(status_code=400, detail="Invalid brand ID")

    brand = await db.brands.find_one({
        "_id": ObjectId(brand_id),
        **readable_brand_filter(user_id),
    })

    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    return brand


async def get_writable_brand(db, brand_id: str, user_id: str) -> dict:
    """
    Only the owner can modify a private brand.
    Shared/demo brands are read-only.
    """
    if not ObjectId.is_valid(brand_id):
        raise HTTPException(status_code=400, detail="Invalid brand ID")

    brand = await db.brands.find_one({
        "_id": ObjectId(brand_id),
        "owner_id": user_id,
    })

    if brand:
        return brand

    shared_brand = await db.brands.find_one({
        "_id": ObjectId(brand_id),
        **shared_demo_brand_filter(),
    })

    if shared_brand:
        raise HTTPException(
            status_code=403,
            detail="Shared demo brands are read-only",
        )

    # Do not reveal whether another user's private brand exists.
    raise HTTPException(status_code=404, detail="Brand not found")


def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc

    doc["id"] = str(doc.pop("_id"))

    if not doc.get("created_at"):
        doc["created_at"] = doc.get("updated_at") or datetime.utcnow()

    for field in (
        "official_social_links",
        "official_app_links",
        "brand_keywords",
        "brand_aliases",
    ):
        if doc.get(field) is None:
            doc[field] = []

    return doc


async def add_brand_counts(db, brand: dict) -> dict:
    """Add asset and threat counts to a brand response."""
    child_filter = brand_child_filter(
        brand,
        str(brand.get("owner_id") or "shared-demo"),
    )

    brand["official_assets_count"] = await db.official_assets.count_documents(
        child_filter
    )

    brand["active_threats_count"] = await db.threats.count_documents({
        "$and": [
            child_filter,
            {
                "is_official_safe": {"$ne": True},
                "status": {"$ne": "RESOLVED"},
            },
        ]
    })

    return serialize_doc(brand)


# ---------------------------------------------------------
# CREATE AND LIST BRANDS
# ---------------------------------------------------------

@router.post("", response_model=BrandResponse)
async def create_brand(
    brand_in: BrandCreate,
    user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(user)

    brand_dict = brand_in.model_dump()
    brand_name = (brand_dict.get("name") or "").strip()

    if not brand_name:
        raise HTTPException(status_code=400, detail="Brand name is required")

    # Prevent duplicate names within this user's own brands.
    existing = await db.brands.find_one({
        "owner_id": user_id,
        "name": brand_name,
    })

    if existing:
        raise HTTPException(
            status_code=400,
            detail="You already have a brand with this name",
        )

    now = datetime.utcnow()
    brand_dict["name"] = brand_name
    brand_dict["owner_id"] = user_id
    brand_dict["is_demo"] = False
    brand_dict["is_shared"] = False
    brand_dict["is_archived"] = False
    brand_dict["created_at"] = now
    brand_dict["updated_at"] = now

    result = await db.brands.insert_one(brand_dict)
    brand_dict["_id"] = result.inserted_id

    return await add_brand_counts(db, brand_dict)


@router.get("", response_model=List[BrandResponse])
async def list_brands(
    include_archived: bool = Query(False),
    user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(user)

    query = readable_brand_filter(user_id)

    if not include_archived:
        query = {
            "$and": [
                query,
                {"is_archived": {"$ne": True}},
            ]
        }

    cursor = db.brands.find(query).sort("created_at", -1)
    brands = await cursor.to_list(length=500)

    result = []
    for brand in brands:
        result.append(await add_brand_counts(db, brand))

    return result


# ---------------------------------------------------------
# GET, UPDATE, AND DELETE BRANDS
# ---------------------------------------------------------

@router.get("/{id}", response_model=BrandResponse)
async def get_brand(
    id: str,
    user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(user)

    brand = await get_readable_brand(db, id, user_id)
    return await add_brand_counts(db, brand)


@router.put("/{id}", response_model=BrandResponse)
async def update_brand(
    id: str,
    brand_in: BrandUpdate,
    user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(user)

    brand = await get_writable_brand(db, id, user_id)

    update_data = {
        key: value
        for key, value in brand_in.model_dump().items()
        if value is not None
    }

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update",
        )

    if "name" in update_data:
        update_data["name"] = update_data["name"].strip()

        if not update_data["name"]:
            raise HTTPException(
                status_code=400,
                detail="Brand name cannot be empty",
            )

        duplicate = await db.brands.find_one({
            "owner_id": user_id,
            "name": update_data["name"],
            "_id": {"$ne": ObjectId(id)},
        })

        if duplicate:
            raise HTTPException(
                status_code=400,
                detail="You already have a brand with this name",
            )

    update_data["updated_at"] = datetime.utcnow()

    result = await db.brands.find_one_and_update(
        {
            "_id": ObjectId(id),
            "owner_id": user_id,
        },
        {"$set": update_data},
        return_document=True,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Brand not found")

    return await add_brand_counts(db, result)


@router.delete("/{id}")
async def delete_brand(
    id: str,
    cascade: bool = Query(True),
    user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(user)

    brand = await get_writable_brand(db, id, user_id)

    child_filter = brand_child_filter(brand, user_id)
    off_count = await db.official_assets.count_documents(child_filter)
    threat_count = await db.threats.count_documents(child_filter)

    if not cascade and (off_count > 0 or threat_count > 0):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Brand has {off_count} official assets and "
                f"{threat_count} threats. Enable cascade to delete dependencies."
            ),
        )

    await db.brands.delete_one({
        "_id": ObjectId(id),
        "owner_id": user_id,
    })

    await db.official_assets.delete_many(child_filter)
    await db.threats.delete_many(child_filter)
    await db.alerts.delete_many(child_filter)
    await db.campaigns.delete_many(child_filter)

    return {
        "status": "success",
        "message": (
            f"Brand '{brand.get('name')}' and its associated records "
            f"were deleted"
        ),
        "deleted_id": id,
    }


# ---------------------------------------------------------
# OFFICIAL ASSETS
# ---------------------------------------------------------

@router.post(
    "/{id}/official-assets",
    response_model=OfficialAssetResponse,
)
async def add_official_asset(
    id: str,
    asset_in: OfficialAssetCreate,
    user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(user)

    await get_writable_brand(db, id, user_id)

    asset_dict = asset_in.model_dump()
    asset_dict["brand_id"] = id
    asset_dict["owner_id"] = user_id
    asset_dict["created_at"] = datetime.utcnow()

    result = await db.official_assets.insert_one(asset_dict)
    asset_dict["id"] = str(result.inserted_id)

    return asset_dict


@router.get(
    "/{id}/official-assets",
    response_model=List[OfficialAssetResponse],
)
async def list_official_assets(
    id: str,
    user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(user)

    brand = await get_readable_brand(db, id, user_id)

    cursor = db.official_assets.find(
        brand_child_filter(brand, user_id)
    ).sort(
        "created_at", -1
    )
    assets = await cursor.to_list(length=500)

    return [serialize_doc(asset) for asset in assets]


@router.put(
    "/{id}/official-assets/{asset_id}",
    response_model=OfficialAssetResponse,
)
async def update_official_asset(
    id: str,
    asset_id: str,
    asset_in: OfficialAssetUpdate,
    user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(user)

    brand = await get_writable_brand(db, id, user_id)

    if not ObjectId.is_valid(asset_id):
        raise HTTPException(status_code=400, detail="Invalid asset ID")

    update_data = {
        key: value
        for key, value in asset_in.model_dump().items()
        if value is not None
    }

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update",
        )

    # Prevent clients from changing ownership or moving assets.
    update_data.pop("owner_id", None)
    update_data.pop("brand_id", None)
    update_data["updated_at"] = datetime.utcnow()

    result = await db.official_assets.find_one_and_update(
        {
            "_id": ObjectId(asset_id),
            "brand_id": id,
            **brand_child_filter(brand, user_id),
        },
        {"$set": update_data},
        return_document=True,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Official asset not found",
        )

    return serialize_doc(result)


@router.delete("/{id}/official-assets/{asset_id}")
async def delete_official_asset(
    id: str,
    asset_id: str,
    user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(user)

    brand = await get_writable_brand(db, id, user_id)

    if not ObjectId.is_valid(asset_id):
        raise HTTPException(status_code=400, detail="Invalid asset ID")

    result = await db.official_assets.delete_one({
        "_id": ObjectId(asset_id),
        "brand_id": id,
        **brand_child_filter(brand, user_id),
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Official asset not found",
        )

    return {"status": "success", "message": "Official asset deleted"}


# ---------------------------------------------------------
# LOGO UPLOAD
# ---------------------------------------------------------

@router.post("/upload-logo")
async def upload_brand_logo(
    file: UploadFile = File(...),
    user: dict = Depends(require_current_user),
):
    # Authentication is required to upload a logo.
    get_user_id(user)

    allowed_formats = {
        ".png": "PNG",
        ".jpg": "JPEG",
        ".jpeg": "JPEG",
        ".webp": "WEBP",
        ".gif": "GIF",
    }
    ext = os.path.splitext(file.filename or "")[1].lower()

    if ext not in allowed_formats:
        raise HTTPException(
            status_code=400,
            detail="Unsupported logo file type",
        )

    max_file_size = 5 * 1024 * 1024
    contents = await file.read(max_file_size + 1)
    if len(contents) > max_file_size:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum logo size is 5MB",
        )

    try:
        with Image.open(io.BytesIO(contents)) as image:
            if image.format != allowed_formats[ext]:
                raise HTTPException(
                    status_code=400,
                    detail="Logo content does not match its file type",
                )
            image.verify()
    except (
        Image.DecompressionBombError,
        UnidentifiedImageError,
        OSError,
        ValueError,
    ):
        raise HTTPException(
            status_code=400,
            detail="Logo must be a valid raster image",
        ) from None

    safe_name = f"{uuid.uuid4().hex[:12]}{ext}"
    logos_dir = (
        Path(__file__).resolve().parent.parent / "static" / "logos"
    )
    logos_dir.mkdir(parents=True, exist_ok=True)

    target_path = logos_dir / safe_name

    with open(target_path, "wb") as file_handle:
        file_handle.write(contents)

    logo_url = f"/static/logos/{safe_name}"

    return {
        "status": "success",
        "logo_url": logo_url,
        "relative_url": logo_url,
        "filename": safe_name,
    }


# ---------------------------------------------------------
# MULTI-STEP BRAND WIZARD
# ---------------------------------------------------------

@router.put("/{id}/wizard")
async def sync_brand_wizard(
    id: str,
    wizard_in: BrandWizardSyncRequest,
    user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(user)

    brand = await get_writable_brand(db, id, user_id)

    cleaned_name = (wizard_in.name or "").strip()

    if not cleaned_name:
        raise HTTPException(
            status_code=400,
            detail="Brand name cannot be empty",
        )

    duplicate = await db.brands.find_one({
        "owner_id": user_id,
        "name": cleaned_name,
        "_id": {"$ne": ObjectId(id)},
    })

    if duplicate:
        raise HTTPException(
            status_code=400,
            detail=f"You already have a brand named '{cleaned_name}'",
        )

    ig_account = next(
        (
            account
            for account in wizard_in.social_accounts
            if (account.platform or "").lower() == "instagram"
        ),
        None,
    )

    ig_user = None
    ig_url = None

    if ig_account:
        ig_url = ig_account.url.strip() if ig_account.url else None
        ig_user = (ig_account.identifier or "").strip().lstrip("@")

        if not ig_user and ig_url:
            match = re.search(
                r"instagram\.com/([^/?#]+)",
                ig_url,
                re.IGNORECASE,
            )
            if match:
                ig_user = match.group(1)

    now = datetime.utcnow()

    brand_update_doc = {
        "name": cleaned_name,
        "website": (
            wizard_in.website.strip() if wizard_in.website else None
        ),
        "industry": wizard_in.industry or "Other",
        "description": (
            wizard_in.description.strip()
            if wizard_in.description else None
        ),
        "logo_url": (
            wizard_in.logo_url.strip() if wizard_in.logo_url else None
        ),
        "brand_keywords": [
            value.strip()
            for value in wizard_in.brand_keywords
            if value.strip()
        ],
        "brand_aliases": [
            value.strip()
            for value in wizard_in.brand_aliases
            if value.strip()
        ],
        "official_instagram_username": ig_user,
        "official_instagram_url": ig_url,
        "official_bio": (
            wizard_in.description.strip()
            if wizard_in.description else None
        ),
        "official_instagram_logo": (
            wizard_in.logo_url.strip() if wizard_in.logo_url else None
        ),
        "official_social_links": [
            account.url.strip()
            for account in wizard_in.social_accounts
            if account.url and account.url.strip()
        ],
        "official_app_links": [
            app.url.strip()
            for app in wizard_in.mobile_apps
            if app.url and app.url.strip()
        ],
        "updated_at": now,
    }

    await db.brands.update_one(
        {
            "_id": ObjectId(id),
            "owner_id": user_id,
        },
        {"$set": brand_update_doc},
    )

    child_filter = brand_child_filter(brand, user_id)
    existing_assets = await db.official_assets.find(
        child_filter
    ).to_list(length=500)

    existing_map = {
        str(asset["_id"]): asset for asset in existing_assets
    }

    retained_ids = set()
    incoming_assets = []

    for item in wizard_in.social_accounts:
        if item.url and item.url.strip():
            data = item.model_dump()
            data["asset_type"] = "social"
            data["name"] = (
                data.get("name")
                or f"{cleaned_name} {data.get('platform') or 'Social'}"
            )
            incoming_assets.append(data)

    for item in wizard_in.mobile_apps:
        if item.url and item.url.strip():
            data = item.model_dump()
            data["asset_type"] = "app"
            data["name"] = data.get("name") or f"{cleaned_name} App"
            incoming_assets.append(data)

    for item in wizard_in.domains:
        if item.url and item.url.strip():
            data = item.model_dump()
            data["asset_type"] = "domain"
            data["platform"] = "Domain"
            data["name"] = data.get("name") or "Official Domain"
            incoming_assets.append(data)

    for asset_data in incoming_assets:
        asset_id = asset_data.get("id")

        asset_doc = {
            "brand_id": id,
            "owner_id": user_id,
            "name": asset_data.get("name") or f"{cleaned_name} Asset",
            "asset_type": asset_data["asset_type"],
            "platform": asset_data.get("platform") or "Web",
            "url": asset_data["url"].strip(),
            "identifier": asset_data.get("identifier"),
            "developer_name": asset_data.get("developer_name"),
            "package_id": asset_data.get("package_id"),
            "verification_status": (
                asset_data.get("verification_status") or "VERIFIED"
            ),
            "is_active": asset_data.get("is_active", True),
            "updated_at": now,
        }

        if (
            asset_id
            and ObjectId.is_valid(asset_id)
            and asset_id in existing_map
        ):
            await db.official_assets.update_one(
                {
                    "_id": ObjectId(asset_id),
                    **child_filter,
                },
                {"$set": asset_doc},
            )
            retained_ids.add(asset_id)
        else:
            asset_doc["created_at"] = now
            inserted = await db.official_assets.insert_one(asset_doc)
            retained_ids.add(str(inserted.inserted_id))

    assets_to_delete = [
        ObjectId(asset_id)
        for asset_id in existing_map
        if asset_id not in retained_ids
    ]

    if assets_to_delete:
        await db.official_assets.delete_many({
            "_id": {"$in": assets_to_delete},
            **child_filter,
        })

    fresh_brand = await db.brands.find_one({
        "_id": ObjectId(id),
        "owner_id": user_id,
    })

    if not fresh_brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    fresh_assets = await db.official_assets.find(
        brand_child_filter(fresh_brand, user_id)
    ).sort("created_at", -1).to_list(length=500)

    serialized_brand = await add_brand_counts(db, fresh_brand)

    return {
        "status": "success",
        "message": (
            f"Brand profile '{cleaned_name}' and "
            f"{len(fresh_assets)} official assets updated"
        ),
        "brand": serialized_brand,
        "official_assets": [
            serialize_doc(asset) for asset in fresh_assets
        ],
    }