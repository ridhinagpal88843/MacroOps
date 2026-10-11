# MacroOps AI — Prototype Data Profiling & Limitations Report

**Project:** MacroOps AI — GenAI-Powered Operations Intelligence Platform  
**Document Version:** 1.0  
**Phase:** Data Preparation & Semantic Layer  
**Authoritative Reference:** [README.txt](file:///c:/Users/HP/Desktop/MacroOps/README.txt)  
**Execution Context:** Synthetic Operational Prototype Dataset (200,000 records)  
**Date:** September 28, 2026  

---

## 1. Executive Data Inventory

The MacroOps AI platform is powered by a multi-tier synthetic operational dataset modeling dark-store fulfillment, quick-commerce inventory, warehouse picking, last-mile courier dispatch, and store staffing across 100 dark stores (`ST001` to `ST100`) for the full calendar month of September 2026.

All 5 original CSV files remain **100% untouched and preserved** in the project directory:

| Dataset File | File Size (Bytes) | Row Count | Column Count | Primary Identifier | Completeness | Duplicates |
| :--- | :---: | :---: | :---: | :--- | :---: | :---: |
| [`orders.csv`](file:///c:/Users/HP/Desktop/MacroOps/orders.csv) | 12,736,693 | 100,000 | 10 | `order_id` (Unique) | 100.0% (0 Nulls) | 0 |
| [`inventory.csv`](file:///c:/Users/HP/Desktop/MacroOps/inventory.csv) | 1,253,132 | 40,000 | 7 | `(store_id, sku_id)` | 100.0% (0 Nulls) | 0 |
| [`picking.csv`](file:///c:/Users/HP/Desktop/MacroOps/picking.csv) | 1,994,296 | 25,000 | 7 | `order_id` (Unique) | 100.0% (0 Nulls) | 0 |
| [`delivery.csv`](file:///c:/Users/HP/Desktop/MacroOps/delivery.csv) | 2,979,929 | 25,000 | 7 | `order_id` (Unique) | 100.0% (0 Nulls) | 0 |
| [`workforce.csv`](file:///c:/Users/HP/Desktop/MacroOps/workforce.csv) | 393,929 | 10,000 | 6 | `(employee_id, shift, role, store)`* | 100.0% (0 Nulls) | 0 |
| **Total Platform Assets** | **19,357,979** | **200,000** | **37** | — | **100.0%** | **0** |

*\*Note: `workforce.csv` represents shift logs without a natural single-column primary key.*

---

## 2. Dataset-by-Dataset Profiling

### 2.1. `orders.csv` (Customer Transactions & SLA Log)
- **Granularity:** 1 row per customer order checkout.
- **Row Count:** 100,000 | **Column Count:** 10 | **Missing Values:** 0
- **Unique Identifier:** `order_id` (100,000 distinct values, `ORD-000001` to `ORD-100000`).

| Column Name | Inferred Type | SQLite Type | Unique Count | Classification | Domain & Range |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `order_id` | String | `TEXT` | 100,000 | Primary Identifier | Format: `ORD-XXXXXX` |
| `store_id` | String | `TEXT` | 100 | Foreign Key / Category | 100 stores (`ST001` to `ST100`) |
| `order_time` | Datetime | `TEXT` | 38,986 | Temporal (Input) | `2026-09-01 00:00:00` to `2026-09-30 23:59:00` |
| `item_count` | Integer | `INTEGER` | 17 | Numerical (Discrete) | `1` to `17` units (Mean: 5.00, Median: 5.0) |
| `order_value` | Float | `REAL` | 63,045 | Financial / Metric | `$80.00` to `$2,744.18` (Mean: $574.63) |
| `promised_time` | Timestamp | `TEXT` | 99,982 | Temporal (Target) | `2026-09-01 00:21:14` to `2026-10-01 00:36:20` |
| `actual_delivery_time` | Timestamp | `TEXT` | 100,000 | Temporal (Outcome) | `2026-09-01 00:23:44` to `2026-10-01 00:54:11` |
| `status` | String | `TEXT` | 4 | Categorical (Status) | `Delivered_Late` (87,392), `Delivered_On_Time` (10,057), `Cancelled` (1,795), `Failed` (756) |
| `sla_breached` | Integer | `INTEGER` | 2 | Binary Flag | `1`: 89,674 (89.67%), `0`: 10,326 (10.33%) |
| `delivery_delay_minutes` | Float | `REAL` | 313 | Numerical (Metric) | `0.0` to `37.3` mins (Mean: 6.43 mins) |

---

### 2.2. `inventory.csv` (Dark Store Stock Snapshot)
- **Granularity:** 1 row per store-SKU inventory audit pair.
- **Row Count:** 40,000 | **Column Count:** 7 | **Missing Values:** 0
- **Unique Identifier:** Composite Key `(store_id, sku_id)` — 40,000 unique combinations.

| Column Name | Inferred Type | SQLite Type | Unique Count | Classification | Domain & Range |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `store_id` | String | `TEXT` | 100 | Composite Key / FK | `ST001` to `ST100` |
| `sku_id` | String | `TEXT` | 500 | Composite Key / FK | `SKU0001` to `SKU0500` (400 per store) |
| `system_stock` | Integer | `INTEGER` | 49 | Numerical (WMS Book) | `14` to `62` units (Mean: 34.97) |
| `physical_stock` | Integer | `INTEGER` | 72 | Numerical (Physical) | `0` to `71` units (Mean: 35.01) |
| `stockout` | String | `TEXT` | 2 | Categorical (Flag) | `'No'` (39,997), `'Yes'` (3) |
| `stock_variance` | Integer | `INTEGER` | 37 | Numerical (Calculated)| `-18` to `+18` (physical - system) |
| `inventory_accuracy_pct` | Float | `REAL` | 404 | Percentage (Metric) | `0.0%` to `100.0%` (Mean: 89.42%) |

---

### 2.3. `picking.csv` (Warehouse Picking Operations Log)
- **Granularity:** 1 row per picked order.
- **Row Count:** 25,000 | **Column Count:** 7 | **Missing Values:** 0
- **Unique Identifier:** `order_id` (25,000 unique values).

| Column Name | Inferred Type | SQLite Type | Unique Count | Classification | Domain & Range |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `order_id` | String | `TEXT` | 25,000 | Primary Key / FK | Matches 25,000 orders in `orders.csv` |
| `picker_id` | String | `TEXT` | 1,200 | Resource Identifier | `PICK00001` to `PICK01200` |
| `pick_start` | Datetime | `TEXT` | 18,922 | Temporal (Start) | `2026-09-01 00:05:00` to `2026-10-01 00:05:00` |
| `pick_end` | Timestamp | `TEXT` | 25,000 | Temporal (End) | `2026-09-01 00:12:19` to `2026-10-01 00:17:47` |
| `items_picked` | Integer | `INTEGER` | 16 | Numerical (Metric) | `0` to `17` units (Mean: 4.86) |
| `items_missing` | Integer | `INTEGER` | 4 | Numerical (Exception) | `0` (22,080), `1` (2,748), `2` (164), `3` (8) |
| `pick_duration_minutes` | Float | `REAL` | 275 | Numerical (Duration) | `2.0` to `33.8` mins (Mean: 13.03 mins) |

---

### 2.4. `delivery.csv` (Last-Mile Courier Transit Log)
- **Granularity:** 1 row per courier delivery run.
- **Row Count:** 25,000 | **Column Count:** 7 | **Missing Values:** 0
- **Unique Identifier:** `order_id` (25,000 unique values, co-indexed with `picking.csv`).

| Column Name | Inferred Type | SQLite Type | Unique Count | Classification | Domain & Range |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `order_id` | String | `TEXT` | 25,000 | Primary Key / FK | Matches 25,000 orders in `picking.csv` |
| `rider_id` | String | `TEXT` | 1,800 | Resource Identifier | `RID00001` to `RID01800` |
| `assignment_time` | Timestamp | `TEXT` | 24,896 | Temporal (Dispatch) | `2026-09-01 00:07:36` to `2026-10-01 00:11:01` |
| `pickup_time` | Timestamp | `TEXT` | 25,000 | Temporal (Store) | `2026-09-01 00:17:35` to `2026-10-01 00:15:08` |
| `delivery_time` | Timestamp | `TEXT` | 25,000 | Temporal (Drop-off) | `2026-09-01 00:30:08` to `2026-10-01 00:52:42` |
| `distance_km` | Float | `REAL` | 1,195 | Numerical (Metric) | `0.50` to `15.00` km (Mean: 3.51 km) |
| `assignment_delay_minutes`| Float | `REAL` | 186 | Numerical (Latency) | `1.5` to `21.6` mins (Mean: 8.17 mins) |

---

### 2.5. `workforce.csv` (Shift-Level Staffing Log)
- **Granularity:** 1 row per employee shift assignment log.
- **Row Count:** 10,000 | **Column Count:** 6 | **Missing Values:** 0
- **Unique Identifier:** Surrogate Key required (contains 2,456 distinct `employee_id` values across shifts).

| Column Name | Inferred Type | SQLite Type | Unique Count | Classification | Domain & Range |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `employee_id` | String | `TEXT` | 2,456 | Staff Identifier | `EMP00001` to `EMP02500` (Repeat entries) |
| `role` | String | `TEXT` | 5 | Categorical (Role) | `Picker` (3,380), `Store Associate` (2,803), `Packer` (2,020), `Rider Coordinator` (1,036), `Supervisor` (761) |
| `store_id` | String | `TEXT` | 100 | Foreign Key / Category | `ST001` to `ST100` |
| `shift` | String | `TEXT` | 4 | Categorical (Shift) | `Evening` (3,779), `Afternoon` (2,889), `Morning` (2,130), `Night` (1,202) |
| `tasks_completed` | Integer | `INTEGER` | 51 | Numerical (Metric) | `25` to `75` tasks (Mean: 48.05) |
| `tasks_pending` | Integer | `INTEGER` | 18 | Numerical (Backlog) | `0` to `17` tasks (Mean: 5.98) |

---

## 3. Known Limitations of the Synthetic Data

To ensure the MacroOps AI prototype is built with clear architectural boundaries, the following known synthetic limitations are explicitly documented:

### 1. Partial Operational Coverage (25% Telemetry Subsampling)
- **Limitation:** Exactly **25,000 out of 100,000 orders (25.0%)** have corresponding warehouse picking (`picking.csv`) and courier transit (`delivery.csv`) logs. The remaining 75,000 orders have checkout and delivery status records only.
- **Prototype Impact:** End-to-end milestone analysis (pick duration, assignment delay, transit speed) is evaluated on the 25,000-order co-indexed cohort, while macro business metrics (total revenue, gross order volume, high-level SLA) operate across all 100,000 orders.

### 2. Disconnected Inventory Catalog (No Order-to-SKU Line Items)
- **Limitation:** `orders.csv` records aggregate basket size (`item_count`) and monetary value (`order_value`), but contains no line-item table (`order_items.csv`) referencing `inventory.sku_id`.
- **Prototype Impact:** Inventory metrics cannot be decremented dynamically per order; inventory performance is modeled as a store-level capacity and accuracy snapshot.

### 3. Decoupled Workforce Namespace (No Worker-to-Task Foreign Key)
- **Limitation:** Workforce records use `employee_id` (`EMPxxxxx`), whereas picking uses `picker_id` (`PICKxxxxx`) and delivery uses `rider_id` (`RIDxxxxx`). There is no crosswalk table. Furthermore, `workforce.csv` contains no date column.
- **Prototype Impact:** Workforce productivity cannot be linked to individual order picks or deliveries. Workforce is modeled at the **`store_id` and `shift` aggregate capacity level**.

### 4. Cross-Dataset Timestamp Noise & Sequence Inversions
- **Limitation:**
  - *Sequence Inversion:* In 61.92% of orders, `delivery.pickup_time` occurs prior to `picking.pick_end` (median delta: -1.78 min).
  - *Delivery Drop-off Divergence:* In 100% of orders, `orders.actual_delivery_time` deviates from `delivery.delivery_time` (symmetric zero-centered noise with $\sigma = 16.36$ min).
- **Prototype Impact:** Rather than treating this as data corruption, the analytical layer treats `orders.actual_delivery_time` as the authoritative system SLA ground truth, treats `delivery.pickup_time` semantically as *Rider Arrival at Store*, and derives an *effective dispatch timestamp* as $\max(\text{pick\_end}, \text{pickup\_time})$.

### 5. Synthetic Fulfillment of Terminal Cancelled/Failed Orders
- **Limitation:** All 1,795 Cancelled and 756 Failed orders have synthetic delivery drop-off timestamps and calculated delivery delays in `orders.csv`, and 631 of them have full picking and delivery runs.
- **Prototype Impact:** The analytical layer segments cancelled and failed orders into an `Exception_Cohort`, excluding them from customer delivery speed metrics while preserving them for Exception Management and Churn Analysis.
