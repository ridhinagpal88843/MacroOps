# MacroOps AI — Proposed Data Relationships & Entity Architecture

**Document Version:** 1.0  
**Phase:** Data Understanding & Foundation  
**Reference Document:** [README.txt](file:///c:/Users/HP/Desktop/MacroOps/README.txt)  
**Inspection Date:** September 28, 2026  

---

## 1. Entity-Relationship Overview

The MacroOps AI operational data model connects five core datasets across two primary business dimensions: **Fulfillment & Logistics Lifecycle (Order-Centric)** and **Store Operations & Capacity (Store-Centric)**.

```mermaid
erDiagram
    STORES ||--o{ ORDERS : "fulfills (1:N)"
    STORES ||--o{ INVENTORY : "stocks (1:N)"
    STORES ||--o{ WORKFORCE : "employs (1:N)"
    
    ORDERS ||--o| PICKING : "picked by (1:0..1)"
    ORDERS ||--o| DELIVERY : "dispatched by (1:0..1)"
    PICKING ||--|| DELIVERY : "co-indexed order subset (1:1)"

    PRODUCTS ||--o{ INVENTORY : "catalog (1:N)"

    PICKERS ||--o{ PICKING : "executes (1:N)"
    RIDERS ||--o{ DELIVERY : "delivers (1:N)"

    ORDERS {
        string order_id PK
        string store_id FK
        datetime order_time
        int item_count
        float order_value
        datetime promised_time
        datetime actual_delivery_time
        string status
        int sla_breached
        float delivery_delay_minutes
    }

    INVENTORY {
        string store_id PK_FK
        string sku_id PK_FK
        int system_stock
        int physical_stock
        string stockout
        int stock_variance
        float inventory_accuracy_pct
    }

    PICKING {
        string order_id PK_FK
        string picker_id FK
        datetime pick_start
        datetime pick_end
        int items_picked
        int items_missing
        float pick_duration_minutes
    }

    DELIVERY {
        string order_id PK_FK
        string rider_id FK
        datetime assignment_time
        datetime pickup_time
        datetime delivery_time
        float distance_km
        float assignment_delay_minutes
    }

    WORKFORCE {
        string employee_id
        string role
        string store_id FK
        string shift
        int tasks_completed
        int tasks_pending
    }
```

---

## 2. Cross-Dataset Referential Integrity & Cardinalities

### 2.1. `orders.csv` to `picking.csv`
- **Relationship:** One-to-Optional-One (`1 : 0..1`)
- **Join Key:** `orders.order_id = picking.order_id`
- **Integrity Validation:**
  - `orders.order_id` total count: **100,000**
  - `picking.order_id` total count: **25,000**
  - Set intersection: **25,000 (100.0% of picking orders exist in orders)**
  - Unmatched orders in `orders.csv`: **75,000 orders (75%) have NO picking log**
- **Business Implication:** The fulfillment picking log represents a sampled or partial operational subset (exactly 25% of orders).

---

### 2.2. `orders.csv` to `delivery.csv`
- **Relationship:** One-to-Optional-One (`1 : 0..1`)
- **Join Key:** `orders.order_id = delivery.order_id`
- **Integrity Validation:**
  - `delivery.order_id` total count: **25,000**
  - Set intersection with `orders.order_id`: **25,000 (100.0% of delivery orders exist in orders)**
  - Unmatched orders in `orders.csv`: **75,000 orders (75%) have NO delivery log**

---

### 2.3. `picking.csv` to `delivery.csv`
- **Relationship:** Exact One-to-One (`1 : 1`) across the operational subset
- **Join Key:** `picking.order_id = delivery.order_id`
- **Integrity Validation:**
  - `set(picking.order_id) == set(delivery.order_id)`: **TRUE** (100% identical 25,000 order IDs).
- **Business Implication:** Every order that was picked in this dataset also has a corresponding delivery transit record. Together, they provide end-to-end visibility for 25,000 orders.

---

### 2.4. Store Dimension Linking: `orders`, `inventory`, `workforce`
- **Relationship:** Star-schema / Hub-and-Spoke around Dark Store (`store_id`)
- **Join Key:** `store_id`
- **Integrity Validation:**
  - Unique stores in `orders.csv`: **100 (`ST001` to `ST100`)**
  - Unique stores in `inventory.csv`: **100 (`ST001` to `ST100`)**
  - Unique stores in `workforce.csv`: **100 (`ST001` to `ST100`)**
  - `set(orders.store_id) == set(inventory.store_id) == set(workforce.store_id)`: **TRUE (100% alignment)**
- **Cardinality:**
  - `stores` to `orders`: `1 : N` (Average 1,000 orders per store, Range: ~850 to 1,150)
  - `stores` to `inventory`: `1 : N` (Exactly 400 SKUs per store, totaling 40,000 store-SKU rows)
  - `stores` to `workforce`: `1 : N` (Average 100 shift records per store)

---

### 2.5. Product Catalog & Inventory Linking: `inventory.sku_id`
- **Relationship:** Catalog master to Store Inventory
- **Join Key:** `sku_id`
- **Unique Count:** 500 distinct SKUs (`SKU0001` to `SKU0500`)
- **Catalog Density:** Each store stocks exactly 400 out of the 500 catalog SKUs (80% catalog distribution per store). Total pairs: $100 \times 400 = 40,000$.
- **STATUS:** **UNKNOWN Line-Item Linkage**
  - Neither `orders.csv` nor `picking.csv` contains a `sku_id` or itemized basket breakdown.
  - There is NO `order_items.csv` or `picking_items.csv` supplied.
  - Therefore, order items **CANNOT** be traced to specific inventory SKUs directly from the supplied files. Inventory can only be aggregated and analyzed at the `store_id` level.

---

### 2.6. Workforce to Operations Linking: `employee_id` vs `picker_id` vs `rider_id`
- **Attempted Joins:**
  - `workforce.employee_id` vs `picking.picker_id`
  - `workforce.employee_id` vs `delivery.rider_id`
- **Integrity Validation:**
  - Workforce IDs: `EMP00001` to `EMP02500` (2,456 unique)
  - Picker IDs: `PICK00001` to `PICK01200` (1,200 unique)
  - Rider IDs: `RID00001` to `RID01800` (1,800 unique)
  - Direct ID Overlap: **0.0% (Zero shared values)**
- **STATUS:** **UNKNOWN / DISCONNECTED**
  - There is no mapping table (e.g. `employee_mapping.csv`) or prefix normalization provided to translate `employee_id` into `picker_id` or `rider_id`.
  - While `workforce.csv` lists `role = 'Picker'` (3,380 records) and `role = 'Rider Coordinator'` (1,036 records), they cannot be directly joined to individual order-picking or delivery runs.
  - Workforce metrics can only be correlated with operations at the **`store_id` aggregate level** or **`shift` aggregate level**.

---

## 3. Operational Event Flow & Chronological Pipeline

For the 25,000 end-to-end orders present across `orders.csv`, `picking.csv`, and `delivery.csv`, the operational timeline flows through the following theoretical pipeline:

```
[Customer Checkout] 
       │ (orders.order_time)
       ▼
[Order Assignment to Rider]
       │ (delivery.assignment_time)
       ▼
[Picking Commences]
       │ (picking.pick_start)
       ▼
[Picking Completes]
       │ (picking.pick_end)
       ▼
[Rider Pickup from Store]
       │ (delivery.pickup_time)
       ▼
[Customer Drop-Off & Delivery]
       │ (delivery.delivery_time / orders.actual_delivery_time)
       ▼
[SLA Evaluation]
         (Promised Deadline vs Actual Delivery)
```

### Data Pipeline Chronology Findings:
1. `orders.order_time <= picking.pick_start`: **100% Valid (0 errors)**. Picking always starts after the order is placed.
2. `delivery.assignment_time <= delivery.pickup_time <= delivery.delivery_time`: **100% Valid (0 errors)**. Dispatch and transit within `delivery.csv` are strictly sequential.
3. `picking.pick_end <= delivery.pickup_time`: **INCONSISTENCY DETECTED (See Quality Report)**. In 15,480 orders (61.9%), `pickup_time` precedes `pick_end`.
4. `orders.actual_delivery_time` vs `delivery.delivery_time`: **DISCREPANCY DETECTED**. Timestamps differ across all 25,000 records.

---

## 4. Established vs. Unknown Mappings Summary

| Proposed Relationship | Join Condition | Established / Confirmed? | Cardinality | Notes / Constraints |
| :--- | :--- | :--- | :--- | :--- |
| Orders to Picking | `orders.order_id = picking.order_id` | **ESTABLISHED** | `1 : 0..1` | Exact subset: 25,000 orders present in both. |
| Orders to Delivery | `orders.order_id = delivery.order_id` | **ESTABLISHED** | `1 : 0..1` | Exact subset: 25,000 orders present in both. |
| Picking to Delivery | `picking.order_id = delivery.order_id` | **ESTABLISHED** | `1 : 1` | Exact 1:1 match across 25,000 records. |
| Store to Orders | `orders.store_id = store_id` | **ESTABLISHED** | `1 : N` | 100 stores, 100% referential integrity. |
| Store to Inventory | `inventory.store_id = store_id` | **ESTABLISHED** | `1 : N` | 100 stores, 400 SKUs per store. |
| Store to Workforce | `workforce.store_id = store_id` | **ESTABLISHED** | `1 : N` | 100 stores, 100% referential integrity. |
| Orders to Inventory SKUs | `orders.sku_id = inventory.sku_id` | **UNKNOWN** | `N : M` | **Missing line-item table.** Orders only list total `item_count`. |
| Workforce to Pickers | `workforce.employee_id = picking.picker_id` | **UNKNOWN** | Unknown | Distinct ID namespaces (`EMPxxxxx` vs `PICKxxxxx`). No crosswalk table. |
| Workforce to Riders | `workforce.employee_id = delivery.rider_id` | **UNKNOWN** | Unknown | Distinct ID namespaces (`EMPxxxxx` vs `RIDxxxxx`). No crosswalk table. |
| Workforce Shift Dates | `workforce.date = orders.date` | **UNKNOWN** | Unknown | **Missing date column in workforce.csv.** Cannot join on date/time. |
