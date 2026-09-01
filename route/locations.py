from fastapi import APIRouter, HTTPException
from config.supabase import supabase

router = APIRouter(prefix="/locations", tags=["Locations"])


@router.get("/", summary="Get all locations")
async def get_all_locations():
    """Return all available locations (districts) sorted by district name."""
    try:
        response = (
            supabase.table("locations")
            .select(
                "id, district_name, province, agro_ecological_zone, "
                "default_soil_type, avg_annual_rainfall_mm, latitude, longitude"
            )
            .order("district_name")
            .execute()
        )
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch locations: {str(e)}")
