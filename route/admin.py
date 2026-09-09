"""
Admin router — Protected CRUD for users, crops, and courses.
All endpoints require ADMIN role (enforced via Supabase JWT claims check).
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
import jwt

from config.supabase import supabase

router = APIRouter(prefix="/admin", tags=["Admin"])

VALID_CROP_COLS = {
    "name_en", "name_si", "category", "growing_cycle_duration_days",
    "min_soil_ph", "max_soil_ph", "preferred_soil_type",
    "min_temp_celsius", "max_temp_celsius", "water_requirement_summary",
    "image_url", "growing_period", "pests_and_diseases", "suitable_climate",
}


# ── Minimal JWT role check ────────────────────────────────────────────────────
def _require_admin(authorization: str | None) -> str:
    """Extract user_id from Bearer token and verify ADMIN role in profiles."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token has no user subject")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    try:
        profile_res = supabase.table("profiles").select("role").eq("id", user_id).single().execute()
        if not profile_res.data or profile_res.data.get("role") != "ADMIN":
            raise HTTPException(status_code=403, detail="Admin access required")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify admin profile: {str(e)}")
    return user_id


# ── Schemas ───────────────────────────────────────────────────────────────────
class RoleUpdate(BaseModel):
    role: str  # USER | RESEARCHER | ADMIN

class CropCreate(BaseModel):
    name_en: str
    name_si: str
    category: str
    growing_period: Optional[str] = None
    growing_cycle_duration_days: Optional[int] = None
    min_soil_ph: Optional[float] = None
    max_soil_ph: Optional[float] = None
    preferred_soil_type: Optional[str] = None
    min_temp_celsius: Optional[float] = None
    max_temp_celsius: Optional[float] = None
    water_requirement_summary: Optional[str] = None
    pests_and_diseases: Optional[str] = None
    suitable_climate: Optional[str] = None
    image_url: Optional[str] = None

class CropUpdate(BaseModel):
    name_en: Optional[str] = None
    name_si: Optional[str] = None
    category: Optional[str] = None
    growing_period: Optional[str] = None
    growing_cycle_duration_days: Optional[int] = None
    min_soil_ph: Optional[float] = None
    max_soil_ph: Optional[float] = None
    preferred_soil_type: Optional[str] = None
    min_temp_celsius: Optional[float] = None
    max_temp_celsius: Optional[float] = None
    water_requirement_summary: Optional[str] = None
    pests_and_diseases: Optional[str] = None
    suitable_climate: Optional[str] = None
    image_url: Optional[str] = None

class CourseCreate(BaseModel):
    title: str
    institution: Optional[str] = None
    institution_type: Optional[str] = None   # DOA | NAITA | UNIVERSITY | PRIVATE | OTHER
    nvq_level: Optional[str] = None
    certification_type: Optional[str] = None
    duration: Optional[str] = None
    mode: Optional[str] = None               # Online | On-site | Hybrid
    location_city: Optional[str] = None
    estimated_fee_lkr: Optional[float] = None
    description: Optional[str] = None
    applicable_crops: Optional[list[str]] = None
    applicable_methods: Optional[list[str]] = None
    apply_url: Optional[str] = None
    inquiry_url: Optional[str] = None
    is_active: Optional[bool] = True

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    institution: Optional[str] = None
    institution_type: Optional[str] = None
    nvq_level: Optional[str] = None
    certification_type: Optional[str] = None
    duration: Optional[str] = None
    mode: Optional[str] = None
    location_city: Optional[str] = None
    estimated_fee_lkr: Optional[float] = None
    description: Optional[str] = None
    applicable_crops: Optional[list[str]] = None
    applicable_methods: Optional[list[str]] = None
    apply_url: Optional[str] = None
    inquiry_url: Optional[str] = None
    is_active: Optional[bool] = None


# ════════════════════════════════════════════════════════════════════════════════
# STATS
# ════════════════════════════════════════════════════════════════════════════════

@router.get("/stats", summary="Platform statistics")
@router.get("/stats/", summary="Platform statistics")
async def admin_stats(authorization: Optional[str] = Header(None)):
    _require_admin(authorization)
    try:
        users_res = supabase.table("profiles").select("id", count="exact").execute()
        crops_res = supabase.table("crops").select("id", count="exact").execute()
        courses_res = supabase.table("agricultural_courses").select("id", count="exact").execute()
        return {
            "total_users": users_res.count if users_res.count is not None else len(users_res.data or []),
            "total_crops": crops_res.count if crops_res.count is not None else len(crops_res.data or []),
            "total_courses": courses_res.count if courses_res.count is not None else len(courses_res.data or []),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════════════════════════
# USERS
# ════════════════════════════════════════════════════════════════════════════════

@router.get("/users", summary="List all users (paginated)")
@router.get("/users/", summary="List all users (paginated)")
async def list_users(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    authorization: Optional[str] = Header(None),
):
    _require_admin(authorization)
    try:
        q = supabase.table("profiles").select(
            "id, email, full_name, role, phone_number, created_at, avatar_url"
        ).order("created_at", desc=True)

        if search:
            q = q.or_(f"full_name.ilike.%{search}%,email.ilike.%{search}%")

        offset = (page - 1) * page_size
        q = q.range(offset, offset + page_size - 1)
        res = q.execute()
        return {"data": res.data or [], "page": page, "page_size": page_size}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/users/{user_id}/role", summary="Change a user's role")
async def update_user_role(
    user_id: str,
    body: RoleUpdate,
    authorization: Optional[str] = Header(None),
):
    _require_admin(authorization)
    valid_roles = {"USER", "RESEARCHER", "ADMIN"}
    if body.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of {valid_roles}")
    try:
        res = supabase.table("profiles").update({"role": body.role}).eq("id", user_id).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}", summary="Delete a user profile")
async def delete_user(user_id: str, authorization: Optional[str] = Header(None)):
    _require_admin(authorization)
    try:
        supabase.table("profiles").delete().eq("id", user_id).execute()
        return {"message": "User deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════════════════════════
# CROPS
# ════════════════════════════════════════════════════════════════════════════════

@router.get("/crops", summary="List all crops (admin)")
@router.get("/crops/", summary="List all crops (admin)")
async def admin_list_crops(authorization: Optional[str] = Header(None)):
    _require_admin(authorization)
    try:
        res = supabase.table("crops").select("*").order("name_en").execute()
        return res.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crops", summary="Create a new crop")
@router.post("/crops/", summary="Create a new crop")
async def admin_create_crop(body: CropCreate, authorization: Optional[str] = Header(None)):
    _require_admin(authorization)
    try:
        payload = {k: v for k, v in body.model_dump(exclude_none=True).items() if k in VALID_CROP_COLS}
        res = supabase.table("crops").insert(payload).execute()
        return res.data[0] if res.data else {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/crops/{crop_id}", summary="Update a crop")
async def admin_update_crop(crop_id: str, body: CropUpdate, authorization: Optional[str] = Header(None)):
    _require_admin(authorization)
    payload = {k: v for k, v in body.model_dump(exclude_none=True).items() if k in VALID_CROP_COLS}
    if not payload:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        res = supabase.table("crops").update(payload).eq("id", crop_id).execute()
        return res.data[0] if res.data else {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/crops/{crop_id}", summary="Delete a crop")
async def admin_delete_crop(crop_id: str, authorization: Optional[str] = Header(None)):
    _require_admin(authorization)
    try:
        supabase.table("crops").delete().eq("id", crop_id).execute()
        return {"message": "Crop deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════════════════════════
# COURSES
# ════════════════════════════════════════════════════════════════════════════════

@router.get("/courses", summary="List all courses (admin)")
@router.get("/courses/", summary="List all courses (admin)")
async def admin_list_courses(authorization: Optional[str] = Header(None)):
    _require_admin(authorization)
    try:
        res = (
            supabase.table("agricultural_courses")
            .select("*, educational_institutions(name, institution_type, website_url)")
            .order("created_at", desc=True)
            .execute()
        )
        courses = []
        for c in (res.data or []):
            inst = c.get("educational_institutions") or {}
            courses.append({
                "id": c.get("id"),
                "title": c.get("title"),
                "institution": inst.get("name") or c.get("location_city") or "Department of Agriculture",
                "institution_type": inst.get("institution_type") or "DOA",
                "nvq_level": c.get("nvq_level"),
                "certification_type": c.get("nvq_level") or "Certificate",
                "duration": c.get("duration"),
                "mode": c.get("mode"),
                "location_city": c.get("location_city"),
                "estimated_fee_lkr": c.get("estimated_fee_lkr") or 0.0,
                "description": c.get("description"),
                "apply_url": c.get("application_link"),
                "inquiry_url": inst.get("website_url"),
                "is_active": True,
                "created_at": c.get("created_at"),
            })
        return courses
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/courses", summary="Create a new course")
@router.post("/courses/", summary="Create a new course")
async def admin_create_course(body: CourseCreate, authorization: Optional[str] = Header(None)):
    _require_admin(authorization)
    try:
        inst_name = (body.institution or "Department of Agriculture").strip()
        inst_type = (body.institution_type or "DOA").upper()
        if inst_type not in {"DOA", "NAITA", "UNIVERSITY", "PRIVATE", "OTHER"}:
            inst_type = "DOA"

        # Find or create educational_institutions record
        inst_res = supabase.table("educational_institutions").select("id").eq("name", inst_name).execute()
        if inst_res.data and len(inst_res.data) > 0:
            institution_id = inst_res.data[0]["id"]
        else:
            new_inst = supabase.table("educational_institutions").insert({
                "name": inst_name,
                "institution_type": inst_type,
                "website_url": body.inquiry_url,
            }).execute()
            institution_id = new_inst.data[0]["id"]

        raw_mode = (body.mode or "ON_SITE").upper().replace("-", "_").replace(" ", "_")
        if "ONLINE" in raw_mode:
            mode_val = "ONLINE"
        elif "HYBRID" in raw_mode:
            mode_val = "HYBRID"
        else:
            mode_val = "ON_SITE"

        payload = {
            "institution_id": institution_id,
            "title": body.title,
            "nvq_level": body.nvq_level or "NVQ 4",
            "duration": body.duration or "3 Months",
            "mode": mode_val,
            "location_city": body.location_city or inst_name,
            "estimated_fee_lkr": float(body.estimated_fee_lkr or 0.0),
            "application_link": body.apply_url,
            "description": body.description or "",
        }
        res = supabase.table("agricultural_courses").insert(payload).execute()
        return res.data[0] if res.data else {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/courses/{course_id}", summary="Update a course")
async def admin_update_course(course_id: str, body: CourseUpdate, authorization: Optional[str] = Header(None)):
    _require_admin(authorization)
    try:
        payload = {}
        if body.title is not None:
            payload["title"] = body.title
        if body.nvq_level is not None:
            payload["nvq_level"] = body.nvq_level
        if body.duration is not None:
            payload["duration"] = body.duration
        if body.mode is not None:
            raw_mode = body.mode.upper().replace("-", "_").replace(" ", "_")
            payload["mode"] = "ONLINE" if "ONLINE" in raw_mode else ("HYBRID" if "HYBRID" in raw_mode else "ON_SITE")
        if body.location_city is not None:
            payload["location_city"] = body.location_city
        if body.estimated_fee_lkr is not None:
            payload["estimated_fee_lkr"] = float(body.estimated_fee_lkr)
        if body.apply_url is not None:
            payload["application_link"] = body.apply_url
        if body.description is not None:
            payload["description"] = body.description

        if not payload:
            raise HTTPException(status_code=400, detail="No fields to update")

        res = supabase.table("agricultural_courses").update(payload).eq("id", course_id).execute()
        return res.data[0] if res.data else {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/courses/{course_id}", summary="Delete a course")
async def admin_delete_course(course_id: str, authorization: Optional[str] = Header(None)):
    _require_admin(authorization)
    try:
        supabase.table("agricultural_courses").delete().eq("id", course_id).execute()
        return {"message": "Course deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
