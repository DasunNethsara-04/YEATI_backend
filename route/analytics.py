"""
Analytics router — Financial calculations + ML-powered predictions.

Climate model features: [week_num, month, sin_week, cos_week]
  → outputs: [Total Rainfall (mm), Avg Temp (°C), Avg Min Temp (°C), Avg Max Temp (°C)]

Price model features: [crop (OHE), week_num, month, sin_week, cos_week, rainfall, avg_temp, min_temp, max_temp]
  → outputs: price (Rs./kg)
  Supported crops: Tomato, Green Chilli, Cucumber, Brinjal, Capsicum
"""
import math
from datetime import datetime, date, timedelta
from typing import Optional

import joblib
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config.supabase import supabase

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# ── Load ML models at startup ─────────────────────────────────────────────────
# Compatibility shim for scikit-learn >= 1.9 loading models pickled in 1.6.1
import sklearn.compose._column_transformer as _ct
if not hasattr(_ct, "_RemainderColsList"):
    class _RemainderColsList(list):
        pass
    _ct._RemainderColsList = _RemainderColsList

try:
    _climate_model = joblib.load("ml/climate_model.joblib")
except Exception as e:
    _climate_model = None
    print(f"[WARNING] Could not load climate model: {e}")

try:
    _price_model = joblib.load("ml/crop_price_model.joblib")
except Exception as e:
    _price_model = None
    print(f"[WARNING] Could not load price model: {e}")

# Crop name normalization — maps DB names → model names (OHE trained names)
CROP_NAME_TO_MODEL: dict[str, str] = {
    "tomato": "Tomato",
    "chilli": "Green Chilli",
    "green chilli": "Green Chilli",
    "cucumber": "Cucumber",
    "brinjal": "Brinjal",
    "capsicum": "Capsicum",
    "carrot": None,  # Handled via DEFAULT_CROP_BASELINES
}

# Market baseline prices (Rs./kg) for crops not in the ML model
DEFAULT_CROP_BASELINES: dict[str, float] = {
    "carrot": 285.0,
}

# ── Sri Lanka Market Benchmark Price Bounds (LKR/kg) ─────────────────────────
# Source: Hector Kobbekaduwa Agrarian Research and Training Institute (HARTI) & DOA Sri Lanka
CROP_PRICE_BOUNDS: dict[str, tuple[float, float]] = {
    "tomato":       (100.0, 700.0),   # Typical range: Rs. 100 - 700 / kg
    "green chilli": (250.0, 1600.0),  # Typical range: Rs. 250 - 1600 / kg
    "chilli":       (250.0, 1600.0),
    "cucumber":     (60.0,  350.0),   # Typical range: Rs. 60 - 350 / kg
    "brinjal":      (100.0, 650.0),   # Typical range: Rs. 100 - 650 / kg
    "capsicum":     (200.0, 1400.0),  # Typical range: Rs. 200 - 1400 / kg
    "carrot":       (120.0, 650.0),   # Typical range: Rs. 120 - 650 / kg
}

# ── Land Measurement Unit Conversion (Sri Lanka Standard) ─────────────────────
# 1 Acre = 4 Roods = 160 Perches = 4,046.86 m²
# 1 Rood = 40 Perches = 1,011.71 m² = 1/4 Acre
# 1 Perch = 25.2929 m² = 1/40 Rood = 1/160 Acre
# 1 m² = 0.000247 Acres = 0.0395 Perches
ROOD_TO_ACRES = 1 / 4
PERCH_TO_ACRES = 1 / 160
SQ_M_TO_ACRES = 1 / 4046.86
SQ_FT_TO_ACRES = 1 / 43560


# ── Utility: week features ────────────────────────────────────────────────────
def _week_features(dt: date) -> dict:
    week_num = dt.isocalendar()[1]
    month = dt.month
    return {
        "week_num": week_num,
        "month": month,
        "sin_week": math.sin(2 * math.pi * week_num / 52),
        "cos_week": math.cos(2 * math.pi * week_num / 52),
    }


# ── Utility: area → acres ─────────────────────────────────────────────────────
def _to_acres(value: float, unit: str) -> float:
    unit = unit.lower().strip()
    if unit in ("acres", "acre", "ac"):
        return value
    if unit in ("roods", "rood"):
        return value * ROOD_TO_ACRES
    if unit in ("perches", "perch"):
        return value * PERCH_TO_ACRES
    if unit in ("sq_m", "sqm", "sq m", "sq_meters", "m²", "m2"):
        return value * SQ_M_TO_ACRES
    if unit in ("sq_ft", "sqft", "sq ft"):
        return value * SQ_FT_TO_ACRES
    raise ValueError(f"Unknown area unit: {unit}")


# ── Schemas ───────────────────────────────────────────────────────────────────
class CalculateRequest(BaseModel):
    crop_id: str
    method_type: str          # OPEN_FIELD | HYDROPONICS | ORGANIC
    area_value: float
    area_unit: str            # acres | perches | sq_ft | sq_m
    capital_lkr: float
    target_date: Optional[str] = None  # ISO date string; defaults to today


class ClimateResponse(BaseModel):
    week_num: int
    month: int
    predicted_rainfall_mm: float
    predicted_avg_temp_c: float
    predicted_min_temp_c: float
    predicted_max_temp_c: float


class PriceResponse(BaseModel):
    crop_name: str
    model_crop_name: str
    predicted_price_rs_per_kg: float
    week_num: int
    month: int


# ── POST /analytics/calculate ─────────────────────────────────────────────────
@router.post("/calculate", summary="Calculate financial analytics for a crop plan")
async def calculate_analytics(req: CalculateRequest):
    """
    Combine benchmark data + ML predictions to produce a full financial plan.
    Returns OpEx breakdown, yield estimate, revenue, ROI, and ML price/climate.
    """
    # 1. Fetch crop
    crop_res = supabase.table("crops").select("*").eq("id", req.crop_id).single().execute()
    if not crop_res.data:
        raise HTTPException(status_code=404, detail="Crop not found")
    crop = crop_res.data

    # 2. Fetch method benchmark
    bench_res = (
        supabase.table("cultivation_method_benchmarks")
        .select("*")
        .eq("crop_id", req.crop_id)
        .eq("method_type", req.method_type)
        .execute()
    )
    if not bench_res.data:
        raise HTTPException(status_code=404, detail=f"No benchmark found for method {req.method_type}")
    bench = bench_res.data[0]

    # 3. Convert area to acres
    try:
        area_acres = _to_acres(req.area_value, req.area_unit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 4. OpEx calculation
    total_cost_per_acre: float = bench["total_cost_rs_per_acre"]
    total_opex = total_cost_per_acre * area_acres

    seed_cost = total_opex * (bench["seed_share_pct"] / 100)
    labour_cost = total_opex * (bench["labour_share_pct"] / 100)
    fertilizer_cost = total_opex * (bench["fertilizer_share_pct"] / 100)
    other_cost = total_opex * (bench["other_share_pct"] / 100)

    # 5. Yield estimate
    avg_yield_per_acre: float = bench["avg_yield_kg_per_acre"]
    estimated_yield_kg = avg_yield_per_acre * area_acres

    # 6. ML: climate + price predictions for harvest date (after harvesting period)
    # Formula Reference: Predicted Market Price after Harvesting Period (Rs/kg)
    growing_days = int(crop.get("growing_cycle_duration_days") or 90)
    plant_date = date.fromisoformat(req.target_date) if req.target_date else date.today()
    harvest_date = plant_date + timedelta(days=growing_days)
    wf = _week_features(harvest_date)

    climate_prediction = None
    price_prediction = None
    predicted_price_per_kg = 0.0

    if _climate_model:
        X_clim = np.array([[wf["week_num"], wf["month"], wf["sin_week"], wf["cos_week"]]])
        clim_pred = _climate_model.predict(X_clim)[0]
        climate_prediction = {
            "week_num": wf["week_num"],
            "month": wf["month"],
            "predicted_rainfall_mm": round(float(clim_pred[0]), 2),
            "predicted_avg_temp_c": round(float(clim_pred[1]), 2),
            "predicted_min_temp_c": round(float(clim_pred[2]), 2),
            "predicted_max_temp_c": round(float(clim_pred[3]), 2),
            "harvest_date": harvest_date.isoformat(),
        }

        if _price_model:
            model_crop = CROP_NAME_TO_MODEL.get(crop["name_en"].lower())
            if model_crop:
                import pandas as pd
                X_price = pd.DataFrame([{
                    "crop": model_crop,
                    "week_num": wf["week_num"],
                    "month": wf["month"],
                    "sin_week": wf["sin_week"],
                    "cos_week": wf["cos_week"],
                    "rainfall": float(clim_pred[0]),
                    "avg_temp": float(clim_pred[1]),
                    "min_temp": float(clim_pred[2]),
                    "max_temp": float(clim_pred[3]),
                }])
                predicted_price_per_kg = round(float(_price_model.predict(X_price)[0]), 2)
                price_prediction = {
                    "crop_name": crop["name_en"],
                    "model_crop_name": model_crop,
                    "predicted_price_rs_per_kg": predicted_price_per_kg,
                    "week_num": wf["week_num"],
                    "month": wf["month"],
                    "harvest_date": harvest_date.isoformat(),
                    "growing_cycle_days": growing_days,
                }
            elif crop["name_en"].lower() in DEFAULT_CROP_BASELINES:
                base = float(DEFAULT_CROP_BASELINES[crop["name_en"].lower()])
                rain_factor = (float(clim_pred[0]) - 25.0) * 0.1
                predicted_price_per_kg = round(float(max(base * 0.7, base + rain_factor)), 2)
                price_prediction = {
                    "crop_name": crop["name_en"],
                    "model_crop_name": "Market Baseline",
                    "predicted_price_rs_per_kg": predicted_price_per_kg,
                    "week_num": int(wf["week_num"]),
                    "month": int(wf["month"]),
                    "harvest_date": harvest_date.isoformat(),
                    "growing_cycle_days": growing_days,
                }

    # Fallback if climate model was offline or baseline wasn't triggered
    if predicted_price_per_kg == 0.0 and crop["name_en"].lower() in DEFAULT_CROP_BASELINES:
        predicted_price_per_kg = float(DEFAULT_CROP_BASELINES[crop["name_en"].lower()])
        price_prediction = {
            "crop_name": crop["name_en"],
            "model_crop_name": "Market Baseline",
            "predicted_price_rs_per_kg": predicted_price_per_kg,
            "week_num": int(wf["week_num"]),
            "month": int(wf["month"]),
            "harvest_date": harvest_date.isoformat(),
            "growing_cycle_days": growing_days,
        }

    # Apply Sri Lanka HARTI / DOA Wholesale Farm-Gate Bounds to prevent extreme ML outliers
    bounds = CROP_PRICE_BOUNDS.get(crop["name_en"].lower(), (80.0, 500.0))
    if predicted_price_per_kg > 0:
        predicted_price_per_kg = round(float(np.clip(predicted_price_per_kg, bounds[0], bounds[1])), 2)
        if price_prediction:
            price_prediction["predicted_price_rs_per_kg"] = predicted_price_per_kg

    # 7. Revenue & ROI (per Formula Sheet)
    # Estimated Revenue (Rs) = Estimated Yield (kg) * Predicted Market Price after Harvesting Period (Rs/kg)
    gross_revenue = round(float(estimated_yield_kg * predicted_price_per_kg), 2) if predicted_price_per_kg > 0 else 0.0
    net_profit = round(float(gross_revenue - total_opex), 2)
    # OpEx ROI (%) = [(Estimated Revenue - Cultivation Cost) / Cultivation Cost] * 100
    roi_pct = round(float(net_profit / total_opex * 100), 2) if total_opex > 0 else 0.0
    # Capital ROI (%) = [(Estimated Revenue - User Capital) / User Capital] * 100
    capital_roi_pct = round(float((gross_revenue - req.capital_lkr) / req.capital_lkr * 100), 2) if req.capital_lkr > 0 else 0.0
    # Net Profit Margin (%)
    profit_margin_pct = round(float(net_profit / gross_revenue * 100), 2) if gross_revenue > 0 else 0.0

    capital_surplus = round(float(req.capital_lkr - total_opex), 2)
    can_afford = bool(req.capital_lkr >= total_opex)

    return {
        "crop": {"id": crop["id"], "name_en": crop["name_en"], "name_si": crop["name_si"]},
        "method_type": req.method_type,
        "area": {"value": req.area_value, "unit": req.area_unit, "acres": round(area_acres, 4)},
        "capital_lkr": req.capital_lkr,
        "can_afford": can_afford,
        "capital_surplus_lkr": round(capital_surplus, 2),
        "opex": {
            "total_rs": round(total_opex, 2),
            "seed_rs": round(seed_cost, 2),
            "labour_rs": round(labour_cost, 2),
            "fertilizer_rs": round(fertilizer_cost, 2),
            "other_rs": round(other_cost, 2),
            "seed_pct": bench["seed_share_pct"],
            "labour_pct": bench["labour_share_pct"],
            "fertilizer_pct": bench["fertilizer_share_pct"],
            "other_pct": bench["other_share_pct"],
        },
        "yield": {
            "estimated_kg": round(estimated_yield_kg, 2),
            "avg_yield_per_acre": avg_yield_per_acre,
        },
        "revenue": {
            "predicted_price_per_kg": predicted_price_per_kg,
            "gross_revenue_rs": round(gross_revenue, 2),
            "net_profit_rs": round(net_profit, 2),
            "roi_pct": round(roi_pct, 2),
            "capital_roi_pct": round(capital_roi_pct, 2),
            "profit_margin_pct": round(profit_margin_pct, 2),
        },
        "climate_prediction": climate_prediction,
        "price_prediction": price_prediction,
        "harvest": {
            "plant_date": plant_date.isoformat(),
            "harvest_date": harvest_date.isoformat(),
            "growing_cycle_days": growing_days,
        },
    }


# ── GET /analytics/climate-prediction ────────────────────────────────────────
@router.get("/climate-prediction", summary="Predict climate for a given date")
async def predict_climate(target_date: Optional[str] = None):
    """Predict rainfall and temperatures for a given ISO date (defaults to today)."""
    if _climate_model is None:
        raise HTTPException(status_code=503, detail="Climate model not loaded")

    dt = date.fromisoformat(target_date) if target_date else date.today()
    wf = _week_features(dt)
    X = np.array([[wf["week_num"], wf["month"], wf["sin_week"], wf["cos_week"]]])
    pred = _climate_model.predict(X)[0]

    return {
        "date": dt.isoformat(),
        "week_num": wf["week_num"],
        "month": wf["month"],
        "predicted_rainfall_mm": round(float(pred[0]), 2),
        "predicted_avg_temp_c": round(float(pred[1]), 2),
        "predicted_min_temp_c": round(float(pred[2]), 2),
        "predicted_max_temp_c": round(float(pred[3]), 2),
    }


# ── GET /analytics/price-prediction/{crop_name} ──────────────────────────────
@router.get("/price-prediction/{crop_name}", summary="Predict crop price for the current week")
async def predict_price(crop_name: str, target_date: Optional[str] = None):
    """
    Predict the market price (Rs./kg) for a crop for a given date.
    Supported crops: Tomato, Green Chilli, Cucumber, Brinjal, Capsicum, Carrot.
    """
    model_crop = CROP_NAME_TO_MODEL.get(crop_name.lower())
    is_baseline = (model_crop is None and crop_name.lower() in DEFAULT_CROP_BASELINES)

    if not model_crop and not is_baseline:
        raise HTTPException(
            status_code=400,
            detail=f"Crop '{crop_name}' not supported by price model. Supported: Tomato, Chilli, Cucumber, Brinjal, Capsicum, Carrot"
        )

    dt = date.fromisoformat(target_date) if target_date else date.today()
    wf = _week_features(dt)

    clim_pred = [25.0, 27.0, 23.0, 31.0]
    if _climate_model is not None:
        X_clim = np.array([[wf["week_num"], wf["month"], wf["sin_week"], wf["cos_week"]]])
        clim_pred = _climate_model.predict(X_clim)[0]

    if model_crop and _price_model is not None:
        import pandas as pd
        X_price = pd.DataFrame([{
            "crop": model_crop,
            "week_num": wf["week_num"],
            "month": wf["month"],
            "sin_week": wf["sin_week"],
            "cos_week": wf["cos_week"],
            "rainfall": float(clim_pred[0]),
            "avg_temp": float(clim_pred[1]),
            "min_temp": float(clim_pred[2]),
            "max_temp": float(clim_pred[3]),
        }])
        predicted_price = float(_price_model.predict(X_price)[0])
    else:
        base = DEFAULT_CROP_BASELINES.get(crop_name.lower(), 250.0)
        rain_factor = (clim_pred[0] - 25.0) * 0.1
        predicted_price = round(max(base * 0.7, base + rain_factor), 2)

    return {
        "crop_name": crop_name,
        "model_crop_name": model_crop or "Market Baseline",
        "date": dt.isoformat(),
        "week_num": wf["week_num"],
        "month": wf["month"],
        "predicted_price_rs_per_kg": round(predicted_price, 2),
        "climate_used": {
            "rainfall_mm": round(float(clim_pred[0]), 2),
            "avg_temp_c": round(float(clim_pred[1]), 2),
        },
    }


# ── GET /analytics/price-history/{crop_name} ─────────────────────────────────
@router.get("/price-history/{crop_name}", summary="Generate weekly price forecast via ML model")
async def price_history(crop_name: str, weeks: int = 52):
    """
    Generate forward-looking weekly price forecast for the next N weeks starting from today (this month onwards)
    using the ML model or seasonal baseline.
    """
    model_crop = CROP_NAME_TO_MODEL.get(crop_name.lower())
    is_baseline = (model_crop is None and crop_name.lower() in DEFAULT_CROP_BASELINES)

    if not model_crop and not is_baseline:
        raise HTTPException(
            status_code=400,
            detail=f"Crop '{crop_name}' not supported. Supported: Tomato, Chilli, Cucumber, Brinjal, Capsicum, Carrot"
        )

    import pandas as pd
    from datetime import timedelta

    today = date.today()
    records = []

    for i in range(weeks):
        dt = today + timedelta(weeks=i)
        wf = _week_features(dt)
        clim = [25.0, 27.0, 23.0, 31.0]
        if _climate_model is not None:
            X_clim = np.array([[wf["week_num"], wf["month"], wf["sin_week"], wf["cos_week"]]])
            clim = _climate_model.predict(X_clim)[0]

        if model_crop and _price_model is not None:
            X_price = pd.DataFrame([{
                "crop": model_crop,
                "week_num": wf["week_num"],
                "month": wf["month"],
                "sin_week": wf["sin_week"],
                "cos_week": wf["cos_week"],
                "rainfall": float(clim[0]),
                "avg_temp": float(clim[1]),
                "min_temp": float(clim[2]),
                "max_temp": float(clim[3]),
            }])
            price = float(_price_model.predict(X_price)[0])
        else:
            base = DEFAULT_CROP_BASELINES.get(crop_name.lower(), 250.0)
            seasonal = math.sin(2 * math.pi * wf["week_num"] / 52) * 20.0
            price = round(base + seasonal + (float(clim[0]) - 25.0) * 0.05, 2)

        # Apply sensible floor and soft ceiling so curve preserves natural variation without flat-lining
        crop_bounds = CROP_PRICE_BOUNDS.get(crop_name.lower(), (60.0, 1500.0))
        price = max(float(price), crop_bounds[0])
        if price > crop_bounds[1]:
            # Apply soft compression above benchmark ceiling rather than flat-clamping
            price = crop_bounds[1] + (price - crop_bounds[1]) * 0.25
        price = round(float(price), 2)

        records.append({
            "week_start": dt.isoformat(),
            "week_num": wf["week_num"],
            "month": wf["month"],
            "predicted_price_rs_per_kg": round(price, 2),
            "rainfall_mm": round(float(clim[0]), 2),
        })

    return {
        "crop_name": crop_name,
        "model_crop_name": model_crop or "Market Baseline",
        "weeks": weeks,
        "data": records,
    }
