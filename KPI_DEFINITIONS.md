# MacroOps AI — Core Operational KPI Specifications

**Platform:** MacroOps AI — Fulfillment & Operations Intelligence Platform  
**Document Version:** 1.0  
**Phase:** Metrics Standardization & Semantic Definitions  
**Database Source:** [`macroops_analytics.db`](file:///c:/Users/HP/Desktop/MacroOps/macroops_analytics.db)  
**Execution Context:** Synthetic Operational Prototype Baseline  
**Date:** September 28, 2026  

---

## 1. Executive Metric Summary

This document standardizes the 15 core operational Key Performance Indicators (KPIs) for the MacroOps AI platform. For each metric, the mathematical formula, source dataset, source columns, filtering assumptions, and verified prototype baseline values are specified.

| Metric Name | Prototype Baseline | Target Benchmark | Source View / Table | Operational Category |
| :--- | :---: | :---: | :--- | :--- |
| **1. Total Orders** | **100,000** | — | `v_all_orders` | Order Volume |
| **2. Completed Orders** | **97,449 (97.45%)** | $\ge 98.5\%$ | `v_completed_orders` | Fulfillment Delivery |
| **3. Cancelled Orders** | **1,795 (1.79%)** | $< 1.0\%$ | `v_exception_orders` | Order Churn |
| **4. Failed Orders** | **756 (0.76%)** | $< 0.5\%$ | `v_exception_orders` | Drop-off Failure |
| **5. SLA Breach Rate** | **89.68%** | $< 5.0\%$ | `v_completed_orders` | SLA Compliance |
| **6. On-Time Delivery Rate (OTD)** | **10.32%** | $\ge 95.0\%$ | `v_completed_orders` | SLA Compliance |
| **7. Average Delivery Delay** | **6.43 mins** | $< 1.0\text{ min}$ | `v_completed_orders` | Delivery Speed |
| **8. Average Picking Duration** | **13.03 mins** | $< 8.0\text{ mins}$ | `v_picking_performance` | Warehouse Velocity |
| **9. Picking Exception Rate** | **11.68%** | $< 2.0\%$ | `v_picking_performance` | Fulfillment Accuracy |
| **10. Average Assignment Delay** | **8.17 mins** | $< 3.0\text{ mins}$ | `v_delivery_performance` | Dispatch Efficiency |
| **11. Average Delivery Distance** | **3.51 km** | $2.0 - 4.0\text{ km}$ | `v_delivery_performance` | Last-Mile Radius |
| **12. Average Transit Time** | **18.95 mins** (Eff.) | $< 15.0\text{ mins}$ | `v_full_lifecycle_orders` | Courier Speed |
| **13. Inventory Accuracy** | **89.42%** | $\ge 98.0\%$ | `v_store_inventory` | Catalog Health |
| **14. Stockout Rate** | **0.0075%** | $< 1.0\%$ | `v_store_inventory` | Product Availability |
| **15. Workforce Task Completion Rate**| **88.93%** | $\ge 95.0\%$ | `v_workforce_performance` | Labor Capacity |
| **16. Workforce Backlog Rate** | **11.07%** | $< 5.0\%$ | `v_workforce_performance` | Labor Backlog |

---

## 2. Detailed KPI Specifications

---

### KPI 1: Total Orders
- **Business Description:** Total gross volume of customer checkout transactions initiated across all dark stores during the reporting window.
- **Formula:**
  $$\text{Total Orders} = \text{COUNT}(\text{order\_id})$$
- **Source Dataset:** `raw_orders` / `v_all_orders`
- **Source Columns:** `order_id`
- **Filtering Assumptions:** None (Unfiltered macro transaction count across all order states).
- **Prototype Baseline:** **100,000 orders** across 100 stores in September 2026.

---

### KPI 2: Completed Orders
- **Business Description:** Total volume of orders that successfully reached customer delivery drop-off.
- **Formula:**
  $$\text{Completed Orders} = \sum [\text{status} \in (\text{'Delivered\_On\_Time'}, \text{'Delivered\_Late'})]$$
- **Source Dataset:** `v_completed_orders` (derived from `raw_orders`)
- **Source Columns:** `status`
- **Filtering Assumptions:** Excludes `status IN ('Cancelled', 'Failed')`.
- **Prototype Baseline:** **97,449 orders (97.45%)**.

---

### KPI 3: Cancelled Orders (Cancellation Rate)
- **Business Description:** Customer- or merchant-initiated order terminations prior to successful delivery drop-off.
- **Formula:**
  $$\text{Cancellation Rate (\%)} = \frac{\text{COUNT}(\text{status} = \text{'Cancelled'})}{\text{Total Orders}} \times 100$$
- **Source Dataset:** `v_exception_orders` / `v_all_orders`
- **Source Columns:** `status`
- **Filtering Assumptions:** All records where `status = 'Cancelled'`.
- **Prototype Baseline:** **1,795 orders (1.79%)**.

---

### KPI 4: Failed Orders (Failure Rate)
- **Business Description:** Orders where delivery couriers were unable to complete customer drop-off (e.g. customer unavailable, wrong address, rejected package).
- **Formula:**
  $$\text{Failure Rate (\%)} = \frac{\text{COUNT}(\text{status} = \text{'Failed'})}{\text{Total Orders}} \times 100$$
- **Source Dataset:** `v_exception_orders` / `v_all_orders`
- **Source Columns:** `status`
- **Filtering Assumptions:** All records where `status = 'Failed'`.
- **Prototype Baseline:** **756 orders (0.76%)**.

---

### KPI 5: SLA Breach Rate
- **Business Description:** Percentage of delivered customer orders that exceeded the promised delivery SLA commitment.
- **Formula:**
  $$\text{SLA Breach Rate (\%)} = \frac{\text{COUNT}(\text{status} = \text{'Delivered\_Late'})}{\text{COUNT}(\text{status} \in (\text{'Delivered\_On\_Time'}, \text{'Delivered\_Late'}))} \times 100$$
- **Source Dataset:** `v_completed_orders`
- **Source Columns:** `status`, `sla_breached`, `actual_delivery_time`, `promised_time`
- **Filtering Assumptions:**
  - Evaluated **strictly across Completed Orders (97,449)**.
  - Cancelled and Failed orders are excluded to prevent synthetic delay distortion.
- **Prototype Baseline:** **89.68%** (87,392 late deliveries out of 97,449 completed).  
  *(Note: If calculated naively across all 100,000 raw rows without masking Cancelled/Failed orders, the figure is 89.67%).*

---

### KPI 6: On-Time Delivery Rate (OTD)
- **Business Description:** Percentage of customer orders delivered strictly at or before the promised delivery deadline.
- **Formula:**
  $$\text{On-Time Delivery Rate (\%)} = \frac{\text{COUNT}(\text{status} = \text{'Delivered\_On\_Time'})}{\text{COUNT}(\text{status} \in (\text{'Delivered\_On\_Time'}, \text{'Delivered\_Late'}))} \times 100 = 100\% - \text{SLA Breach Rate}$$
- **Source Dataset:** `v_completed_orders`
- **Source Columns:** `status`, `sla_breached`
- **Filtering Assumptions:** Evaluated exclusively on completed deliveries.
- **Prototype Baseline:** **10.32%** (10,057 on-time deliveries out of 97,449 completed).

---

### KPI 7: Average Delivery Delay
- **Business Description:** Average duration by which late deliveries exceeded the customer SLA promise.
- **Formula:**
  $$\text{Avg Delay (All Completed)} = \frac{1}{N_{\text{completed}}} \sum \text{delivery\_delay\_minutes}$$
  $$\text{Avg Delay (Breached Only)} = \frac{1}{N_{\text{late}}} \sum_{\text{late}} \text{delivery\_delay\_minutes}$$
- **Source Dataset:** `v_completed_orders`
- **Source Columns:** `delivery_delay_minutes`
- **Filtering Assumptions:** Filtered to completed orders.
- **Prototype Baseline:**
  - **All Completed Orders:** **6.43 minutes**
  - **Breached Orders Only:** **7.17 minutes** (Max: 37.3 mins)

---

### KPI 8: Average Picking Duration
- **Business Description:** Average elapsed time spent by dark-store pickers fulfilling customer baskets in store aisles.
- **Formula:**
  $$\text{Avg Pick Duration} = \frac{1}{N_{\text{picked}}} \sum \text{pick\_duration\_minutes} = \frac{1}{N_{\text{picked}}} \sum \left( \frac{\text{pick\_end} - \text{pick\_start}}{60} \right)$$
- **Source Dataset:** `v_picking_performance` / `raw_picking`
- **Source Columns:** `pick_start`, `pick_end`, `pick_duration_minutes`
- **Filtering Assumptions:** Evaluated across the 25,000 picked orders.
- **Prototype Baseline:** **13.03 minutes** (Median: 12.8 min, Range: 2.0 to 33.8 mins).

---

### KPI 9: Picking Exception Rate (Missing Items)
- **Business Description:** Percentage of picked orders where one or more items could not be fulfilled due to shelf stockout or inventory misplacement.
- **Formula:**
  $$\text{Picking Exception Rate (\%)} = \frac{\text{COUNT}(\text{items\_missing} > 0)}{\text{Total Picked Orders}} \times 100$$
- **Source Dataset:** `v_picking_performance` / `raw_picking`
- **Source Columns:** `items_missing`
- **Filtering Assumptions:** Evaluated across the 25,000 picked orders.
- **Prototype Baseline:** **11.68%** (2,920 orders with missing items; 3,100 total missing units).

---

### KPI 10: Average Assignment Delay
- **Business Description:** Elapsed latency from customer checkout until the dispatch algorithm assigns a delivery courier.
- **Formula:**
  $$\text{Avg Assignment Delay} = \frac{1}{N} \sum \text{assignment\_delay\_minutes} = \frac{1}{N} \sum \left( \frac{\text{assignment\_time} - \text{order\_time}}{60} \right)$$
- **Source Dataset:** `v_delivery_performance` / `raw_delivery`
- **Source Columns:** `assignment_time`, `order_time`, `assignment_delay_minutes`
- **Filtering Assumptions:** Evaluated across the 25,000 delivery runs.
- **Prototype Baseline:** **8.17 minutes** (Range: 1.5 to 21.6 mins).

---

### KPI 11: Average Delivery Distance
- **Business Description:** Mean road travel distance from the dark store to the customer drop-off location.
- **Formula:**
  $$\text{Avg Delivery Distance (km)} = \frac{1}{N} \sum \text{distance\_km}$$
- **Source Dataset:** `v_delivery_performance` / `raw_delivery`
- **Source Columns:** `distance_km`
- **Filtering Assumptions:** Evaluated across all 25,000 delivery runs.
- **Prototype Baseline:** **3.51 km** (Median: 3.22 km, Range: 0.50 to 15.00 km).

---

### KPI 12: Average Transit Time
- **Business Description:** Time elapsed while courier is traveling from store departure to customer doorstep.
- **Formula:**
  $$\text{Raw Transit Time} = \frac{\text{delivery\_time} - \text{pickup\_time}}{60}$$
  $$\text{Effective Transit Time} = \frac{\text{delivery\_time} - \max(\text{pick\_end}, \text{pickup\_time})}{60}$$
- **Source Dataset:** `v_full_lifecycle_orders`
- **Source Columns:** `pickup_time`, `pick_end`, `delivery_time`
- **Filtering Assumptions:** Evaluated across the 25,000 full-lifecycle orders. Reconciles the sequence inversion anomaly.
- **Prototype Baseline:**
  - **Raw Transit Time:** **22.30 minutes**
  - **Effective Transit Time:** **18.95 minutes**
  - **Average Courier Speed:** **9.40 km/h**

---

### KPI 13: Store Inventory Accuracy
- **Business Description:** Extent to which physical inventory counts match WMS book records across store SKUs.
- **Formula:**
  $$\text{Inventory Accuracy (\%)} = \frac{1}{N_{\text{store-SKUs}}} \sum \text{inventory\_accuracy\_pct}$$
  $$\text{where } \text{inventory\_accuracy\_pct} = 100.0\% \text{ if } (\text{physical} \ge \text{system}) \text{ else } \left( \frac{\text{physical}}{\text{system}} \times 100 \right)$$
- **Source Dataset:** `v_store_inventory` / `raw_inventory`
- **Source Columns:** `inventory_accuracy_pct`, `system_stock`, `physical_stock`
- **Filtering Assumptions:** Evaluated across all 40,000 store-SKU combinations.
- **Prototype Baseline:** **89.42%** (38,006 SKUs exhibit non-zero variance).

---

### KPI 14: Stockout Rate
- **Business Description:** Proportion of catalog SKUs in a store currently carrying zero physical stock.
- **Formula:**
  $$\text{Stockout Rate (\%)} = \frac{\text{COUNT}(\text{physical\_stock} = 0)}{\text{Total Store-SKUs}} \times 100$$
- **Source Dataset:** `v_store_inventory` / `raw_inventory`
- **Source Columns:** `physical_stock`, `stockout`
- **Filtering Assumptions:** Evaluated across all 40,000 store-SKU records.
- **Prototype Baseline:** **0.0075%** (Exactly 3 out of 40,000 SKUs have physical stockout).

---

### KPI 15: Workforce Task Completion & Backlog Rates
- **Business Description:** Operational throughput and task clearance efficiency of dark-store staffing.
- **Formula:**
  $$\text{Task Completion Rate (\%)} = \frac{\sum \text{tasks\_completed}}{\sum (\text{tasks\_completed} + \text{tasks\_pending})} \times 100$$
  $$\text{Task Backlog Rate (\%)} = \frac{\sum \text{tasks\_pending}}{\sum (\text{tasks\_completed} + \text{tasks\_pending})} \times 100$$
- **Source Dataset:** `v_workforce_performance` / `raw_workforce`
- **Source Columns:** `tasks_completed`, `tasks_pending`
- **Filtering Assumptions:** Evaluated across all 10,000 workforce shift records (100 stores, 4 shifts, 5 roles).
- **Prototype Baseline:**
  - **Tasks Completed:** **480,503 tasks (88.93%)**
  - **Tasks Pending (Backlog):** **59,828 tasks (11.07%)**
  - **Total Assigned:** 540,331 tasks across 10,000 shifts.
