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