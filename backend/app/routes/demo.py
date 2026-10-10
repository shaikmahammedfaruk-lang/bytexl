import logging
from fastapi import APIRouter
from app.database import get_db
from app.services.demo_service import load_demo_data

logger = logging.getLogger("brandshield.routes.demo")
router = APIRouter(prefix="/demo", tags=["Demo Environment"])

@router.post("/load")
async def trigger_load_demo():
    """
    Populates full enterprise demo dataset with ABC Bank, verified assets,
    suspicious threats, active campaign, AI investigations, and alerts.
    """
    db = get_db()
    result = await load_demo_data(db)
    return result
