# MacroOps AI — Comprehensive Data Dictionary

**Platform:** MacroOps AI — GenAI-Powered Fulfillment & Last-Mile Operations Intelligence  
**Authoritative Reference:** [README.txt](file:///c:/Users/HP/Desktop/MacroOps/README.txt)  
**Inspection Date:** September 28, 2026  
**Total Records Analyzed:** 200,000 rows across 5 CSV datasets  
**Status:** Data Understanding & Foundation Stage (Original datasets unmodified)

---

## 1. Executive Dataset Summary

| Dataset File | File Size (Bytes) | Row Count | Column Count | Primary Key Candidate | Completeness (Null %) | Full Duplicate Rows |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| [`orders.csv`](file:///c:/Users/HP/Desktop/MacroOps/orders.csv) | 12,736,693 | 100,000 | 10 | `order_id` (100% unique) | 100.0% (0.0% Null) | 0 |
| [`inventory.csv`](file:///c:/Users/HP/Desktop/MacroOps/inventory.csv) | 1,253,132 | 40,000 | 7 | `(store_id, sku_id)` Composite PK | 100.0% (0.0% Null) | 0 |
| [`picking.csv`](file:///c:/Users/HP/Desktop/MacroOps/picking.csv) | 1,994,296 | 25,000 | 7 | `order_id` (100% unique) | 100.0% (0.0% Null) | 0 |
| [`delivery.csv`](file:///c:/Users/HP/Desktop/MacroOps/delivery.csv) | 2,979,929 | 25,000 | 7 | `order_id` (100% unique) | 100.0% (0.0% Null) | 0 |
| [`workforce.csv`](file:///c:/Users/HP/Desktop/MacroOps/workforce.csv) | 393,929 | 10,000 | 6 | *None (Surrogate/Date needed)* | 100.0% (0.0% Null) | 0 |
| **Total** | **19,357,979** | **200,000** | **37** | — | **100.0% Complete** | **0** |

---

## 2. Dataset-by-Dataset Detailed Dictionary

### 2.1. `orders.csv`
- **Description:** Central transactional log containing customer order lifecycle details, promised delivery commitments, store origins, values, and SLA compliance metrics.
- **Row Count:** 100,000 rows | **Column Count:** 10 columns
- **Temporal Coverage:** September 1, 2026, 00:00:00 to September 30, 2026, 23:59:00 (1 full calendar month).

#### Column Specifications:
| Column Name | Inferred Data Type | Null Count (%) | Unique Values | Field Category | Value Range / Constraints | Description & Business Rules |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `order_id` | String (`VARCHAR(16)`) | 0 (0.0%) | 100,000 | Identifier / PK | `ORD-000001` to `ORD-100000` | Unique alphanumeric identifier for each customer order. Primary Key. |
| `store_id` | String (`VARCHAR(8)`) | 0 (0.0%) | 100 | Foreign Key / Categorical | `ST001` to `ST100` | Identifier of the fulfillment micro-warehouse / dark store handling the order. |
| `order_time` | Datetime (`YYYY-MM-DD HH:MM:SS`) | 0 (0.0%) | 38,986 | Temporal | `2026-09-01 00:00:00` to `2026-09-30 23:59:00` | Timestamp when the customer completed order checkout. |
| `item_count` | Integer | 0 (0.0%) | 17 | Numerical (Discrete) | `1` to `17` (Mean: 5.00) | Total quantity of items requested in the customer basket. |
| `order_value` | Float (`DECIMAL(10,2)`) | 0 (0.0%) | 63,045 | Numerical (Financial) | `80.00` to `2744.18` (Mean: 574.63) | Gross order transaction value in currency units. |
| `promised_time` | Datetime (`TIMESTAMP(9)`) | 0 (0.0%) | 99,982 | Temporal | `2026-09-01 00:21:14` to `2026-10-01 00:36:20` | Customer-facing SLA promised delivery deadline. Calculated by dispatch engine. |
| `actual_delivery_time` | Datetime (`TIMESTAMP(9)`) | 0 (0.0%) | 100,000 | Temporal | `2026-09-01 00:23:44` to `2026-10-01 00:54:11` | Timestamp recorded in order service when order is marked delivered. |
| `status` | String (`VARCHAR(32)`) | 0 (0.0%) | 4 | Categorical (Status) | `Delivered_Late`: 87,392 (87.39%)<br>`Delivered_On_Time`: 10,057 (10.06%)<br>`Cancelled`: 1,795 (1.80%)<br>`Failed`: 756 (0.76%) | Final order status state. Note: Massive late-delivery operational skew. |
| `sla_breached` | Integer / Boolean (`TINYINT`) | 0 (0.0%) | 2 | Categorical / Flag | `0`: 10,326 (10.33%)<br>`1`: 89,674 (89.67%) | Binary indicator (1 = SLA breached, 0 = SLA met). |
| `delivery_delay_minutes` | Float (`DECIMAL(5,1)`) | 0 (0.0%) | 313 | Numerical (Continuous) | `0.0` to `37.3` (Mean: 6.43 mins) | Minutes delayed past `promised_time`. `0.0` for on-time deliveries. |

#### Sample Records:
```csv
order_id,store_id,order_time,item_count,order_value,promised_time,actual_delivery_time,status,sla_breached,delivery_delay_minutes
ORD-000001,ST009,2026-09-11 21:50:00,6,680.14,2026-09-11 22:17:38.702397234,2026-09-11 22:16:08.464770751,Delivered_On_Time,0,0.0
ORD-000002,ST004,2026-09-25 18:55:00,8,1374.53,2026-09-25 19:30:50.628793746,2026-09-25 19:35:23.864758487,Delivered_Late,1,4.6
ORD-000003,ST050,2026-09-01 07:08:00,2,215.0,2026-09-01 07:31:20.479669758,2026-09-01 07:37:32.848029960,Delivered_Late,1,6.2
ORD-000004,ST061,2026-09-27 21:14:00,6,785.48,2026-09-27 21:48:08.201257866,2026-09-27 21:51:38.322385698,Delivered_Late,1,3.5
ORD-000005,ST087,2026-09-17 06:50:00,3,271.82,2026-09-17 07:15:13.375683624,2026-09-17 07:22:40.213745838,Delivered_Late,1,7.4
```

---

### 2.2. `inventory.csv`
- **Description:** Store-level inventory snapshot tracking stock levels, physical counts, variance, stockout state, and accuracy percentages per SKU.
- **Row Count:** 40,000 rows | **Column Count:** 7 columns
- **Temporal Coverage:** Static snapshot (No timestamps or audit dates present).

#### Column Specifications:
| Column Name | Inferred Data Type | Null Count (%) | Unique Values | Field Category | Value Range / Constraints | Description & Business Rules |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `store_id` | String (`VARCHAR(8)`) | 0 (0.0%) | 100 | Composite PK / FK | `ST001` to `ST100` | Dark store / fulfillment center identifier. |
| `sku_id` | String (`VARCHAR(10)`) | 0 (0.0%) | 500 | Composite PK / FK | `SKU0001` to `SKU0500` | Stock Keeping Unit identifier for specific product catalog items. |
| `system_stock` | Integer | 0 (0.0%) | 49 | Numerical (Discrete) | `14` to `62` (Mean: 34.97) | Book stock level recorded in the warehouse management system (WMS). |
| `physical_stock` | Integer | 0 (0.0%) | 72 | Numerical (Discrete) | `0` to `71` (Mean: 35.01) | Actual physical unit count verified during stock audit. |
| `stockout` | String (`VARCHAR(3)`) | 0 (0.0%) | 2 | Categorical (Flag) | `No`: 39,997 (99.99%)<br>`Yes`: 3 (0.01%) | Binary stockout indicator. Set to 'Yes' only when physical_stock = 0. |
| `stock_variance` | Integer | 0 (0.0%) | 37 | Numerical (Calculated) | `-18` to `+18` (Mean: +0.04) | Difference between physical and system count: `physical_stock - system_stock`. |
| `inventory_accuracy_pct` | Float (`DECIMAL(5,1)`) | 0 (0.0%) | 404 | Numerical (Percentage) | `0.0` to `100.0%` (Mean: 89.42%) | Stock accuracy ratio. 100.0% when physical >= system, else `(physical / system) * 100`. |

#### Sample Records:
```csv
store_id,sku_id,system_stock,physical_stock,stockout,stock_variance,inventory_accuracy_pct
ST020,SKU0384,40,41,No,1,100.0
ST085,SKU0405,39,42,No,3,100.0
ST062,SKU0193,33,15,No,-18,45.5
ST066,SKU0384,43,26,No,-17,60.5
ST098,SKU0206,32,41,No,9,100.0
```

---

### 2.3. `picking.csv`
- **Description:** Warehouse fulfillment log recording picking execution, assigned picker, duration, items retrieved, and missing item exceptions.
- **Row Count:** 25,000 rows | **Column Count:** 7 columns
- **Temporal Coverage:** September 1, 2026, 00:05:00 to October 1, 2026, 00:17:47.

#### Column Specifications:
| Column Name | Inferred Data Type | Null Count (%) | Unique Values | Field Category | Value Range / Constraints | Description & Business Rules |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `order_id` | String (`VARCHAR(16)`) | 0 (0.0%) | 25,000 | Identifier / PK / FK | `ORD-000001` ... | Order identifier. 1:1 candidate PK for picking; references `orders.order_id`. |
| `picker_id` | String (`VARCHAR(10)`) | 0 (0.0%) | 1,200 | Foreign Key / Categorical | `PICK00001` to `PICK01200` | Operational identifier of warehouse picker executing the pick list. |
| `pick_start` | Datetime (`YYYY-MM-DD HH:MM:SS`) | 0 (0.0%) | 18,922 | Temporal | `2026-09-01 00:05:00` to `2026-10-01 00:05:00` | Timestamp when picker begins retrieving items from dark store bins. |
| `pick_end` | Datetime (`TIMESTAMP(9)`) | 0 (0.0%) | 25,000 | Temporal | `2026-09-01 00:12:19` to `2026-10-01 00:17:47` | Timestamp when picker deposits picked items at packing/staging station. |
| `items_picked` | Integer | 0 (0.0%) | 16 | Numerical (Discrete) | `0` to `17` (Mean: 4.86) | Total items successfully retrieved and placed in basket. |
| `items_missing` | Integer | 0 (0.0%) | 4 | Numerical (Discrete) | `0`: 22,080 (88.32%)<br>`1`: 2,748 (10.99%)<br>`2`: 164 (0.66%)<br>`3`: 8 (0.03%) | Items unfulfilled due to bin stockout or misplacement (2,920 exceptions). |
| `pick_duration_minutes` | Float (`DECIMAL(4,1)`) | 0 (0.0%) | 275 | Numerical (Continuous) | `2.0` to `33.8` (Mean: 13.03 mins) | Total elapsed pick duration: `round((pick_end - pick_start) / 60, 1)`. |

#### Sample Records:
```csv
order_id,picker_id,pick_start,pick_end,items_picked,items_missing,pick_duration_minutes
ORD-029899,PICK00500,2026-09-02 03:34:00,2026-09-02 03:42:22.542371724,5,0,8.4
ORD-062514,PICK00982,2026-09-09 13:14:00,2026-09-09 13:33:59.251370412,11,1,20.0
ORD-022321,PICK00250,2026-09-30 03:50:00,2026-09-30 03:56:09.443139690,4,0,6.2
ORD-006008,PICK00938,2026-09-04 17:11:00,2026-09-04 17:16:15.984159870,1,0,5.3
ORD-079556,PICK00249,2026-09-15 02:33:00,2026-09-15 02:39:37.742548446,4,0,6.6
```

---

### 2.4. `delivery.csv`
- **Description:** Last-mile dispatch and transit tracking log containing rider assignments, transit milestones, travel distance, and dispatch delays.
- **Row Count:** 25,000 rows | **Column Count:** 7 columns
- **Temporal Coverage:** September 1, 2026, 00:07:36 to October 1, 2026, 00:52:42.

#### Column Specifications:
| Column Name | Inferred Data Type | Null Count (%) | Unique Values | Field Category | Value Range / Constraints | Description & Business Rules |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `order_id` | String (`VARCHAR(16)`) | 0 (0.0%) | 25,000 | Identifier / PK / FK | `ORD-000001` ... | Order identifier. 1:1 candidate PK for delivery; references `orders.order_id`. |
| `rider_id` | String (`VARCHAR(10)`) | 0 (0.0%) | 1,800 | Foreign Key / Categorical | `RID00001` to `RID01800` | Fleet identifier for assigned delivery courier. |
| `assignment_time` | Datetime (`TIMESTAMP(9)`) | 0 (0.0%) | 24,896 | Temporal | `2026-09-01 00:07:36` to `2026-10-01 00:11:01` | Timestamp when routing system assigned order to rider. |
| `pickup_time` | Datetime (`TIMESTAMP(9)`) | 0 (0.0%) | 25,000 | Temporal | `2026-09-01 00:17:35` to `2026-10-01 00:15:08` | Timestamp when rider accepted/departed store with order bag. |
| `delivery_time` | Datetime (`TIMESTAMP(9)`) | 0 (0.0%) | 25,000 | Temporal | `2026-09-01 00:30:08` to `2026-10-01 00:52:42` | Timestamp recorded in rider mobile app upon customer drop-off. |
| `distance_km` | Float (`DECIMAL(5,2)`) | 0 (0.0%) | 1,195 | Numerical (Continuous) | `0.50` to `15.00` (Mean: 3.51 km) | Road travel distance between store and delivery destination. |
| `assignment_delay_minutes` | Float (`DECIMAL(4,1)`) | 0 (0.0%) | 186 | Numerical (Continuous) | `1.5` to `21.6` (Mean: 8.17 mins) | Time elapsed from `orders.order_time` to `assignment_time`. |

#### Sample Records:
```csv
order_id,rider_id,assignment_time,pickup_time,delivery_time,distance_km,assignment_delay_minutes
ORD-029899,RID00856,2026-09-02 03:40:28.858334688,2026-09-02 03:46:37.291339668,2026-09-02 04:18:05.816092992,4.1,13.5
ORD-062514,RID00695,2026-09-09 13:17:30.921443286,2026-09-09 13:27:31.965450030,2026-09-09 13:43:25.365824580,1.83,9.5
ORD-022321,RID01108,2026-09-30 03:50:30.000000000,2026-09-30 03:59:27.287834808,2026-09-30 04:26:09.436828284,3.22,4.5
ORD-006008,RID01542,2026-09-04 17:16:24.794365800,2026-09-04 17:26:31.617827364,2026-09-04 17:42:01.637218896,2.32,9.4
ORD-079556,RID00686,2026-09-15 02:35:19.432206144,2026-09-15 02:37:19.432206144,2026-09-15 02:41:43.629193368,0.5,5.3
```

---

### 2.5. `workforce.csv`
- **Description:** Shift-level operational staffing log capturing employee roles, store assignments, shifts, completed tasks, and pending backlogs.
- **Row Count:** 10,000 rows | **Column Count:** 6 columns
- **Temporal Coverage:** UNKNOWN (No date or timestamp column present).

#### Column Specifications:
| Column Name | Inferred Data Type | Null Count (%) | Unique Values | Field Category | Value Range / Constraints | Description & Business Rules |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `employee_id` | String (`VARCHAR(10)`) | 0 (0.0%) | 2,456 | Identifier (Non-unique) | `EMP00001` to `EMP02500` | Staff identifier. Not unique (employees appear across multiple shifts/stores). |
| `role` | String (`VARCHAR(32)`) | 0 (0.0%) | 5 | Categorical (Role) | `Picker`: 3,380 (33.8%)<br>`Store Associate`: 2,803 (28.0%)<br>`Packer`: 2,020 (20.2%)<br>`Rider Coordinator`: 1,036 (10.4%)<br>`Supervisor`: 761 (7.6%) | Functional duty assigned to employee during shift. |
| `store_id` | String (`VARCHAR(8)`) | 0 (0.0%) | 100 | Foreign Key / Categorical | `ST001` to `ST100` | Dark store location of the shift assignment. |
| `shift` | String (`VARCHAR(16)`) | 0 (0.0%) | 4 | Categorical (Shift) | `Evening`: 3,779 (37.8%)<br>`Afternoon`: 2,889 (28.9%)<br>`Morning`: 2,130 (21.3%)<br>`Night`: 1,202 (12.0%) | Time-of-day working window. |
| `tasks_completed` | Integer | 0 (0.0%) | 51 | Numerical (Discrete) | `25` to `75` (Mean: 48.05) | Number of operational tasks accomplished during shift. |
| `tasks_pending` | Integer | 0 (0.0%) | 18 | Numerical (Discrete) | `0` to `17` (Mean: 5.98) | Number of unresolved operational tasks remaining at shift close. |

#### Sample Records:
```csv
employee_id,role,store_id,shift,tasks_completed,tasks_pending
EMP01494,Store Associate,ST073,Afternoon,48,6
EMP01928,Picker,ST074,Evening,45,10
EMP01573,Rider Coordinator,ST058,Evening,44,8
EMP00056,Store Associate,ST069,Evening,49,8
EMP00268,Store Associate,ST055,Afternoon,53,3
```

---

## 3. Comparative Type & Granularity Matrix

| Dataset | Granularity Level | Primary Key (PK) | Foreign Keys (FK) | Date/Time Fields | Categorical Attributes | Numerical Metrics |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`orders.csv`** | 1 row per customer order | `order_id` | `store_id` | `order_time`, `promised_time`, `actual_delivery_time` | `store_id`, `status`, `sla_breached` | `item_count`, `order_value`, `delivery_delay_minutes` |
| **`inventory.csv`** | 1 row per store x SKU pair | `(store_id, sku_id)` | `store_id`, `sku_id` | *None* | `store_id`, `sku_id`, `stockout` | `system_stock`, `physical_stock`, `stock_variance`, `inventory_accuracy_pct` |
| **`picking.csv`** | 1 row per picked order | `order_id` | `order_id`, `picker_id` | `pick_start`, `pick_end` | `picker_id` | `items_picked`, `items_missing`, `pick_duration_minutes` |
| **`delivery.csv`** | 1 row per delivered order | `order_id` | `order_id`, `rider_id` | `assignment_time`, `pickup_time`, `delivery_time` | `rider_id` | `distance_km`, `assignment_delay_minutes` |
| **`workforce.csv`** | 1 row per employee shift log | *UNKNOWN (Missing surrogate/date)* | `store_id` | *None* | `role`, `store_id`, `shift` | `tasks_completed`, `tasks_pending` |
