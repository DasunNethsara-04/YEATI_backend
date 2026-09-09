from fastapi import APIRouter, HTTPException
from config.supabase import supabase

router = APIRouter(prefix="/crops", tags=["Crops"])


@router.get("", summary="Get all crops")
@router.get("/", summary="Get all crops")
async def get_all_crops():
    """Return all available crops ordered by English name."""
    try:
        response = supabase.table("crops").select("*").order("name_en").execute()
        return response.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch crops: {str(e)}")



@router.get("/by-location/{location_id}", summary="Get crops suited for a location")
async def get_crops_by_location(location_id: str):
    """
    Return all crops that have a suitability record for the given location,
    including their suitability rating and core parameters.
    Results are ordered by suitability (OPTIMAL first) and then crop name.
    """
    try:
        response = (
            supabase.table("crop_location_suitability")
            .select(
                "suitability, recommendation_notes, "
                "crops(*)"
            )
            .eq("location_id", location_id)
            .neq("suitability", "UNSUITABLE")
            .execute()
        )

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


@router.get("/by-district/{district_name}", summary="Get crops suited for a district (by name)")
async def get_crops_by_district(district_name: str):
    """
    Return crops suitable for a district using the district_crop_suitability table
    (works even when the locations table is empty).
    """
    try:
        response = (
            supabase.table("district_crop_suitability")
            .select("crop_name, cultivation_method, suitability_level, reason_notes, is_mvp_recommended")
            .eq("district", district_name)
            .neq("suitability_level", "Low")
            .execute()
        )

        # Group by crop_name and enrich with crops table data
        crop_names = list({r["crop_name"] for r in response.data})
        if not crop_names:
            return []

        crops_res = (
            supabase.table("crops")
            .select("*")
            .in_("name_en", crop_names)
            .execute()
        )

        crop_map = {c["name_en"]: c for c in crops_res.data}

        # Merge suitability data
        seen = {}
        for row in response.data:
            name = row["crop_name"]
            if name not in seen and name in crop_map:
                crop = dict(crop_map[name])
                crop["suitability_level"] = row["suitability_level"]
                crop["cultivation_method"] = row["cultivation_method"]
                crop["reason_notes"] = row["reason_notes"]
                crop["is_mvp_recommended"] = row["is_mvp_recommended"]
                seen[name] = crop

        results = list(seen.values())
        results.sort(key=lambda c: (0 if c.get("is_mvp_recommended") else 1, c.get("name_en", "")))
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch crops: {str(e)}")


@router.get("/{crop_id}", summary="Get full crop detail")
async def get_crop_detail(crop_id: str):
    """Return complete crop profile including all agronomic parameters."""
    try:
        res = supabase.table("crops").select("*").eq("id", crop_id).single().execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Crop not found")
        return res.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{crop_id}/methods", summary="Get cultivation method benchmarks for a crop")
async def get_crop_methods(crop_id: str):
    """
    Return all available cultivation method benchmarks for a crop,
    including cost breakdowns, yield estimates, and resource intensity.
    """
    try:
        res = (
            supabase.table("cultivation_method_benchmarks")
            .select("*")
            .eq("crop_id", crop_id)
            .execute()
        )
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
