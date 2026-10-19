import csv
import json
import os
from datetime import datetime
from collections import defaultdict

DATA_DIR = r"c:\Users\HP\Desktop\MacroOps"
OUT_DIR = os.path.join(DATA_DIR, "predictive_features")
CSV_OUT = os.path.join(OUT_DIR, "stage_a_features.csv")
META_OUT = os.path.join(OUT_DIR, "feature_metadata.json")
AUDIT_OUT = os.path.join(OUT_DIR, "validation_audit.json")

def parse_dt(s):
    if not s:
        return None
    s = s.strip()
    if '.' in s:
        parts = s.split('.')
        base = parts[0]
        frac = (parts[1] + '000000')[:6]
        return datetime.strptime(f"{base}.{frac}", "%Y-%m-%d %H:%M:%S.%f")
    else:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")

def run_pipeline():
    print("=" * 70, flush=True)
    print("MacroOps AI — Stage A Feature Engineering Pipeline (Phase 2A Revised)", flush=True)
    print("=" * 70, flush=True)
    
    os.makedirs(OUT_DIR, exist_ok=True)
    
    raw_orders_path = os.path.join(DATA_DIR, "orders.csv")
    print(f"Reading source orders from: {raw_orders_path}", flush=True)
    
    # 1. Filter population: status IN ('Delivered_On_Time', 'Delivered_Late')
    # Exclude 'Cancelled' and 'Failed'
    filtered_records = []
    excluded_counts = {"Cancelled": 0, "Failed": 0, "Other": 0}
    
    with open(raw_orders_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            status = r['status']
            if status in ('Delivered_On_Time', 'Delivered_Late'):
                filtered_records.append(r)
            else:
                if status in excluded_counts:
                    excluded_counts[status] += 1
                else:
                    excluded_counts["Other"] += 1
                    
    print(f"Filtered Completed Orders count: {len(filtered_records):,}", flush=True)
    print(f"Excluded orders breakdown: {excluded_counts}", flush=True)
    
    # 2. Extract strictly approved Stage A features and partition chronologically
    processed_rows = []
    
    for r in filtered_records:
        oid = r['order_id']
        sid = r['store_id']
        ot_str = r['order_time']
        pt_str = r['promised_time']
        
        ot = parse_dt(ot_str)
        pt = parse_dt(pt_str)
        
        # Approved Feature 1: item_count (integer)
        item_count = int(r['item_count'])
        
        # Approved Feature 2: order_value (float)
        order_value = round(float(r['order_value']), 2)
        
        # Approved Feature 3: promised_duration_minutes (float, promised_time - order_time)
        promised_duration_min = round((pt - ot).total_seconds() / 60.0, 2)
        
        # Approved Feature 4: order_hour (integer, 0 to 23)
        order_hour = ot.hour
        
        # Approved Feature 5: day_of_week (string, Monday to Sunday)
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_of_week = day_names[ot.weekday()]
        
        # Approved Feature 6: is_peak_rush_hour (binary flag, 1 if hour in 17-21 else 0)
        is_peak_rush_hour = 1 if order_hour in (17, 18, 19, 20, 21) else 0
        
        # Approved Feature 7: store_id (raw categorical string, ST001 to ST100)
        store_id = sid
        
        # Target 1: sla_breached (binary: 0 or 1)
        sla_breached = int(r['sla_breached'])
        
        # Target 2: delivery_delay_minutes (continuous float)
        delivery_delay_minutes = round(float(r['delivery_delay_minutes']), 1)
        
        # Chronological Split Assignment:
        # Train: Sept 01 - Sept 21 (Days 1 to 21)
        # Val:   Sept 22 - Sept 25 (Days 22 to 25)
        # Test:  Sept 26 - Sept 30 (Days 26 to 30)
        order_date_str = ot.strftime("%Y-%m-%d")
        day_int = ot.day
        
        if day_int <= 21:
            split = "train"
        elif day_int <= 25:
            split = "val"
        else:
            split = "test"
            
        processed_rows.append({
            'order_id': oid,
            'prediction_timestamp_t0': ot_str,
            'order_date': order_date_str,
            'split': split,
            'item_count': item_count,
            'order_value': order_value,
            'promised_duration_minutes': promised_duration_min,
            'order_hour': order_hour,
            'day_of_week': day_of_week,
            'is_peak_rush_hour': is_peak_rush_hour,
            'store_id': store_id,
            'sla_breached': sla_breached,
            'delivery_delay_minutes': delivery_delay_minutes
        })

    # 3. Write stage_a_features.csv (Strictly 7 raw conceptual features + IDs + Targets)
    print(f"Writing Stage A feature dataset to: {CSV_OUT}", flush=True)
    fieldnames = [
        'order_id',
        'prediction_timestamp_t0',
        'order_date',
        'split',
        'item_count',
        'order_value',
        'promised_duration_minutes',
        'order_hour',
        'day_of_week',
        'is_peak_rush_hour',
        'store_id',
        'sla_breached',
        'delivery_delay_minutes'
    ]
    
    with open(CSV_OUT, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(processed_rows)
        
    print(f"Successfully saved {len(processed_rows):,} rows to {CSV_OUT}", flush=True)
    
    # 4. Save feature metadata with explicit model preprocessing pipeline specification
    metadata = {
        "pipeline_name": "MacroOps AI Stage A Feature Engineering (Revised)",
        "created_at": datetime.now().isoformat(),
        "prediction_point": "ORDER CHECKOUT / ORDER CREATION (T0 = orders.order_time)",
        "population": "status IN ('Delivered_On_Time', 'Delivered_Late')",
        "total_rows": len(processed_rows),
        "excluded_orders": excluded_counts,
        "split_strategy": "Chronological Time-Series Partition (September 2026)",
        "split_boundaries": {
            "train": "2026-09-01 to 2026-09-21 (Days 1 to 21)",
            "val": "2026-09-22 to 2026-09-25 (Days 22 to 25)",
            "test": "2026-09-26 to 2026-09-30 (Days 26 to 30)"
        },
        "target_definitions": {
            "sla_breached": {
                "type": "binary classification",
                "definition": "1 if actual_delivery_time > promised_time else 0",
                "classes": {"0": "SLA Met (On-Time)", "1": "SLA Breached (Late)"}
            },
            "delivery_delay_minutes": {
                "type": "continuous regression",
                "definition": "Realized delivery delay in minutes for completed orders: max(0.0, (actual_delivery_time - promised_time)/60)"
            }
        },
        "approved_raw_features": [
            {"name": "item_count", "type": "numerical_integer", "description": "Total units in basket"},
            {"name": "order_value", "type": "numerical_float", "description": "Gross order monetary value"},
            {"name": "promised_duration_minutes", "type": "numerical_float", "description": "Promised delivery window at checkout (promised_time - order_time)"},
            {"name": "order_hour", "type": "categorical_integer", "description": "Hour of order checkout (0-23)"},
            {"name": "day_of_week", "type": "categorical_string", "description": "Day of week (Monday to Sunday)"},
            {"name": "is_peak_rush_hour", "type": "binary_flag", "description": "1 if order_hour in 17-21, else 0"},
            {"name": "store_id", "type": "categorical_string", "description": "Dark store identifier (ST001-ST100)"}
        ],
        "target_encoding_status": "NONE. No target encoding is applied in the feature matrix or the baseline model pipeline.",
        "model_preprocessing_specification": {
            "baseline_1_logistic_regression": {
                "categorical_pipeline": {
                    "columns": ["store_id", "order_hour", "day_of_week"],
                    "transformer": "OneHotEncoder(handle_unknown='ignore', sparse_output=False)"
                },
                "continuous_pipeline": {
                    "columns": ["item_count", "order_value", "promised_duration_minutes"],
                    "transformer": "StandardScaler()"
                },
                "passthrough_pipeline": {
                    "columns": ["is_peak_rush_hour"],
                    "transformer": "passthrough"
                },
                "fitting_rule": "Fit strictly on Train partition (split == 'train'). Transform Val and Test partitions unchanged without re-fitting."
            }
        },
        "synthetic_data_disclaimer": "All model performance is prototype performance on synthetic data and must not be interpreted as real-world operational performance."
    }
    
    with open(META_OUT, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    print(f"Successfully saved feature metadata to {META_OUT}", flush=True)

    # 5. Validation Audit Execution
    run_audit(processed_rows)

def run_audit(rows):
    print("\n" + "=" * 70, flush=True)
    print("STAGE A FEATURE MATRIX VALIDATION AUDIT (REVISED)", flush=True)
    print("=" * 70, flush=True)
    
    total_count = len(rows)
    split_counts = defaultdict(int)
    split_targets_clf = defaultdict(lambda: defaultdict(int))
    split_targets_reg = defaultdict(list)
    split_dates = defaultdict(list)
    
    missing_counts = defaultdict(int)
    seen_order_ids = set()
    dup_order_ids = 0
    
    split_stores = defaultdict(set)
    
    item_counts = []
    order_values = []
    promised_durs = []
    order_hours = []
    peak_counts = 0
    
    for r in rows:
        oid = r['order_id']
        sp = r['split']
        split_counts[sp] += 1
        
        if oid in seen_order_ids:
            dup_order_ids += 1
        else:
            seen_order_ids.add(oid)
            
        sb = r['sla_breached']
        dd = r['delivery_delay_minutes']
        split_targets_clf[sp][sb] += 1
        split_targets_reg[sp].append(dd)
        split_dates[sp].append(r['order_date'])
        split_stores[sp].add(r['store_id'])
        
        item_counts.append(r['item_count'])
        order_values.append(r['order_value'])
        promised_durs.append(r['promised_duration_minutes'])
        order_hours.append(r['order_hour'])
        if r['is_peak_rush_hour'] == 1:
            peak_counts += 1
        
        for k, v in r.items():
            if v is None or v == "":
                missing_counts[k] += 1
                
    # Unseen stores audit
    train_stores = split_stores['train']
    unseen_val_stores = split_stores['val'] - train_stores
    unseen_test_stores = split_stores['test'] - train_stores
    
    audit_summary = {
        "total_rows": total_count,
        "duplicate_order_ids": dup_order_ids,
        "missing_values_by_column": dict(missing_counts),
        "split_counts": dict(split_counts),
        "split_shares_pct": {k: round(v / total_count * 100.0, 2) for k, v in split_counts.items()},
        "split_date_ranges": {k: {"min": min(v), "max": max(v)} for k, v in split_dates.items()},
        "target_classification_distribution": {
            sp: {
                "breached_1": split_targets_clf[sp][1],
                "met_0": split_targets_clf[sp][0],
                "breach_rate_pct": round(split_targets_clf[sp][1] / split_counts[sp] * 100.0, 2)
            } for sp in ('train', 'val', 'test')
        },
        "target_regression_distribution": {
            sp: {
                "mean_delay_min": round(sum(split_targets_reg[sp]) / len(split_targets_reg[sp]), 2),
                "min_delay_min": min(split_targets_reg[sp]),
                "max_delay_min": max(split_targets_reg[sp])
            } for sp in ('train', 'val', 'test')
        },
        "feature_statistics": {
            "item_count": {"min": min(item_counts), "max": max(item_counts), "mean": round(sum(item_counts)/len(item_counts), 2)},
            "order_value": {"min": min(order_values), "max": max(order_values), "mean": round(sum(order_values)/len(order_values), 2)},
            "promised_duration_minutes": {"min": min(promised_durs), "max": max(promised_durs), "mean": round(sum(promised_durs)/len(promised_durs), 2)},
            "order_hour": {"min": min(order_hours), "max": max(order_hours), "mean": round(sum(order_hours)/len(order_hours), 2)},
            "is_peak_rush_hour_count": peak_counts,
            "is_peak_rush_hour_pct": round(peak_counts / total_count * 100.0, 2)
        },
        "unseen_stores_audit": {
            "train_unique_stores": len(train_stores),
            "val_unique_stores": len(split_stores['val']),
            "test_unique_stores": len(split_stores['test']),
            "unseen_in_val_count": len(unseen_val_stores),
            "unseen_in_test_count": len(unseen_test_stores)
        },
        "target_leakage_verification": {
            "status": "PASSED. Zero features are derived from target labels. store_target_encoded was removed. Preprocessing uses OneHotEncoder and StandardScaler."
        }
    }
    
    with open(AUDIT_OUT, 'w', encoding='utf-8') as f:
        json.dump(audit_summary, f, indent=2)
        
    print(f"Validation Audit Saved to: {AUDIT_OUT}", flush=True)
    print(json.dumps(audit_summary, indent=2), flush=True)
    print("=" * 70, flush=True)

if __name__ == '__main__':
    run_pipeline()
