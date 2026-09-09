"""
Courses router — Public listing of agricultural courses for the Training Hub.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from config.supabase import supabase

router = APIRouter(prefix="/courses", tags=["Courses"])


def _format_course(c: dict) -> dict:
    inst = c.get("educational_institutions") or {}
    mode_raw = c.get("mode") or "ON_SITE"
    mode_map = {
        "ON_SITE": "On-site",
        "ONLINE": "Online",
        "HYBRID": "Hybrid"
    }
    mode_display = mode_map.get(str(mode_raw).upper(), str(mode_raw))

    return {
        "id": c.get("id"),
        "title": c.get("title") or "Agricultural Training Course",
        "institution": inst.get("name") or c.get("location_city") or "Department of Agriculture",
        "institution_type": inst.get("institution_type") or "DOA",
        "nvq_level": c.get("nvq_level") or "NVQ Level 4",
        "certification_type": c.get("nvq_level") or "Certificate",
        "duration": c.get("duration") or "3 Months",
        "mode": mode_display,
        "location_city": c.get("location_city"),
        "estimated_fee_lkr": float(c.get("estimated_fee_lkr") or 0),
        "description": c.get("description") or "",
        "applicable_crops": [],
        "applicable_methods": [],
        "apply_url": c.get("application_link"),
        "inquiry_url": inst.get("website_url"),
        "is_active": True,
        "created_at": c.get("created_at"),
    }


@router.get("", summary="List all active courses (filterable)")
@router.get("/", summary="List all active courses (filterable)")
async def list_courses(
    search: Optional[str] = None,
    institution_type: Optional[str] = None,
    mode: Optional[str] = None,
    crop: Optional[str] = None,
    method: Optional[str] = None,
):
    """
    Return all active courses joined with institution data. Supports filtering by:
    - search: text search on title / institution / description
    - institution_type: DOA | NAITA | UNIVERSITY | PRIVATE
    - mode: Online | On-site | Hybrid
    - crop: crop name filter
    - method: method filter
    """
    try:
        res = (
            supabase.table("agricultural_courses")
            .select("*, educational_institutions(name, institution_type, website_url)")
            .order("created_at", desc=True)
            .execute()
        )
        data = [_format_course(c) for c in (res.data or [])]

        if institution_type:
            it_lower = institution_type.lower()
            data = [c for c in data if (c.get("institution_type") or "").lower() == it_lower]

        if mode:
            m_lower = mode.lower().replace("-", "").replace("_", "").replace(" ", "")
            data = [
                c for c in data
                if (c.get("mode") or "").lower().replace("-", "").replace("_", "").replace(" ", "") == m_lower
            ]

        if crop:
            c_lower = crop.lower()
            data = [
                c for c in data
                if c_lower in c["title"].lower() or c_lower in (c["description"] or "").lower()
            ]

        if method:
            m_lower = method.lower()
            data = [
                c for c in data
                if m_lower in c["title"].lower() or m_lower in (c["description"] or "").lower()
            ]

        if search:
            s = search.lower()
            data = [
                c for c in data
                if s in c["title"].lower()
                or s in c["institution"].lower()
                or s in (c["description"] or "").lower()
            ]

        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations", summary="Get contextual course recommendations")
@router.get("/recommendations/", summary="Get contextual course recommendations")
async def recommend_courses(
    crop_name: Optional[str] = None,
    method: Optional[str] = None,
    limit: int = 6,
):
    """
    Return courses contextually matched to the user's selected crop and/or method.
    """
    try:
        res = (
            supabase.table("agricultural_courses")
            .select("*, educational_institutions(name, institution_type, website_url)")
            .order("created_at", desc=True)
            .limit(limit * 2)
            .execute()
        )
        all_courses = [_format_course(c) for c in (res.data or [])]

        if crop_name or method:
            matched = []
            for c in all_courses:
                text = f"{c['title']} {c['description']}".lower()
                score = 0
                if crop_name and crop_name.lower() in text:
                    score += 2
                if method and method.lower() in text:
                    score += 1
                if score > 0:
                    matched.append((score, c))
            if matched:
                matched.sort(key=lambda x: x[0], reverse=True)
                return [m[1] for m in matched[:limit]]

        return all_courses[:limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{course_id}", summary="Get course detail")
async def get_course(course_id: str):
    try:
        res = (
            supabase.table("agricultural_courses")
            .select("*, educational_institutions(name, institution_type, website_url)")
            .eq("id", course_id)
            .single()
            .execute()
        )
        if not res.data:
            raise HTTPException(status_code=404, detail="Course not found")
        return _format_course(res.data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
