from fastapi import APIRouter, HTTPException
from config.supabase import supabase

router = APIRouter(prefix="/locations", tags=["Locations"])

SRI_LANKA_DISTRICTS = {
    "badulla": {
        "district": "Badulla",
        "province": "Uva",
        "agro_ecological_zone": "UCIZ (Up Country Intermediate)",
        "default_soil_type": "Red-Yellow Podzolic",
        "avg_annual_rainfall_mm": 1800,
        "latitude": 6.9934,
        "longitude": 81.0550,
    },
    "nuwara eliya": {
        "district": "Nuwara Eliya",
        "province": "Central",
        "agro_ecological_zone": "UCWZ (Up Country Wet)",
        "default_soil_type": "Red-Yellow Podzolic & Latosolic",
        "avg_annual_rainfall_mm": 2200,
        "latitude": 6.9497,
        "longitude": 80.7891,
    },
    "kandy": {
        "district": "Kandy",
        "province": "Central",
        "agro_ecological_zone": "MCWZ (Mid Country Wet)",
        "default_soil_type": "Red-Yellow Podzolic & RBL",
        "avg_annual_rainfall_mm": 2000,
        "latitude": 7.2906,
        "longitude": 80.6337,
    },
    "matale": {
        "district": "Matale",
        "province": "Central",
        "agro_ecological_zone": "MCIZ (Mid Country Intermediate)",
        "default_soil_type": "Reddish Brown Latosolic",
        "avg_annual_rainfall_mm": 1650,
        "latitude": 7.4675,
        "longitude": 80.6234,
    },
    "anuradhapura": {
        "district": "Anuradhapura",
        "province": "North Central",
        "agro_ecological_zone": "LCDZ (Low Country Dry - DL1)",
        "default_soil_type": "Reddish Brown Earths (RBE)",
        "avg_annual_rainfall_mm": 1280,
        "latitude": 8.3114,
        "longitude": 80.4037,
    },
    "polonnaruwa": {
        "district": "Polonnaruwa",
        "province": "North Central",
        "agro_ecological_zone": "LCDZ (Low Country Dry - DL1)",
        "default_soil_type": "Reddish Brown Earths & LHG",
        "avg_annual_rainfall_mm": 1500,
        "latitude": 7.9403,
        "longitude": 81.0188,
    },
    "kurunegala": {
        "district": "Kurunegala",
        "province": "North Western",
        "agro_ecological_zone": "LCIZ (Low Country Intermediate)",
        "default_soil_type": "Red-Yellow Podzolic & RBE",
        "avg_annual_rainfall_mm": 1600,
        "latitude": 7.4818,
        "longitude": 80.3609,
    },
    "puttalam": {
        "district": "Puttalam",
        "province": "North Western",
        "agro_ecological_zone": "LCDZ (Low Country Dry - DL3)",
        "default_soil_type": "Sandy Regosols & Latosols",
        "avg_annual_rainfall_mm": 1100,
        "latitude": 8.0362,
        "longitude": 79.8283,
    },
    "jaffna": {
        "district": "Jaffna",
        "province": "Northern",
        "agro_ecological_zone": "LCDZ (Low Country Dry - DL3)",
        "default_soil_type": "Calcic Red-Yellow Latosols",
        "avg_annual_rainfall_mm": 1200,
        "latitude": 9.6615,
        "longitude": 80.0255,
    },
    "kilinochchi": {
        "district": "Kilinochchi",
        "province": "Northern",
        "agro_ecological_zone": "LCDZ (Low Country Dry - DL3)",
        "default_soil_type": "Red-Yellow Latosols & Alluvial",
        "avg_annual_rainfall_mm": 1250,
        "latitude": 9.3803,
        "longitude": 80.3770,
    },
    "mannar": {
        "district": "Mannar",
        "province": "Northern",
        "agro_ecological_zone": "LCAD (Low Country Arid - DL4)",
        "default_soil_type": "Grumusols & Sandy Regosols",
        "avg_annual_rainfall_mm": 980,
        "latitude": 8.9810,
        "longitude": 79.9044,
    },
    "vavuniya": {
        "district": "Vavuniya",
        "province": "Northern",
        "agro_ecological_zone": "LCDZ (Low Country Dry - DL1)",
        "default_soil_type": "Reddish Brown Earths",
        "avg_annual_rainfall_mm": 1400,
        "latitude": 8.7542,
        "longitude": 80.4982,
    },
    "mullaitivu": {
        "district": "Mullaitivu",
        "province": "Northern",
        "agro_ecological_zone": "LCDZ (Low Country Dry - DL1/DL3)",
        "default_soil_type": "Red-Yellow Latosols & Alluvial",
        "avg_annual_rainfall_mm": 1350,
        "latitude": 9.2671,
        "longitude": 80.8142,
    },
    "batticaloa": {
        "district": "Batticaloa",
        "province": "Eastern",
        "agro_ecological_zone": "LCDZ (Low Country Dry - DL2)",
        "default_soil_type": "Sandy Regosols & Alluvial",
        "avg_annual_rainfall_mm": 1650,
        "latitude": 7.7310,
        "longitude": 81.6747,
    },
    "ampara": {
        "district": "Ampara",
        "province": "Eastern",
        "agro_ecological_zone": "LCDZ (Low Country Dry - DL2)",
        "default_soil_type": "Reddish Brown Earths & Noncalcic Brown",
        "avg_annual_rainfall_mm": 1450,
        "latitude": 7.2912,
        "longitude": 81.6724,
    },
    "trincomalee": {
        "district": "Trincomalee",
        "province": "Eastern",
        "agro_ecological_zone": "LCDZ (Low Country Dry - DL1)",
        "default_soil_type": "Reddish Brown Earths & Sandy Regosols",
        "avg_annual_rainfall_mm": 1580,
        "latitude": 8.5874,
        "longitude": 81.2152,
    },
    "colombo": {
        "district": "Colombo",
        "province": "Western",
        "agro_ecological_zone": "LCWZ (Low Country Wet - WL1)",
        "default_soil_type": "Red-Yellow Podzolic",
        "avg_annual_rainfall_mm": 2400,
        "latitude": 6.9271,
        "longitude": 79.8612,
    },
    "gampaha": {
        "district": "Gampaha",
        "province": "Western",
        "agro_ecological_zone": "LCWZ (Low Country Wet - WL1)",
        "default_soil_type": "Red-Yellow Podzolic & Laterite",
        "avg_annual_rainfall_mm": 2300,
        "latitude": 7.0840,
        "longitude": 79.9939,
    },
    "kalutara": {
        "district": "Kalutara",
        "province": "Western",
        "agro_ecological_zone": "LCWZ (Low Country Wet - WL1/WL2)",
        "default_soil_type": "Red-Yellow Podzolic & Bog Soils",
        "avg_annual_rainfall_mm": 3000,
        "latitude": 6.5854,
        "longitude": 79.9607,
    },
    "galle": {
        "district": "Galle",
        "province": "Southern",
        "agro_ecological_zone": "LCWZ (Low Country Wet - WL1/WL2)",
        "default_soil_type": "Red-Yellow Podzolic",
        "avg_annual_rainfall_mm": 2500,
        "latitude": 6.0535,
        "longitude": 80.2210,
    },
    "matara": {
        "district": "Matara",
        "province": "Southern",
        "agro_ecological_zone": "LCWZ (Low Country Wet - WL1/IL1)",
        "default_soil_type": "Red-Yellow Podzolic & Alluvial",
        "avg_annual_rainfall_mm": 2100,
        "latitude": 5.9549,
        "longitude": 80.5550,
    },
    "hambantota": {
        "district": "Hambantota",
        "province": "Southern",
        "agro_ecological_zone": "LCDZ (Low Country Dry - DL5)",
        "default_soil_type": "Reddish Brown Earths & Solodized Solonetz",
        "avg_annual_rainfall_mm": 1050,
        "latitude": 6.1429,
        "longitude": 81.1212,
    },
    "monaragala": {
        "district": "Monaragala",
        "province": "Uva",
        "agro_ecological_zone": "LCIZ (Low Country Intermediate - IL2)",
        "default_soil_type": "Reddish Brown Earths & Immature Loams",
        "avg_annual_rainfall_mm": 1550,
        "latitude": 6.8728,
        "longitude": 81.3507,
    },
    "ratnapura": {
        "district": "Ratnapura",
        "province": "Sabaragamuwa",
        "agro_ecological_zone": "MCWZ (Mid Country Wet - WM1)",
        "default_soil_type": "Red-Yellow Podzolic",
        "avg_annual_rainfall_mm": 3500,
        "latitude": 6.7056,
        "longitude": 80.3847,
    },
    "kegalle": {
        "district": "Kegalle",
        "province": "Sabaragamuwa",
        "agro_ecological_zone": "MCWZ (Mid Country Wet - WM1)",
        "default_soil_type": "Red-Yellow Podzolic & Latosolic",
        "avg_annual_rainfall_mm": 2800,
        "latitude": 7.2513,
        "longitude": 80.3464,
    },
}


def _enrich_location(record: dict) -> dict:
    district_name = record.get("district_name") or record.get("district") or ""
    key = district_name.lower().strip()
    meta = SRI_LANKA_DISTRICTS.get(key, {})
    return {
        "id": record.get("id") or meta.get("district") or district_name.title(),
        "district_name": meta.get("district") or district_name.title(),
        "province": (
            record.get("province")
            if record.get("province") and record.get("province") not in ("Sri Lanka", "")
            else meta.get("province", "Sri Lanka")
        ),
        "agro_ecological_zone": (
            record.get("agro_ecological_zone")
            if record.get("agro_ecological_zone") and record.get("agro_ecological_zone").strip()
            else meta.get("agro_ecological_zone", "Intermediate Zone")
        ),
        "default_soil_type": (
            record.get("default_soil_type")
            if record.get("default_soil_type") and record.get("default_soil_type").strip()
            else meta.get("default_soil_type", "Red-Yellow Podzolic")
        ),
        "avg_annual_rainfall_mm": (
            record.get("avg_annual_rainfall_mm")
            if record.get("avg_annual_rainfall_mm")
            else meta.get("avg_annual_rainfall_mm", 1800)
        ),
        "latitude": record.get("latitude") or meta.get("latitude"),
        "longitude": record.get("longitude") or meta.get("longitude"),
    }


@router.get("", summary="Get all locations")
@router.get("/", summary="Get all locations")
async def get_all_locations():
    """Return all available locations (districts) sorted by district name with enriched metadata."""
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
        if response.data and len(response.data) > 0:
            return [_enrich_location(r) for r in response.data]

        # Fallback if locations table is empty: derive from district_crop_suitability or defaults
        dist_res = (
            supabase.table("district_crop_suitability")
            .select("district")
            .execute()
        )
        unique_districts = sorted(set(r["district"] for r in (dist_res.data or []) if r.get("district")))
        if not unique_districts:
            unique_districts = [meta["district"] for meta in SRI_LANKA_DISTRICTS.values()]

        return [_enrich_location({"id": d, "district_name": d}) for d in unique_districts]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch locations: {str(e)}")


@router.get("/districts", summary="Get unique districts from suitability data")
@router.get("/districts/", summary="Get unique districts from suitability data")
async def get_unique_districts():
    """
    Return a sorted list of unique districts with province.
    Used as fallback when the locations table is empty.
    """
    try:
        response = (
            supabase.table("district_crop_suitability")
            .select("district")
            .execute()
        )
        districts = sorted(set(r["district"] for r in (response.data or []) if r.get("district")))
        if not districts:
            districts = [meta["district"] for meta in SRI_LANKA_DISTRICTS.values()]
        return [
            {
                "district": d,
                "province": SRI_LANKA_DISTRICTS.get(d.lower().strip(), {}).get("province", "Sri Lanka"),
            }
            for d in districts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch districts: {str(e)}")


