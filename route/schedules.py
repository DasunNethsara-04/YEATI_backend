"""
Schedules router — Cultivation timeline and daily/weekly agronomic task schedules
for Sri Lankan vegetable crops (Tomato, Chilli, Cucumber, Brinjal, Capsicum, Carrot)
across Open Field, Hydroponics, and Organic farming methods.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from config.supabase import supabase

router = APIRouter(prefix="/schedules", tags=["Schedules"])

# ─────────────────────────────────────────────────────────────────────────────
# Crop Profiles & Cultivation Knowledge Base
# ─────────────────────────────────────────────────────────────────────────────

CROP_PROFILES: Dict[str, Dict[str, Any]] = {
    "Tomato": {
        "name_en": "Tomato",
        "name_si": "තක්කාලි",
        "category": "Solanaceae",
        "cycle_days": 120,
        "nursery_days": 25,
        "stages": [
            {"name": "Land & Nursery Prep", "start_day": 0, "end_day": 14, "description": "Nursery bed preparation, seed treatment, and soil preparation."},
            {"name": "Transplanting & Establishment", "start_day": 15, "end_day": 35, "description": "Transplanting hardened seedlings, basal nutrition, and early root establishment."},
            {"name": "Vegetative & Trellising", "start_day": 36, "end_day": 60, "description": "Active vegetative canopy growth, staking, sucker pruning, and first top-dressing."},
            {"name": "Flowering & Fruit Setting", "start_day": 61, "end_day": 85, "description": "Bloom phase, fruit swelling, calcium/potassium supplementation, and pest vigilance."},
            {"name": "Harvesting & Picking", "start_day": 86, "end_day": 120, "description": "Breaker stage to ripe fruit harvesting every 3-4 days and post-harvest grading."}
        ],
        "pests_diseases": ["Whiteflies", "Fruit borer", "Leaf miner", "Late blight", "Early blight", "Bacterial wilt"],
        "daily_routine": [
            {"time": "06:30 AM - 07:30 AM", "activity": "Irrigation & Soil Check", "notes": "Check topsoil/substrate moisture. Run morning drip/fertigation before peak heat."},
            {"time": "07:30 AM - 08:30 AM", "activity": "Pest & Leaf Scouting", "notes": "Inspect undersides of 10 random leaves for whitefly nymphs, leaf miners, and early blight spots."},
            {"time": "04:30 PM - 05:30 PM", "activity": "Pruning & Evening Walkthrough", "notes": "Remove side suckers during dry conditions; check moisture level for evening recovery."}
        ]
    },
    "Chilli": {
        "name_en": "Chilli",
        "name_si": "අමු මිරිස්",
        "category": "Solanaceae",
        "cycle_days": 150,
        "nursery_days": 35,
        "stages": [
            {"name": "Nursery & Field Prep", "start_day": 0, "end_day": 28, "description": "Nursery bed protection from thrips, soil liming, and organic basal manure incorporation."},
            {"name": "Transplanting & Rooting", "start_day": 29, "end_day": 50, "description": "Transplanting 35-day seedlings with starter watering and light mulch."},
            {"name": "Branching & Canopy Growth", "start_day": 51, "end_day": 80, "description": "N-K top dressings, weed clearing, and intensive mite/thrips monitoring."},
            {"name": "Flowering & Pod Formation", "start_day": 81, "end_day": 105, "description": "Continuous blooming and fruit elongation; balanced potassium feeding."},
            {"name": "Multi-Flush Harvesting", "start_day": 106, "end_day": 150, "description": "Regular green pod harvesting every 7-10 days, followed by recovery fertilizer."}
        ],
        "pests_diseases": ["Thrips", "Broad mites (leaf curl)", "Aphids", "Anthracnose (die-back)", "Bacterial wilt"],
        "daily_routine": [
            {"time": "06:30 AM - 07:30 AM", "activity": "Morning Irrigation", "notes": "Maintain consistent moisture; avoid water stress during early flowering to prevent flower drop."},
            {"time": "07:30 AM - 08:30 AM", "activity": "Thrips & Mite Check", "notes": "Examine terminal shoots and young leaves with a hand lens for upward curling (thrips) or downward cupping (mites)."},
            {"time": "04:30 PM - 05:30 PM", "activity": "Field Sanitation", "notes": "Collect and burn any anthracnose-spotted pods or die-back twigs to prevent fungal spread."}
        ]
    },
    "Cucumber": {
        "name_en": "Cucumber",
        "name_si": "පිපිඤ්ඤා",
        "category": "Cucurbitaceae",
        "cycle_days": 75,
        "nursery_days": 12,
        "stages": [
            {"name": "Seed Sowing & Medium Prep", "start_day": 0, "end_day": 10, "description": "Direct sowing or plug trays; deep organic manure trenches or coir slab hydration."},
            {"name": "Vine Establishment & Trellising", "start_day": 11, "end_day": 25, "description": "Trellis wire installation, vertical vine training, and basal NPK feeding."},
            {"name": "Flowering & Rapid Growth", "start_day": 26, "end_day": 40, "description": "Rapid vegetative growth, lateral pinching below 5th node, fruit fly traps."},
            {"name": "High-Frequency Harvesting", "start_day": 41, "end_day": 75, "description": "Harvesting young crisp cucumbers every 2-3 days in early morning."}
        ],
        "pests_diseases": ["Fruit flies (Bactrocera)", "Cucumber beetles", "Powdery mildew", "Downy mildew"],
        "daily_routine": [
            {"time": "06:30 AM - 07:30 AM", "activity": "Morning Harvest & Water", "notes": "Pick marketable fruits before the sun heats the skin; initiate generous drip irrigation."},
            {"time": "08:00 AM - 09:00 AM", "activity": "Vine Training", "notes": "Wind leading stems around trellis twine clockwise; prune lower yellowing senescent leaves."},
            {"time": "04:30 PM - 05:30 PM", "activity": "Pheromone Trap Inspection", "notes": "Inspect cue-lure fruit fly traps along plot perimeter; verify trap clearance."}
        ]
    },
    "Brinjal": {
        "name_en": "Brinjal",
        "name_si": "වම්බටු",
        "category": "Solanaceae",
        "cycle_days": 140,
        "nursery_days": 30,
        "stages": [
            {"name": "Nursery & Field Tillage", "start_day": 0, "end_day": 25, "description": "Raised nursery seedbeds, deep ploughing, and farmyard manure incorporation."},
            {"name": "Transplanting & Establishment", "start_day": 26, "end_day": 45, "description": "Transplanting stocky 4-leaf seedlings, drenching against damping off."},
            {"name": "Vegetative & Early Shoot Care", "start_day": 46, "end_day": 70, "description": "Regular earthing up, top dressing with Nitrogen/Potassium, and shoot borer inspection."},
            {"name": "Flowering & Fruit Development", "start_day": 71, "end_day": 95, "description": "High phosphorus/potassium supply, shoot borer clipping, and leaf spot monitoring."},
            {"name": "Continuous Harvest Flushes", "start_day": 96, "end_day": 140, "description": "Harvesting glossy fruits with calyx every 4-6 days, with booster organic/NPK feeding."}
        ],
        "pests_diseases": ["Shoot and Fruit Borer (Leucinodes)", "Epilachna beetle", "Whiteflies", "Bacterial wilt", "Phomopsis blight"],
        "daily_routine": [
            {"time": "06:30 AM - 07:30 AM", "activity": "Deep Watering", "notes": "Soak root zone thoroughly; Brinjal requires deep root moisture for high yield."},
            {"time": "07:30 AM - 08:30 AM", "activity": "Shoot Borer Scouting", "notes": "Clip off any wilted terminal shoots showing borer entry holes and submerge in soapy water."},
            {"time": "04:30 PM - 05:30 PM", "activity": "Foliar Health Check", "notes": "Inspect underside for Epilachna beetle grubs and remove skeletonized leaves."}
        ]
    },
    "Capsicum": {
        "name_en": "Capsicum",
        "name_si": "මාළු මිරිස්",
        "category": "Solanaceae",
        "cycle_days": 120,
        "nursery_days": 30,
        "stages": [
            {"name": "Nursery Sowing & Medium Prep", "start_day": 0, "end_day": 25, "description": "Plug tray seed sowing with pro-tray mix; soil solarization or greenhouse bed prep."},
            {"name": "Transplanting & Staking", "start_day": 26, "end_day": 45, "description": "Transplanting vigorous seedlings, staking stems to support heavy fruit load."},
            {"name": "Vegetative Growth & Canopy Pruning", "start_day": 46, "end_day": 70, "description": "Pruning to 2-3 main stems, suckering, and calcium nitrate foliar spraying."},
            {"name": "Flowering & Fruit Setting", "start_day": 71, "end_day": 90, "description": "Optimal temperature management, balanced fertigation, blossom-end rot prevention."},
            {"name": "Green / Color Harvest", "start_day": 91, "end_day": 120, "description": "Careful scissor-cutting of firm, glossy pods with intact pedicel."}
        ],
        "pests_diseases": ["Thrips", "Broad mites", "Aphids", "Bacterial leaf spot", "Anthracnose", "Blossom end rot"],
        "daily_routine": [
            {"time": "06:30 AM - 07:30 AM", "activity": "Fertigation & pH Check", "notes": "Deliver morning nutrient solution. Keep pH 5.8-6.3 and EC 2.0-2.4 mS/cm."},
            {"time": "07:30 AM - 08:30 AM", "activity": "Micro-Pest Inspection", "notes": "Scout young leaves and flower buds for thrips and mite distortion."},
            {"time": "04:30 PM - 05:30 PM", "activity": "Pruning Side Shoots", "notes": "Remove auxiliary shoots beneath the first fork to concentrate energy into bell fruits."}
        ]
    },
    "Carrot": {
        "name_en": "Carrot",
        "name_si": "කැරට්",
        "category": "Apiaceae",
        "cycle_days": 105,
        "nursery_days": 0,
        "stages": [
            {"name": "Fine Tilth Land Preparation", "start_day": 0, "end_day": 7, "description": "Deep stone-free soil plowing (30 cm), raised beds, and basal rock phosphate / compost."},
            {"name": "Direct Sowing & Germination", "start_day": 8, "end_day": 20, "description": "Line sowing pelleted or mixed sand seeds, light straw mulching, and daily gentle misting."},
            {"name": "Seedling Thinning & Weeding", "start_day": 21, "end_day": 45, "description": "Crucial thinning to 5 cm intra-row spacing to prevent root crowding and forking."},
            {"name": "Root Swelling & Foliage Care", "start_day": 46, "end_day": 75, "description": "Potassium-rich top-dressing, earthing up exposed root shoulders, Alternaria blight watch."},
            {"name": "Maturity & Lifting Harvest", "start_day": 76, "end_day": 105, "description": "Careful lifting of crisp taproots in moist soil, washing, grading, and trimming."}
        ],
        "pests_diseases": ["Carrot rust fly", "Root-knot nematodes", "Wireworms", "Alternaria leaf blight", "Cavity spot"],
        "daily_routine": [
            {"time": "06:30 AM - 07:30 AM", "activity": "Gentle Overhead Watering", "notes": "Ensure even soil moisture to avoid taproot splitting and cracking."},
            {"time": "07:30 AM - 08:30 AM", "activity": "Foliage Blight Scouting", "notes": "Inspect feathery carrot foliage for dark brown water-soaked lesions (Alternaria)."},
            {"time": "04:30 PM - 05:30 PM", "activity": "Shoulder Soil Hilling", "notes": "Cover exposed crown shoulders with soil to prevent solar greening."}
        ]
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# Dynamic Activity Generator based on Crop & Method
# ─────────────────────────────────────────────────────────────────────────────

def _generate_weekly_tasks(crop_name: str, method: str) -> List[Dict[str, Any]]:
    """Generate structured weekly tasks tailored for the crop and cultivation method."""
    method_upper = method.upper()
    is_hydro = "HYDRO" in method_upper
    is_organic = "ORGANIC" in method_upper

    # Base task repository customized by crop
    if crop_name in ["Tomato", "Capsicum"]:
        weeks_data = [
            {
                "week": 1,
                "title": "Nursery Establishment & Medium Preparation",
                "stage": "Land & Nursery Prep",
                "days_range": "Day 1 - 7",
                "tasks": [
                    {
                        "category": "LAND_PREPARATION",
                        "title": "Sterilize & Prepare Substrate / Soil Beds" if is_hydro else ("Incorporate Aged FYM & Biochar" if is_organic else "Deep Plough & Build Raised Beds"),
                        "frequency": "ONCE",
                        "timing": "Day 1 - 3",
                        "description": "Prepare grow slabs (flush with pH 5.8 water) or plow soil 25-30 cm deep and add basal organic manure." if is_hydro else "Thoroughly till soil, add well-rotted cow dung (8-10 tons/ac) and build 1m wide raised beds.",
                        "beginner_tip": "Raised beds improve drainage and root aeration, preventing fungal root rots after rains."
                    },
                    {
                        "category": "PLANTING",
                        "title": "Sow F1 Hybrid Seeds in Plug Trays",
                        "frequency": "ONCE",
                        "timing": "Day 3 - 5",
                        "description": "Sow 1 seed per cell in 98-cell seedling trays filled with sterilized cocopeat/vermicompost. Cover lightly with 0.5 cm fine substrate.",
                        "beginner_tip": "Do not bury seeds too deep. Keep trays under 50% shade netting until germination."
                    },
                    {
                        "category": "IRRIGATION",
                        "title": "Fine Mist Spraying on Nursery Trays",
                        "frequency": "DAILY",
                        "timing": "Twice daily (07:00 AM & 03:00 PM)",
                        "description": "Use a fine hand sprayer to keep the top layer moist without washing away seeds.",
                        "beginner_tip": "Overwatering seeds causes damping-off disease. Substrate should feel like a squeezed sponge."
                    }
                ]
            },
            {
                "week": 2,
                "title": "Germination & Seedling Care",
                "stage": "Land & Nursery Prep",
                "days_range": "Day 8 - 14",
                "tasks": [
                    {
                        "category": "PEST_MONITORING",
                        "title": "Scout for Cutworms & Damping-Off",
                        "frequency": "DAILY",
                        "timing": "Morning (07:00 AM)",
                        "description": "Check stems at soil level. Remove any collapsed seedlings immediately to prevent fungal spread.",
                        "beginner_tip": "If damping-off appears, drench trays with Trichoderma viride or light copper fungicide."
                    },
                    {
                        "category": "FERTILIZING",
                        "title": "Quarter-Strength Liquid Starter Nutrient",
                        "frequency": "WEEKLY",
                        "timing": "Day 12",
                        "description": "Apply dilute nutrient (EC 0.8 for hydroponics, dilute vermiwash for organic, or 0.1% 19:19:19 for open field).",
                        "beginner_tip": "Young seedlings only need very mild nutrition; high concentration burns tender roots."
                    }
                ]
            },
            {
                "week": 3,
                "title": "Hardening & Transplanting Preparation",
                "stage": "Land & Nursery Prep",
                "days_range": "Day 15 - 21",
                "tasks": [
                    {
                        "category": "LAND_PREPARATION",
                        "title": "Apply Basal Fertilizer / Compost to Main Field",
                        "frequency": "ONCE",
                        "timing": "Day 18 - 20",
                        "description": "Apply basal NPK (50kg Urea, 100kg TSP, 50kg MOP per acre) or 5 tons vermicompost and bone meal.",
                        "beginner_tip": "Mix fertilizers evenly into the top 15 cm of soil 2-3 days before transplanting."
                    },
                    {
                        "category": "PLANTING",
                        "title": "Harden Seedlings Ahead of Field Placement",
                        "frequency": "DAILY",
                        "timing": "Day 16 - 21",
                        "description": "Gradually increase sunlight exposure and reduce watering frequency over 5 days to toughen stems.",
                        "beginner_tip": "Hardened seedlings experience near-zero transplant shock and establish rapidly."
                    }
                ]
            },
            {
                "week": 4,
                "title": "Transplanting into Field & Root Establishment",
                "stage": "Transplanting & Establishment",
                "days_range": "Day 22 - 28",
                "tasks": [
                    {
                        "category": "PLANTING",
                        "title": "Transplant Stocky Seedlings into Main Beds",
                        "frequency": "ONCE",
                        "timing": "Late Afternoon (04:00 PM)",
                        "description": "Transplant with 60 cm row-to-row and 45 cm plant-to-plant spacing. Firm soil gently around root collar.",
                        "beginner_tip": "Always transplant in late afternoon or on overcast days so plants adapt during cool night hours."
                    },
                    {
                        "category": "IRRIGATION",
                        "title": "Immediate Deep Drenching & Establishment Irrigation",
                        "frequency": "DAILY",
                        "timing": "Day 22 - 28 (Morning)",
                        "description": "Apply 1-2 liters of water per plant immediately after planting to eliminate air pockets around root plugs.",
                        "beginner_tip": "Consistent moisture during the first 7 days is paramount for adventitious root development."
                    }
                ]
            },
            {
                "week": 5,
                "title": "Weed Control & Trellis Post Installation",
                "stage": "Vegetative & Trellising",
                "days_range": "Day 29 - 35",
                "tasks": [
                    {
                        "category": "PRUNING",
                        "title": "Erect Support Stakes & Trellis Twine",
                        "frequency": "ONCE",
                        "timing": "Day 30 - 32",
                        "description": "Install sturdy bamboo or timber posts (2m high) every 3 meters and stretch horizontal nylon trellis lines.",
                        "beginner_tip": "Staking keeps leaves and fruit off wet soil, reducing fungal blights by up to 70%."
                    },
                    {
                        "category": "FERTILIZING",
                        "title": "First Vegetative Top-Dressing",
                        "frequency": "ONCE",
                        "timing": "Day 35",
                        "description": "Apply 30 kg Urea & 20 kg MOP per acre side-dressed 10 cm from stem base, or drench with fermented fish amino / Panchagavya.",
                        "beginner_tip": "Never place chemical fertilizer directly against the stem; always water in immediately."
                    }
                ]
            },
            {
                "week": 6,
                "title": "Canopy Pruning & Sucker Removal",
                "stage": "Vegetative & Trellising",
                "days_range": "Day 36 - 42",
                "tasks": [
                    {
                        "category": "PRUNING",
                        "title": "Pinch Side Suckers (Axillary Shoots)",
                        "frequency": "WEEKLY",
                        "timing": "Morning during dry weather",
                        "description": "Pinch off side shoots emerging between leaf axils and main stem when they are 2-4 cm long. Train to 1-2 main stems.",
                        "beginner_tip": "Prune only with clean hands or sanitized snips when foliage is dry to avoid spreading bacterial canker."
                    },
                    {
                        "category": "PEST_MONITORING",
                        "title": "Deploy Yellow Sticky Traps for Whiteflies & Thrips",
                        "frequency": "ONCE",
                        "timing": "Day 38",
                        "description": "Hang yellow sticky cards at canopy height (1 trap per 100 sq meters) to catch flying vectors.",
                        "beginner_tip": "Yellow traps give early warning of whiteflies before they transmit destructive leaf curl virus."
                    }
                ]
            },
            {
                "week": 7,
                "title": "First Flower Cluster & Calcium Boost",
                "stage": "Flowering & Fruit Setting",
                "days_range": "Day 43 - 49",
                "tasks": [
                    {
                        "category": "FERTILIZING",
                        "title": "Foliar Calcium Boron Application",
                        "frequency": "BI_WEEKLY",
                        "timing": "Day 45 (Early Morning)",
                        "description": "Spray 0.2% Calcium Nitrate + Boron foliar solution or bone ash brew to fortify cell walls.",
                        "beginner_tip": "Calcium and Boron are critical at first flower set to prevent blossom-end rot (sunken black bottom on fruit)."
                    },
                    {
                        "category": "IRRIGATION",
                        "title": "Maintain Steady Drip Cycle — Avoid Moisture Fluctuations",
                        "frequency": "DAILY",
                        "timing": "06:30 AM",
                        "description": "Deliver measured uniform water. Inconsistent moisture causes fruit splitting and blossom drop.",
                        "beginner_tip": "Never let soil swing from bone-dry to waterlogged. Mulch beds with clean rice straw."
                    }
                ]
            },
            {
                "week": 8,
                "title": "Fruit Swelling & Potassium Top-Dressing",
                "stage": "Flowering & Fruit Setting",
                "days_range": "Day 50 - 56",
                "tasks": [
                    {
                        "category": "FERTILIZING",
                        "title": "Fruit-Enrichment Potassium Top Dressing",
                        "frequency": "WEEKLY",
                        "timing": "Day 52",
                        "description": "Side-dress 25 kg MOP (or adjust Hydroponic AB solution to EC 2.4 with high potassium) to boost fruit weight and brix.",
                        "beginner_tip": "Potassium drives sugar transport into developing fruits for better flavor and firm walls."
                    },
                    {
                        "category": "PEST_MONITORING",
                        "title": "Fruit Borer Scouting & Pheromone Lures",
                        "frequency": "BI_WEEKLY",
                        "timing": "Day 54",
                        "description": "Check green fruit calyxes for tiny entry holes and sawdust-like frass. Install Helicoverpa pheromone traps.",
                        "beginner_tip": "Spray organic Bacillus thuringiensis (Bt) or Neem seed kernel extract (NSKE 5%) if egg counts rise."
                    }
                ]
            },
            {
                "week": 9,
                "title": "Lower Canopy Aeration & De-leafing",
                "stage": "Flowering & Fruit Setting",
                "days_range": "Day 57 - 63",
                "tasks": [
                    {
                        "category": "PRUNING",
                        "title": "Prune Lower Senescent & Yellow Leaves",
                        "frequency": "WEEKLY",
                        "timing": "Day 60",
                        "description": "Remove all bottom leaves below the first fruiting truss. Dispose of trimmed foliage outside the plot.",
                        "beginner_tip": "Improves under-canopy ventilation and sunlight penetration, halting soil-borne fungal spores."
                    },
                    {
                        "category": "PEST_MONITORING",
                        "title": "Inspect for Late Blight (Phytophthora)",
                        "frequency": "DAILY",
                        "timing": "After rainfall or heavy dew",
                        "description": "Check for water-soaked greasy brown lesions on leaves and stems with white fungal mold underneath.",
                        "beginner_tip": "Late blight spreads rapidly in humid weather. Apply prophylactic copper hydroxide or Trichoderma immediately."
                    }
                ]
            },
            {
                "week": 10,
                "title": "First Breaker-Stage Fruit Harvesting",
                "stage": "Harvesting & Picking",
                "days_range": "Day 64 - 70",
                "tasks": [
                    {
                        "category": "HARVESTING",
                        "title": "Commence First Flush Harvest at Breaker Stage",
                        "frequency": "BI_WEEKLY",
                        "timing": "Cool morning (06:30 AM - 09:00 AM)",
                        "description": "Harvest fruits when the blossom end turns pink/light red (breaker stage). Gently twist and snap or use clean snips.",
                        "beginner_tip": "Picking at breaker stage reduces bird damage, eliminates transit bruising, and maximizes shelf life."
                    },
                    {
                        "category": "HARVESTING",
                        "title": "Post-Harvest Shade Cooling & Grading",
                        "frequency": "BI_WEEKLY",
                        "timing": "Immediately post-pick",
                        "description": "Transfer picked fruits into ventilated plastic crates. Keep in cool shade; never leave crates in direct sun.",
                        "beginner_tip": "Field heat degrades fruit quality quickly. Cool fruits under ventilated shade before packing."
                    }
                ]
            },
            {
                "week": 11,
                "title": "Mid-Harvest Boost & Ongoing Pickings",
                "stage": "Harvesting & Picking",
                "days_range": "Day 71 - 77",
                "tasks": [
                    {
                        "category": "HARVESTING",
                        "title": "Harvest Twice-Weekly Picking Cycle",
                        "frequency": "BI_WEEKLY",
                        "timing": "Every 3-4 days",
                        "description": "Pick uniform, mature fruits systematically row-by-row.",
                        "beginner_tip": "Frequent picking stimulates the plant to set new flowers and develop upper trusses."
                    },
                    {
                        "category": "FERTILIZING",
                        "title": "Post-Harvest Booster Nutrition",
                        "frequency": "WEEKLY",
                        "timing": "After heavy pick",
                        "description": "Drench light liquid NPK or Jeevamrutha to sustain plant stamina for subsequent fruiting flushes.",
                        "beginner_tip": "Continuous heavy yield depletes soil minerals; replenishment maintains fruit size."
                    }
                ]
            },
            {
                "week": 12,
                "title": "Peak Production & Flush Maintenance",
                "stage": "Harvesting & Picking",
                "days_range": "Day 78 - 84",
                "tasks": [
                    {
                        "category": "HARVESTING",
                        "title": "Peak Flush Harvest & Grade Sorting (Grade A / B)",
                        "frequency": "BI_WEEKLY",
                        "timing": "Morning",
                        "description": "Sort into Grade A (uniform size, blemish-free) and Grade B for local wholesale vs retail premium.",
                        "beginner_tip": "Proper grading increases farmer revenue by 20-30% compared to selling mixed ungraded sacks."
                    },
                    {
                        "category": "IRRIGATION",
                        "title": "Consistent Regulated Irrigation",
                        "frequency": "DAILY",
                        "timing": "Morning",
                        "description": "Maintain steady hydration. Do not let soil dry out as peak fruit load demands maximum water uptake.",
                        "beginner_tip": "Avoid overhead hose watering during harvest to keep fruit skins dry and prevent fungal rot."
                    }
                ]
            }
        ]
    elif crop_name == "Cucumber":
        weeks_data = [
            {
                "week": 1,
                "title": "Direct Sowing & Bed Preparation",
                "stage": "Seed Sowing & Medium Prep",
                "days_range": "Day 1 - 7",
                "tasks": [
                    {
                        "category": "LAND_PREPARATION",
                        "title": "Deep Plowing & Trench Compost Incorporation",
                        "frequency": "ONCE",
                        "timing": "Day 1 - 3",
                        "description": "Dig 30 cm trenches, fill with well-rotted farmyard manure or hydrate coir grow bags.",
                        "beginner_tip": "Cucumbers possess delicate shallow root systems that require soft, well-aerated organic soil."
                    },
                    {
                        "category": "PLANTING",
                        "title": "Direct Seed Sowing (2 seeds per pit)",
                        "frequency": "ONCE",
                        "timing": "Day 4 - 5",
                        "description": "Sow 2-3 cm deep at 60 cm intra-row and 1.2 m inter-row spacing. Water lightly with rose can.",
                        "beginner_tip": "Germination occurs in 4-6 days. Thin to 1 strong seedling per hill once true leaves emerge."
                    },
                    {
                        "category": "IRRIGATION",
                        "title": "Daily Gentle Moisture Delivery",
                        "frequency": "DAILY",
                        "timing": "Morning",
                        "description": "Keep seed zone moist but not drenched. Avoid crust formation on soil surface.",
                        "beginner_tip": "Hard soil crust traps emerging cotyledons; mulch lightly with composted coir dust."
                    }
                ]
            },
            {
                "week": 2,
                "title": "Thinning & Vertical Trellis Setup",
                "stage": "Vine Establishment & Trellising",
                "days_range": "Day 8 - 14",
                "tasks": [
                    {
                        "category": "PRUNING",
                        "title": "Erect Cucumber Trellis Netting / Overhead Wire",
                        "frequency": "ONCE",
                        "timing": "Day 10 - 12",
                        "description": "Install 2m high A-frame or vertical trellis netting so vines climb upwards off the wet ground.",
                        "beginner_tip": "Vertical trellising produces straight, uniformly green, disease-free cucumbers with double the yield."
                    },
                    {
                        "category": "PLANTING",
                        "title": "Thin Seedlings to Single Vigorous Plant",
                        "frequency": "ONCE",
                        "timing": "Day 12",
                        "description": "Snip the weaker seedling with scissors at ground level. Do not pull to avoid disturbing neighbor roots.",
                        "beginner_tip": "Leaving multiple plants in one hill results in small, bitter, stunted cucumbers."
                    }
                ]
            },
            {
                "week": 3,
                "title": "Rapid Vine Training & Lateral Pinching",
                "stage": "Vine Establishment & Trellising",
                "days_range": "Day 15 - 21",
                "tasks": [
                    {
                        "category": "PRUNING",
                        "title": "Prune Lower Side Shoots below 5th Node",
                        "frequency": "WEEKLY",
                        "timing": "Day 18",
                        "description": "Remove all female flowers and side branches from nodes 1 to 5 to allow the vine to establish strong root architecture.",
                        "beginner_tip": "Sacrificing earliest tiny cucumbers channels energy into building a massive, season-long producing vine."
                    },
                    {
                        "category": "FERTILIZING",
                        "title": "Nitrogen-Potassium Vegetative Fertigation",
                        "frequency": "WEEKLY",
                        "timing": "Day 20",
                        "description": "Apply balanced NPK top-dress or hydroponic solution (EC 1.8 mS/cm).",
                        "beginner_tip": "Fast-growing vines double in size every few days; maintain adequate nitrogen."
                    }
                ]
            },
            {
                "week": 4,
                "title": "Bloom Phase & Fruit Fly Trap Installation",
                "stage": "Flowering & Rapid Growth",
                "days_range": "Day 22 - 28",
                "tasks": [
                    {
                        "category": "PEST_MONITORING",
                        "title": "Hang Methyl Eugenol / Cue-Lure Fruit Fly Traps",
                        "frequency": "ONCE",
                        "timing": "Day 24",
                        "description": "Install male cue-lure traps around perimeter 1.5m above ground (4-6 traps per acre).",
                        "beginner_tip": "Fruit flies sting tender young fruit ovaries, causing curved, rotting fruit. Trapping is essential."
                    },
                    {
                        "category": "IRRIGATION",
                        "title": "Increase Daily Water Volume during Bloom",
                        "frequency": "DAILY",
                        "timing": "06:30 AM & 02:30 PM",
                        "description": "Cucumbers are 95% water. Increase drip volume to prevent fruit bitterness and hollow heart.",
                        "beginner_tip": "Moisture stress triggers synthesis of cucurbitacin, making cucumbers taste intensely bitter."
                    }
                ]
            },
            {
                "week": 5,
                "title": "Downy Mildew Prevention & Early Harvest",
                "stage": "High-Frequency Harvesting",
                "days_range": "Day 29 - 35",
                "tasks": [
                    {
                        "category": "PEST_MONITORING",
                        "title": "Scout for Angular Leaf Spots (Downy Mildew)",
                        "frequency": "DAILY",
                        "timing": "Morning",
                        "description": "Inspect upper leaf surfaces for yellow angular spots bounded by leaf veins; spray bio-fungicide or copper if spotted.",
                        "beginner_tip": "Never wet cucumber foliage in late evening; damp leaves overnight welcome downy mildew."
                    },
                    {
                        "category": "HARVESTING",
                        "title": "Commence First Crisp Cucumber Harvesting",
                        "frequency": "BI_WEEKLY",
                        "timing": "Cool morning (06:30 AM)",
                        "description": "Cut crisp, dark green fruits with 1 cm stem using sharp snips when they reach 15-20 cm length.",
                        "beginner_tip": "Harvest every 2 days. Leaving overgrown fruit on the vine halts all future flower production."
                    }
                ]
            },
            {
                "week": 6,
                "title": "Peak Continuous Pickings & Replenishment",
                "stage": "High-Frequency Harvesting",
                "days_range": "Day 36 - 42",
                "tasks": [
                    {
                        "category": "HARVESTING",
                        "title": "Harvest Every 48 Hours",
                        "frequency": "BI_WEEKLY",
                        "timing": "Morning",
                        "description": "Systematic harvest of marketable cucumbers. Pack gently in ventilated crates.",
                        "beginner_tip": "Handle gently to preserve natural fruit bloom and avoid skin scratches."
                    },
                    {
                        "category": "FERTILIZING",
                        "title": "Weekly Potassium Booster Dose",
                        "frequency": "WEEKLY",
                        "timing": "After heavy pick",
                        "description": "Apply high-potassium soluble fertilizer or compost tea to support developing fruits.",
                        "beginner_tip": "Keeps fruit straight and thick-walled without tapering at the ends."
                    }
                ]
            }
        ]
    elif crop_name == "Chilli":
        weeks_data = [
            {
                "week": 1,
                "title": "Nursery Bed Preparation & Sowing",
                "stage": "Nursery & Field Prep",
                "days_range": "Day 1 - 7",
                "tasks": [
                    {
                        "category": "LAND_PREPARATION",
                        "title": "Solarize & Form Raised Nursery Beds",
                        "frequency": "ONCE",
                        "timing": "Day 1 - 3",
                        "description": "Build 15 cm high raised beds with 1:1 soil and well-rotted compost. Drench with warm water and solarize or treat with Trichoderma.",
                        "beginner_tip": "Chilli seedlings are sensitive to damping-off; sterilized or bio-inoculated soil is vital."
                    },
                    {
                        "category": "PLANTING",
                        "title": "Line Sowing in Nursery Trays / Beds",
                        "frequency": "ONCE",
                        "timing": "Day 4 - 5",
                        "description": "Sow seeds in shallow furrows 5 cm apart or 1 seed per tray plug. Cover with fine compost.",
                        "beginner_tip": "Keep beds covered with light shade mesh until germination (usually 7-10 days)."
                    }
                ]
            },
            {
                "week": 2,
                "title": "Germination & Thrips Protection",
                "stage": "Nursery & Field Prep",
                "days_range": "Day 8 - 14",
                "tasks": [
                    {
                        "category": "PEST_MONITORING",
                        "title": "Inspect for Thrips & Damping Off",
                        "frequency": "DAILY",
                        "timing": "Morning",
                        "description": "Check tender shoots for thrips feeding. Spray light neem seed kernel extract (3%) as prophylactic barrier.",
                        "beginner_tip": "Protecting seedlings from thrips in the nursery prevents Chilli Leaf Curl Virus in the field."
                    },
                    {
                        "category": "IRRIGATION",
                        "title": "Regulated Morning Watering",
                        "frequency": "DAILY",
                        "timing": "07:00 AM",
                        "description": "Moisten root zone thoroughly in morning; avoid late evening dampness.",
                        "beginner_tip": "Chilli hates standing water; ensure beds drain freely."
                    }
                ]
            },
            {
                "week": 4,
                "title": "Hardening & Field Bed Preparation",
                "stage": "Nursery & Field Prep",
                "days_range": "Day 22 - 28",
                "tasks": [
                    {
                        "category": "LAND_PREPARATION",
                        "title": "Main Field Tilling & Basal Fertilizer Addition",
                        "frequency": "ONCE",
                        "timing": "Day 25",
                        "description": "Plough field to 25 cm depth. Apply basal NPK or 10 tons compost/FYM per acre.",
                        "beginner_tip": "Incorporate 200 kg agricultural lime per acre if soil pH is below 6.0."
                    },
                    {
                        "category": "PLANTING",
                        "title": "Harden Seedlings Ahead of Field Placement",
                        "frequency": "DAILY",
                        "timing": "Day 24 - 28",
                        "description": "Withhold water slightly and expose seedlings to full sunlight for 5 days.",
                        "beginner_tip": "Stems turn sturdy and purplish-green, signifying good field readiness."
                    }
                ]
            },
            {
                "week": 5,
                "title": "Field Transplanting & Spacing",
                "stage": "Transplanting & Rooting",
                "days_range": "Day 29 - 35",
                "tasks": [
                    {
                        "category": "PLANTING",
                        "title": "Transplant 35-Day Seedlings",
                        "frequency": "ONCE",
                        "timing": "Late afternoon (04:00 PM)",
                        "description": "Plant at 60 cm x 45 cm spacing. Drench root zone immediately with water.",
                        "beginner_tip": "Do not bury the seedling deeper than its original nursery soil line."
                    },
                    {
                        "category": "IRRIGATION",
                        "title": "Establishment Irrigation & Mulching",
                        "frequency": "DAILY",
                        "timing": "Morning",
                        "description": "Keep root zone evenly moist. Apply organic straw mulch around plants to conserve moisture and suppress weeds.",
                        "beginner_tip": "Mulching also prevents soil splashes carrying fungal spores onto lower leaves."
                    }
                ]
            },
            {
                "week": 7,
                "title": "Vegetative Branching & Broad Mite Check",
                "stage": "Branching & Canopy Growth",
                "days_range": "Day 43 - 49",
                "tasks": [
                    {
                        "category": "FERTILIZING",
                        "title": "First Top Dressing (Urea & MOP)",
                        "frequency": "ONCE",
                        "timing": "Day 45",
                        "description": "Apply 35 kg Urea and 25 kg MOP per acre ringed 15 cm from stem. Earth up soil over fertilizer.",
                        "beginner_tip": "Earthing up stabilizes the plant against monsoon winds and covers shallow root flares."
                    },
                    {
                        "category": "PEST_MONITORING",
                        "title": "Scout for Broad Mite Infestation (Downward Curled Leaves)",
                        "frequency": "BI_WEEKLY",
                        "timing": "Morning",
                        "description": "Look for glossy, brittle downward-curled leaves. Spray wettable sulfur (2g/L) or neem oil.",
                        "beginner_tip": "Broad mites are invisible to naked eye; downward leaf curling is their telltale signature."
                    }
                ]
            },
            {
                "week": 9,
                "title": "First Flowering & Anthracnose Protection",
                "stage": "Flowering & Pod Formation",
                "days_range": "Day 57 - 63",
                "tasks": [
                    {
                        "category": "PEST_MONITORING",
                        "title": "Anthracnose (Die-back) Preventive Spray",
                        "frequency": "BI_WEEKLY",
                        "timing": "Day 60",
                        "description": "Check twigs for tip die-back. Apply prophylactic copper or bio-fungicide after rain spells.",
                        "beginner_tip": "Anthracnose attacks both twigs and ripening pods; prompt pruning of infected branches is vital."
                    },
                    {
                        "category": "FERTILIZING",
                        "title": "Flowering Booster (Phosphorus & Potassium)",
                        "frequency": "WEEKLY",
                        "timing": "Day 62",
                        "description": "Spray 0.2% 0:52:34 or wood ash water extract to support heavy blossom retention.",
                        "beginner_tip": "Avoid excess nitrogen at flowering, which causes flower drop and excessive soft leaves."
                    }
                ]
            },
            {
                "week": 11,
                "title": "First Green Chilli Picking",
                "stage": "Multi-Flush Harvesting",
                "days_range": "Day 71 - 77",
                "tasks": [
                    {
                        "category": "HARVESTING",
                        "title": "Harvest Mature Firm Green Pods",
                        "frequency": "WEEKLY",
                        "timing": "Morning",
                        "description": "Snap firm green chillies with intact stalks. Leave small immature pods for next round.",
                        "beginner_tip": "Picking with pedicel (stalk) intact preserves pod freshness for up to 10 days in storage."
                    },
                    {
                        "category": "FERTILIZING",
                        "title": "Post-Harvest Recovery Fertilizer",
                        "frequency": "WEEKLY",
                        "timing": "After picking flush",
                        "description": "Apply split top dressing of nitrogen and potassium to trigger the next flowering wave.",
                        "beginner_tip": "Chilli is a continuous multi-flush crop; feeding after each pick ensures sustained yield."
                    }
                ]
            }
        ]
    elif crop_name == "Carrot":
        weeks_data = [
            {
                "week": 1,
                "title": "Deep Tilth Bed Preparation & Direct Sowing",
                "stage": "Fine Tilth Land Preparation",
                "days_range": "Day 1 - 7",
                "tasks": [
                    {
                        "category": "LAND_PREPARATION",
                        "title": "Deep Plowing & Stone Removal",
                        "frequency": "ONCE",
                        "timing": "Day 1 - 3",
                        "description": "Till soil 30 cm deep to a fine tilth. Remove all stones, clods, and un-rotted debris.",
                        "beginner_tip": "Stones or hard pans cause carrot roots to fork and deform, ruining marketability."
                    },
                    {
                        "category": "PLANTING",
                        "title": "Precision Line Sowing on Raised Beds",
                        "frequency": "ONCE",
                        "timing": "Day 4 - 5",
                        "description": "Sow in shallow furrows 1-1.5 cm deep, spaced 15 cm between rows. Mix tiny seeds with dry sand for even distribution.",
                        "beginner_tip": "Do not bury seeds deeper than 1.5 cm. Carrot seeds have low food reserves and fail to emerge if buried deep."
                    },
                    {
                        "category": "IRRIGATION",
                        "title": "Light Daily Misting Irrigation",
                        "frequency": "DAILY",
                        "timing": "Morning & Afternoon",
                        "description": "Keep bed surface constantly damp until germination without creating pooling or puddles.",
                        "beginner_tip": "Surface drying during the 7-10 day germination window kills delicate sprouting seeds."
                    }
                ]
            },
            {
                "week": 3,
                "title": "Germination & First Thinning",
                "stage": "Seedling Thinning & Weeding",
                "days_range": "Day 15 - 21",
                "tasks": [
                    {
                        "category": "PRUNING",
                        "title": "First Seedling Thinning & Hand Weeding",
                        "frequency": "ONCE",
                        "timing": "Day 18",
                        "description": "Thin seedlings to 3 cm apart. Carefully hand-pull small weeds along rows.",
                        "beginner_tip": "Thin early! Crowded carrot seedlings compete fiercely and never develop thick taproots."
                    }
                ]
            },
            {
                "week": 5,
                "title": "Final Thinning & Earthing Up",
                "stage": "Seedling Thinning & Weeding",
                "days_range": "Day 29 - 35",
                "tasks": [
                    {
                        "category": "PRUNING",
                        "title": "Final Thinning to 5 cm Spacing",
                        "frequency": "ONCE",
                        "timing": "Day 30",
                        "description": "Thin to final 5-6 cm intra-row spacing. Earth up soil around remaining crowns.",
                        "beginner_tip": "Cover exposed crown shoulders with soil to prevent solar greening (chlorophyll buildup)."
                    },
                    {
                        "category": "FERTILIZING",
                        "title": "Potassium-Rich Top Dressing",
                        "frequency": "ONCE",
                        "timing": "Day 32",
                        "description": "Apply 40 kg MOP / acre side-dressed in inter-row furrows. Water in well.",
                        "beginner_tip": "Potassium directly stimulates root expansion and natural carotene sugar development."
                    }
                ]
            },
            {
                "week": 8,
                "title": "Root Swelling & Blight Inspection",
                "stage": "Root Swelling & Foliage Care",
                "days_range": "Day 50 - 56",
                "tasks": [
                    {
                        "category": "PEST_MONITORING",
                        "title": "Scout for Alternaria Leaf Blight",
                        "frequency": "WEEKLY",
                        "timing": "Morning",
                        "description": "Examine foliage for dark brown lesions on leaf margins. Apply protective bio-fungicide or copper spray.",
                        "beginner_tip": "Healthy green foliage is required for strong root photosynthesis. Protect leaves until harvest."
                    },
                    {
                        "category": "IRRIGATION",
                        "title": "Consistent Moisture — Prevent Root Cracking",
                        "frequency": "DAILY",
                        "timing": "Morning",
                        "description": "Irrigate regularly to maintain uniform moisture throughout the 30 cm soil profile.",
                        "beginner_tip": "Heavy water after a dry dry spell causes roots to crack and split down the center."
                    }
                ]
            },
            {
                "week": 12,
                "title": "Taproot Maturity & Harvesting",
                "stage": "Maturity & Lifting Harvest",
                "days_range": "Day 78 - 84",
                "tasks": [
                    {
                        "category": "HARVESTING",
                        "title": "Harvest Mature Crisp Carrots",
                        "frequency": "WEEKLY",
                        "timing": "Early Morning in moist soil",
                        "description": "Water soil lightly the previous evening. Gently loosen soil with a garden fork and pull roots by the crown base.",
                        "beginner_tip": "Never yank dry soil by leaves alone, as foliage snaps off leaving roots trapped underground."
                    },
                    {
                        "category": "HARVESTING",
                        "title": "Washing, Sorting & Leaf Trimming",
                        "frequency": "ONCE",
                        "timing": "Post-Harvest",
                        "description": "Wash in clean running water, trim foliage to 2 cm, and sort by straightness and size.",
                        "beginner_tip": "Trimming leaves prevents moisture from being sucked out of the taproots during storage."
                    }
                ]
            }
        ]
    else:  # Brinjal and general default
        weeks_data = [
            {
                "week": 1,
                "title": "Nursery Preparation & Sowing",
                "stage": "Nursery & Field Tillage",
                "days_range": "Day 1 - 7",
                "tasks": [
                    {
                        "category": "LAND_PREPARATION",
                        "title": "Deep Tillage & Bed Inoculation",
                        "frequency": "ONCE",
                        "timing": "Day 1 - 3",
                        "description": "Deep plough soil 25-30 cm, build 15 cm raised nursery beds, and incorporate well-rotted compost.",
                        "beginner_tip": "Healthy deep root development starts with loose, aerated soil free of hard compaction."
                    },
                    {
                        "category": "PLANTING",
                        "title": "Nursery Seed Sowing",
                        "frequency": "ONCE",
                        "timing": "Day 4 - 5",
                        "description": "Sow seeds in rows 10 cm apart. Cover with fine compost and light straw mulch.",
                        "beginner_tip": "Water with a fine rose spray twice daily until germination."
                    }
                ]
            },
            {
                "week": 4,
                "title": "Main Field Transplanting",
                "stage": "Transplanting & Establishment",
                "days_range": "Day 22 - 28",
                "tasks": [
                    {
                        "category": "PLANTING",
                        "title": "Transplant 30-Day Seedlings",
                        "frequency": "ONCE",
                        "timing": "Late Afternoon",
                        "description": "Transplant at 75 cm x 60 cm spacing. Drench root zone immediately.",
                        "beginner_tip": "Brinjal plants grow into large spreading bushes; giving adequate spacing prevents disease."
                    },
                    {
                        "category": "FERTILIZING",
                        "title": "Basal Compost & Fertilizer Application",
                        "frequency": "ONCE",
                        "timing": "Transplanting Day",
                        "description": "Apply basal NPK (50kg Urea, 120kg TSP, 40kg MOP per acre) or 8 tons farmyard manure.",
                        "beginner_tip": "Mix thoroughly with soil inside each planting pit."
                    }
                ]
            },
            {
                "week": 7,
                "title": "Shoot & Fruit Borer Prevention",
                "stage": "Vegetative & Early Shoot Care",
                "days_range": "Day 43 - 49",
                "tasks": [
                    {
                        "category": "PEST_MONITORING",
                        "title": "Clip & Destroy Drooping Terminal Shoots",
                        "frequency": "BI_WEEKLY",
                        "timing": "Morning",
                        "description": "Inspect plants for wilted shoots caused by borer larvae. Cut 2 cm below wilted area and submerge in soapy water.",
                        "beginner_tip": "Regular shoot clipping breaks the borer life cycle without requiring heavy chemical pesticides."
                    },
                    {
                        "category": "FERTILIZING",
                        "title": "First Vegetative Top Dressing",
                        "frequency": "ONCE",
                        "timing": "Day 45",
                        "description": "Side-dress 30 kg Urea & 25 kg MOP per acre. Earth up soil around the stem.",
                        "beginner_tip": "Supports heavy branching and prepares strong nodes for flower bud development."
                    }
                ]
            },
            {
                "week": 10,
                "title": "First Glossy Fruit Harvesting",
                "stage": "Continuous Harvest Flushes",
                "days_range": "Day 64 - 70",
                "tasks": [
                    {
                        "category": "HARVESTING",
                        "title": "Harvest Immature Glossy Fruits",
                        "frequency": "BI_WEEKLY",
                        "timing": "Morning",
                        "description": "Harvest fruits when skin is glossy and smooth with a firm calyx. Cut with sharp pruners leaving 1 cm pedicel.",
                        "beginner_tip": "If fruit skin turns dull or seeds turn brown, the fruit is over-mature and bitter."
                    },
                    {
                        "category": "IRRIGATION",
                        "title": "Deep Root Zone Drenching",
                        "frequency": "DAILY",
                        "timing": "Morning",
                        "description": "Deliver 2-3 liters per plant. Maintain soil moisture throughout continuous harvest periods.",
                        "beginner_tip": "Avoid overhead watering; wet leaves invite Phomopsis fruit blight."
                    }
                ]
            }
        ]

    # If Hydroponics: augment tasks with specific hydro adjustments
    if is_hydro:
        for week in weeks_data:
            week["tasks"].append({
                "category": "FERTILIZING",
                "title": "Monitor Solution EC & pH",
                "frequency": "DAILY",
                "timing": "08:00 AM",
                "description": f"Check run-off and reservoir EC (target 1.8-2.5 mS/cm) and pH (target 5.8-6.2). Adjust with dilute nitric/phosphoric acid or fresh nutrient.",
                "beginner_tip": "pH drifting above 6.5 locks out iron and trace elements, causing upper leaf chlorosis (yellowing)."
            })
            week["tasks"].append({
                "category": "IRRIGATION",
                "title": "Flush Substrate Drip Lines",
                "frequency": "WEEKLY",
                "timing": "Day 7 of week",
                "description": "Flush drip emitters with fresh water for 5 minutes to clear mineral salt buildup in drippers.",
                "beginner_tip": "Clogged emitters create uneven plant feeding and root death in hot greenhouse conditions."
            })

    # If Organic: augment tasks with organic concoctions
    if is_organic:
        for week in weeks_data:
            week["tasks"].append({
                "category": "PEST_MONITORING",
                "title": "Prophylactic Organic Neem / Bio-Extract Spray",
                "frequency": "WEEKLY",
                "timing": "Late afternoon (04:30 PM)",
                "description": "Apply 5% Neem Seed Kernel Extract (NSKE) or Panchagavya (3%) foliar spray.",
                "beginner_tip": "Organic sprays act as repellents and must be applied before pest populations explode."
            })
            week["tasks"].append({
                "category": "FERTILIZING",
                "title": "Liquid Bio-Fertilizer / Compost Tea Soil Drench",
                "frequency": "BI_WEEKLY",
                "timing": "Morning",
                "description": "Drench root zone with fermented Jeevamrutha or vermiwash (1:10 dilution) to feed beneficial soil microbes.",
                "beginner_tip": "Microbial activity converts organic matter into readily absorbable plant nutrition."
            })

    return weeks_data


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/crops", summary="Get supported crops and methods for farming schedule")
async def get_schedule_crops():
    """Return list of crops and cultivation methods supported for the schedule generator."""
    return {
        "crops": [
            {"name_en": c["name_en"], "name_si": c["name_si"], "category": c["category"], "cycle_days": c["cycle_days"]}
            for c in CROP_PROFILES.values()
        ],
        "methods": [
            {"value": "OPEN_FIELD", "label": "Open Field Farming", "desc": "Traditional outdoor cultivation in soil beds"},
            {"value": "HYDROPONICS", "label": "Hydroponic Farming", "desc": "Controlled environment in cocopeat/rockwool slabs"},
            {"value": "ORGANIC", "label": "Organic Farming", "desc": "Bio-fertilizers, compost, and chemical-free pest control"}
        ],
        "activity_categories": [
            {"key": "ALL", "label": "All Activities", "icon": "List"},
            {"key": "LAND_PREPARATION", "label": "Land Preparation", "icon": "Trowel"},
            {"key": "PLANTING", "label": "Planting & Sowing", "icon": "Sprout"},
            {"key": "IRRIGATION", "label": "Irrigation & Water", "icon": "Droplets"},
            {"key": "FERTILIZING", "label": "Fertilizing & Nutrition", "icon": "Sparkles"},
            {"key": "PRUNING", "label": "Pruning & Trellising", "icon": "Scissors"},
            {"key": "PEST_MONITORING", "label": "Pest & Disease Care", "icon": "Bug"},
            {"key": "HARVESTING", "label": "Harvesting & Handling", "icon": "Apple"}
        ]
    }


@router.get("", summary="Get complete daily/weekly farming schedule")
async def get_farming_schedule(
    crop: str = Query("Tomato", description="Crop name (e.g. Tomato, Chilli, Cucumber, Brinjal, Capsicum, Carrot)"),
    method: str = Query("OPEN_FIELD", description="Cultivation method: OPEN_FIELD | HYDROPONICS | ORGANIC"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD), defaults to today")
):
    """
    Generate a full daily and weekly cultivation schedule with chronological dates,
    detailed tasks, routine checklists, and beginner advice.
    """
    # Clean crop name
    matched_key = None
    clean_input = crop.strip().lower()
    for key in CROP_PROFILES:
        if key.lower() == clean_input or clean_input in key.lower():
            matched_key = key
            break

    if not matched_key:
        matched_key = "Tomato"

    profile = CROP_PROFILES[matched_key]
    method_normalized = method.strip().upper()
    if method_normalized not in ["OPEN_FIELD", "HYDROPONICS", "ORGANIC"]:
        method_normalized = "OPEN_FIELD"

    # Parse start date
    try:
        if start_date:
            base_date = datetime.strptime(start_date.split("T")[0], "%Y-%m-%d").date()
        else:
            base_date = datetime.now().date()
    except Exception:
        base_date = datetime.now().date()

    total_days = profile["cycle_days"]
    harvest_start_day = int(total_days * 0.65)
    harvest_date = base_date + timedelta(days=harvest_start_day)
    final_date = base_date + timedelta(days=total_days)

    # Compute stages with actual dates
    computed_stages = []
    for s in profile["stages"]:
        s_date = base_date + timedelta(days=s["start_day"])
        e_date = base_date + timedelta(days=min(s["end_day"], total_days))
        computed_stages.append({
            "name": s["name"],
            "start_day": s["start_day"],
            "end_day": s["end_day"],
            "start_date": s_date.isoformat(),
            "end_date": e_date.isoformat(),
            "date_range": f"{s_date.strftime('%b %d')} – {e_date.strftime('%b %d')}",
            "description": s["description"]
        })

    # Generate weeks with real dates
    raw_weeks = _generate_weekly_tasks(matched_key, method_normalized)
    weeks_schedule = []

    for w in raw_weeks:
        w_start_day = (w["week"] - 1) * 7
        w_end_day = min(w_start_day + 6, total_days)
        w_start_date = base_date + timedelta(days=w_start_day)
        w_end_date = base_date + timedelta(days=w_end_day)

        # Assign unique IDs and dates to each task
        enriched_tasks = []
        for idx, t in enumerate(w["tasks"]):
            enriched_tasks.append({
                "id": f"{matched_key.lower()}-{method_normalized.lower()}-w{w['week']}-t{idx+1}",
                "category": t["category"],
                "title": t["title"],
                "frequency": t["frequency"],
                "timing": t["timing"],
                "description": t["description"],
                "beginner_tip": t["beginner_tip"],
                "is_critical": t["frequency"] in ["DAILY", "ONCE"],
            })

        weeks_schedule.append({
            "week_number": w["week"],
            "title": w["title"],
            "stage": w["stage"],
            "start_day": w_start_day,
            "end_day": w_end_day,
            "start_date": w_start_date.isoformat(),
            "end_date": w_end_date.isoformat(),
            "calendar_range": f"{w_start_date.strftime('%b %d, %Y')} – {w_end_date.strftime('%b %d, %Y')}",
            "tasks": enriched_tasks
        })

    return {
        "crop": {
            "name_en": profile["name_en"],
            "name_si": profile["name_si"],
            "category": profile["category"],
            "cultivation_method": method_normalized,
            "total_cycle_days": total_days,
            "pests_and_diseases": profile["pests_diseases"]
        },
        "timeline": {
            "start_date": base_date.isoformat(),
            "first_harvest_date": harvest_date.isoformat(),
            "final_harvest_date": final_date.isoformat(),
            "duration_weeks": len(weeks_schedule),
            "formatted_cycle": f"{base_date.strftime('%b %d, %Y')} to {final_date.strftime('%b %d, %Y')}"
        },
        "growth_stages": computed_stages,
        "daily_routine": profile["daily_routine"],
        "weekly_schedule": weeks_schedule,
        "total_tasks_count": sum(len(w["tasks"]) for w in weeks_schedule)
    }
