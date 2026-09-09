import os
import pandas as pd
from config.supabase import supabase

# Standardize crop name mappings
CROP_NAME_MAP = {
    'Tomato': 'Tomato',
    'Chilli (Green Chilli)': 'Chilli',
    'Chilli': 'Chilli',
    'Cucumber': 'Cucumber',
    'Brinjal': 'Brinjal',
    'Capsicum': 'Capsicum',
    'Carrots': 'Carrot',
    'Carrot': 'Carrot'
}

SINHALA_NAMES = {
    'Tomato': 'තක්කාලි',
    'Chilli': 'අමු මිරිස්',
    'Cucumber': 'පිපිඤ්ඤා',
    'Brinjal': 'වම්බටු',
    'Capsicum': 'මාළු මිරිස්',
    'Carrot': 'කැරට්'
}

def clean_crop_name(name: str) -> str:
    return CROP_NAME_MAP.get(str(name).strip(), str(name).strip())

def clean_pct(val):
    if pd.isna(val):
        return 0.0
    if isinstance(val, str) and '%' in val:
        return float(val.replace('%', '').strip())
    val = float(val)
    return val * 100 if val <= 1.0 else val

def seed_agronomic_guide_and_crops():
    print("Seeding Crops & Agronomic Guides...")
    file_path = "datasets/Vegetable_Cultivation_Plain_Tables-v2.xlsx"
    df_guide = pd.read_excel(file_path, sheet_name='Agronomic Guide')

    for _, row in df_guide.iterrows():
        crop_name = clean_crop_name(row['Crop Name'])
        crop_payload = {
            "name_en": crop_name,
            "name_si": SINHALA_NAMES.get(crop_name, crop_name),
            "category": "VEGETABLE",
            "growing_period": str(row['Growing Period']),
            "growing_cycle_duration_days": 120,
            "min_soil_ph": 6.0,
            "max_soil_ph": 7.0,
            "preferred_soil_type": "Well-drained loamy soil",
            "min_temp_celsius": 20.0,
            "max_temp_celsius": 32.0,
            "pests_and_diseases": str(row.get('Pests & Diseases', '')),
            "suitable_climate": str(row.get('Suitable Climate', ''))
        }
        
        # Upsert crop by name_en
        res = supabase.table("crops").upsert(crop_payload, on_conflict="name_en").execute()

def seed_method_benchmarks():
    print("Seeding Method Benchmarks (Open Field, Hydroponics, Organic)...")
    file_path = "datasets/Vegetable_Cultivation_Plain_Tables-v2.xlsx"
    df_guide = pd.read_excel(file_path, sheet_name='Agronomic Guide')
    
    # Pre-fetch crops to get IDs
    crops_res = supabase.table("crops").select("id, name_en").execute()
    crop_id_map = {c['name_en']: c['id'] for c in crops_res.data}

    methods_config = [
        ('Open Field Farming', 'OPEN_FIELD', 'Open Field (Planting Material & Fertilizer)'),
        ('Hydroponic Farming', 'HYDROPONICS', 'Hydroponic Farming (Planting Material & Fertilizer)'),
        ('Organic Farming', 'ORGANIC', 'Organic Farming (Planting Material & Fertilizer)')
    ]

    for sheet_name, method_enum, guide_col in methods_config:
        df_method = pd.read_excel(file_path, sheet_name=sheet_name)
        for _, row in df_method.iterrows():
            crop_name = clean_crop_name(row['Crop Name'])
            crop_id = crop_id_map.get(crop_name)
            if not crop_id:
                continue

            # Extract material/fertilizer text from Agronomic Guide
            guide_row = df_guide[df_guide['Crop Name'].apply(clean_crop_name) == crop_name]
            notes = str(guide_row.iloc[0][guide_col]) if not guide_row.empty else ""

            benchmark_payload = {
                "crop_id": crop_id,
                "method_type": method_enum,
                "typical_locations": str(row['Location']),
                "avg_yield_kg_per_acre": float(row['Average Yield (kg/ac)']),
                "total_cost_rs_per_acre": float(row['Total Cost (Rs/ac)']),
                "seed_share_pct": round(clean_pct(row['Seed Share (%)']), 2),
                "labour_share_pct": round(clean_pct(row['Labour Share (%)']), 2),
                "fertilizer_share_pct": round(clean_pct(row['Fertilizer Share (%)']), 2),
                "other_share_pct": round(clean_pct(row['Other Share (%)']), 2),
                "planting_material_desc": notes[:250],
                "fertilizer_regime_desc": notes
            }

            supabase.table("cultivation_method_benchmarks").upsert(
                benchmark_payload, on_conflict="crop_id,method_type"
            ).execute()

def seed_suitability_data():
    print("Seeding District Suitability Records...")
    file_path = "datasets/Sri_Lanka_Vegetable_Cultivation_Suitability.xlsx"
    df_detail = pd.read_excel(file_path, sheet_name='Detailed Suitability')
    df_mvp = pd.read_excel(file_path, sheet_name='MVP Recommendations')

    # Create a set of recommended crop-district pairs
    mvp_set = set(zip(
        df_mvp['Vegetable'].apply(clean_crop_name),
        df_mvp['Cultivation Method'].str.upper().str.replace(' ', '_'),
        df_mvp['Recommended District'].str.strip()
    ))

    records = []
    for _, row in df_detail.iterrows():
        crop = clean_crop_name(row['Vegetable'])
        raw_method = str(row['Cultivation Method']).strip().upper()
        method_enum = "OPEN_FIELD" if "OPEN" in raw_method else ("HYDROPONICS" if "HYDRO" in raw_method else "ORGANIC")
        district = str(row['District']).strip()
        is_rec = (crop, method_enum, district) in mvp_set

        records.append({
            "crop_name": crop,
            "cultivation_method": method_enum,
            "district": district,
            "suitability_level": str(row['Suitability Level']).strip(),
            "reason_notes": str(row.get('Reason / Notes', '')),
            "is_mvp_recommended": is_rec
        })

    # Batch insert in chunks of 50
    for i in range(0, len(records), 50):
        chunk = records[i:i+50]
        supabase.table("district_crop_suitability").upsert(
            chunk, on_conflict="crop_name,cultivation_method,district"
        ).execute()

if __name__ == "__main__":
    print("Starting database population...")
    seed_agronomic_guide_and_crops()
    seed_method_benchmarks()
    seed_suitability_data()
    print("All datasets successfully loaded into Supabase!")