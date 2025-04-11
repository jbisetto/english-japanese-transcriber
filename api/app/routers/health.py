from fastapi import APIRouter, status

router = APIRouter()

@router.get("/api/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint to verify API is operational
    """
    return {"status": "ok"} 