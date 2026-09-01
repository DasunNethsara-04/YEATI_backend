from fastapi import APIRouter, HTTPException
from config.supabase import supabase

router = APIRouter(prefix="/crops", tags=["Crops"])


@router.get("/by-location/{location_id}", summary="Get crops suited for a location")
async def get_crops_by_location(location_id: str):
    """
    Return all crops that have a suitability record for the given location,
    including their suitability rating and core parameters.
    Results are ordered by suitability (OPTIMAL first) and then crop name.
    """
    try:
        # Fetch crop_location_suitability joined with crops for the given location
        response = (
            supabase.table("crop_location_suitability")
            .select(
                "suitability, recommendation_notes, "
                "crops(id, name_en, name_si, category, growing_cycle_duration_days, "
                "min_soil_ph, max_soil_ph, preferred_soil_type, "
                "min_temp_celsius, max_temp_celsius, water_requirement_summary, image_url)"
            )
            .eq("location_id", location_id)
            .neq("suitability", "UNSUITABLE")
            .execute()
        )

        # Flatten: merge suitability into crop object
        suitability_order = {"OPTIMAL": 0, "MODERATE": 1, "MARGINAL": 2}
        result = []
        for row in response.data:
            crop = row.get("crops")
            if crop:
                crop["suitability"] = row.get("suitability")
                crop["recommendation_notes"] = row.get("recommendation_notes")
                result.append(crop)

        result.sort(key=lambda c: (suitability_order.get(c.get("suitability", "MARGINAL"), 2), c.get("name_en", "")))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch crops: {str(e)}")
