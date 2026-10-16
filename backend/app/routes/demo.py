# import logging
# from fastapi import APIRouter
# from app.database import get_db
# from app.services.demo_service import load_demo_data

# logger = logging.getLogger("brandshield.routes.demo")
# router = APIRouter(prefix="/demo", tags=["Demo Environment"])

# @router.post("/load")
# async def trigger_load_demo():
#     """
#     Populates full enterprise demo dataset with ABC Bank, verified assets,
#     suspicious threats, active campaign, AI investigations, and alerts.
#     """
#     db = get_db()
#     result = await load_demo_data(db)
#     return result



from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/demo", tags=["Demo Environment"])


@router.post("/load")
async def trigger_load_demo():
    """
    Demo loading is temporarily disabled until the loader is made
    safe for user-owned data and shared demo records.
    """
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "Demo loading is temporarily disabled. "
            "The demo loader must be secured before it can be enabled."
        ),
    )