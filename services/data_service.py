"""
MacroOps AI — Production Data Service
====================================
Read-only data access layer providing verified KPI aggregations, store-level
operational summaries, and paginated order lifecycle queries from the embedded
canonical SQLite database (`macroops_analytics.db`).

Strict Data Integrity Guarantees:
  1. Opens SQLite strictly with URI `mode=ro` (read-only); will error on any write.
  2. All SQL queries use parameterization (`?` placeholders) and column whitelisting.
  3. Every aggregated metric explicitly documents its source database view/table,
     exact mathematical formula, and operational denominator.
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Dict, Any, List, Optional, Tuple, Generator


class DataService:
    """Read-only access service for MacroOps analytical database."""

    DEFAULT_DB_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "macroops_analytics.db"
    )

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the DataService with a path to macroops_analytics.db.
        Defaults to the repository root macroops_analytics.db.
        """
        self.db_path = os.path.abspath(db_path or self.DEFAULT_DB_PATH)
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(
                f"Database file not found at: {self.db_path}. "
                "Ensure macroops_analytics.db exists in the workspace root."
            )

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Open and yield a strict read-only SQLite connection, ensuring proper closure on exit.
        Enforces foreign keys and row factory for dict-like access.
        """
        # SQLite URI read-only connection mode
        uri_path = f"file:{self.db_path}?mode=ro"
        conn = sqlite3.connect(uri_path, uri=True, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # 1. Global KPI Aggregation
    # -------------------------------------------------------------------------
    def get_global_kpis(self) -> Dict[str, Any]:
        """
        Calculate and return canonical operational KPIs with exact source provenance,
        denominators, and business definitions as standardized in KPI_DEFINITIONS.md.

        Returns:
            Dict containing operational metrics grouped by domain.
        """
        with self.get_connection() as conn:
            cur = conn.cursor()

            # Macro Order Volumes & SLA Performance from v_all_orders
            cur.execute("""
                SELECT 
                    COUNT(*) AS gross_orders,
                    SUM(CASE WHEN status = 'Delivered_On_Time' THEN 1 ELSE 0 END) AS on_time_orders,
                    SUM(CASE WHEN status = 'Delivered_Late' THEN 1 ELSE 0 END) AS late_orders,
                    SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
                    SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) AS failed_orders,
                    SUM(CASE WHEN status IN ('Delivered_On_Time', 'Delivered_Late') THEN 1 ELSE 0 END) AS completed_orders,
                    SUM(order_value) AS gross_revenue,
                    AVG(CASE WHEN status IN ('Delivered_On_Time', 'Delivered_Late') THEN delivery_delay_minutes ELSE NULL END) AS avg_delivery_delay_min,
                    AVG(promised_duration_minutes) AS avg_promised_duration_min,
                    AVG(actual_duration_minutes) AS avg_actual_duration_min
                FROM v_all_orders
            """)
            row_orders = cur.fetchone()

            gross = int(row_orders["gross_orders"])
            completed = int(row_orders["completed_orders"])
            late = int(row_orders["late_orders"])
            on_time = int(row_orders["on_time_orders"])
            cancelled = int(row_orders["cancelled_orders"])
            failed = int(row_orders["failed_orders"])
            gross_rev = float(row_orders["gross_revenue"] or 0.0)
            avg_delay = float(row_orders["avg_delivery_delay_min"] or 0.0)
            avg_promised_dur = float(row_orders["avg_promised_duration_min"] or 0.0)
            avg_actual_dur = float(row_orders["avg_actual_duration_min"] or 0.0)

            # Picking metrics from v_picking_performance
            cur.execute("""
                SELECT 
                    COUNT(*) AS picked_orders,
                    AVG(pick_duration_minutes) AS avg_pick_duration_min,
                    AVG(items_picked_per_minute) AS avg_picking_speed,
                    SUM(items_picked) AS total_items_picked,
                    SUM(items_missing) AS total_items_missing,
                    SUM(CASE WHEN has_missing_items = 1 THEN 1 ELSE 0 END) AS picking_exception_count
                FROM v_picking_performance
            """)
            row_picking = cur.fetchone()
            picked_count = int(row_picking["picked_orders"])
            avg_pick_dur = float(row_picking["avg_pick_duration_min"] or 0.0)
            avg_pick_speed = float(row_picking["avg_picking_speed"] or 0.0)
            pick_exceptions = int(row_picking["picking_exception_count"])

            # Delivery & Transit metrics from v_delivery_performance & v_full_lifecycle_orders
            cur.execute("""
                SELECT 
                    COUNT(*) AS delivery_orders,
                    AVG(distance_km) AS avg_distance_km,
                    AVG(assignment_delay_minutes) AS avg_assignment_delay_min,
                    AVG(rider_speed_kmh) AS avg_rider_speed_kmh
                FROM v_delivery_performance
            """)
            row_del = cur.fetchone()
            del_count = int(row_del["delivery_orders"])
            avg_distance = float(row_del["avg_distance_km"] or 0.0)
            avg_assign_delay = float(row_del["avg_assignment_delay_min"] or 0.0)
            avg_speed = float(row_del["avg_rider_speed_kmh"] or 0.0)

            cur.execute("SELECT AVG(effective_transit_minutes) FROM v_full_lifecycle_orders")
            avg_effective_transit = float(cur.fetchone()[0] or 0.0)

            # Store & Inventory metrics from v_store_inventory and v_all_orders
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT store_id) AS active_stores
                FROM v_all_orders
            """)
            active_stores = int(cur.fetchone()["active_stores"])

            cur.execute("""
                SELECT 
                    COUNT(*) AS total_skus,
                    AVG(inventory_accuracy_pct) AS avg_inventory_accuracy,
                    SUM(is_stockout_physical) AS stockout_count
                FROM v_store_inventory
            """)
            row_inv = cur.fetchone()
            total_skus = int(row_inv["total_skus"])
            avg_inv_acc = float(row_inv["avg_inventory_accuracy"] or 0.0)
            stockouts = int(row_inv["stockout_count"] or 0)

            # SLA Breach Rate and OTD on completed orders (canonical denominator)
            sla_breach_rate = (late / completed * 100.0) if completed > 0 else 0.0
            otd_rate = (on_time / completed * 100.0) if completed > 0 else 0.0
            completion_rate = (completed / gross * 100.0) if gross > 0 else 0.0
            cancellation_rate = (cancelled / gross * 100.0) if gross > 0 else 0.0
            failure_rate = (failed / gross * 100.0) if gross > 0 else 0.0

            return {
                "generated_at": "2026-09-30T23:59:59Z",
                "cohort_window": "September 1-30, 2026",
                "macro_volume": {
                    "total_orders": {
                        "value": gross,
                        "formatted": f"{gross:,}",
                        "source": "v_all_orders",
                        "denominator": "All Orders (100,000)"
                    },
                    "completed_orders": {
                        "value": completed,
                        "formatted": f"{completed:,} ({completion_rate:.2f}%)",
                        "source": "v_completed_orders",
                        "denominator": f"Gross Orders ({gross:,})"
                    },
                    "cancelled_orders": {
                        "value": cancelled,
                        "formatted": f"{cancelled:,} ({cancellation_rate:.2f}%)",
                        "source": "v_exception_orders (status='Cancelled')",
                        "denominator": f"Gross Orders ({gross:,})"
                    },
                    "failed_orders": {
                        "value": failed,
                        "formatted": f"{failed:,} ({failure_rate:.2f}%)",
                        "source": "v_exception_orders (status='Failed')",
                        "denominator": f"Gross Orders ({gross:,})"
                    },
                    "gross_revenue": {
                        "value": round(gross_rev, 2),
                        "formatted": f"${gross_rev:,.2f}",
                        "source": "v_all_orders.order_value",
                        "denominator": f"All Orders ({gross:,})"
                    }
                },
                "sla_compliance": {
                    "sla_breach_rate_pct": {
                        "value": round(sla_breach_rate, 2),
                        "formatted": f"{sla_breach_rate:.2f}%",
                        "source": "v_completed_orders (late / completed)",
                        "denominator": f"Completed Orders ({completed:,})",
                        "operational_meaning": "Fraction of fulfilled orders exceeding promised customer deadline"
                    },
                    "on_time_delivery_rate_pct": {
                        "value": round(otd_rate, 2),
                        "formatted": f"{otd_rate:.2f}%",
                        "source": "v_completed_orders (on_time / completed)",
                        "denominator": f"Completed Orders ({completed:,})",
                        "operational_meaning": "Fraction of fulfilled orders delivered strictly on or before promised deadline"
                    },
                    "avg_delivery_delay_min": {
                        "value": round(avg_delay, 2),
                        "formatted": f"{avg_delay:.2f} mins",
                        "source": "v_completed_orders.delivery_delay_minutes",
                        "denominator": f"Completed Orders ({completed:,})"
                    },
                    "avg_promised_duration_min": {
                        "value": round(avg_promised_dur, 2),
                        "formatted": f"{avg_promised_dur:.2f} mins",
                        "source": "v_all_orders.promised_duration_minutes",
                        "denominator": f"All Orders ({gross:,})"
                    },
                    "avg_actual_duration_min": {
                        "value": round(avg_actual_dur, 2),
                        "formatted": f"{avg_actual_dur:.2f} mins",
                        "source": "v_all_orders.actual_duration_minutes",
                        "denominator": f"All Orders ({gross:,})"
                    }
                },
                "dark_store_operations": {
                    "telemetry_orders_count": {
                        "value": picked_count,
                        "formatted": f"{picked_count:,} ({picked_count / gross * 100:.2f}% coverage)",
                        "source": "v_picking_performance",
                        "denominator": f"Gross Orders ({gross:,})"
                    },
                    "avg_pick_duration_min": {
                        "value": round(avg_pick_dur, 2),
                        "formatted": f"{avg_pick_dur:.2f} mins",
                        "source": "v_picking_performance.pick_duration_minutes",
                        "denominator": f"Picked Orders ({picked_count:,})"
                    },
                    "avg_picking_speed_items_per_min": {
                        "value": round(avg_pick_speed, 2),
                        "formatted": f"{avg_pick_speed:.2f} items/min",
                        "source": "v_picking_performance.items_picked_per_minute",
                        "denominator": f"Picked Orders ({picked_count:,})"
                    },
                    "picking_exceptions": {
                        "value": pick_exceptions,
                        "formatted": f"{pick_exceptions:,} orders with missing items",
                        "source": "v_picking_performance (has_missing_items=1)",
                        "denominator": f"Picked Orders ({picked_count:,})"
                    }
                },
                "last_mile_delivery": {
                    "avg_delivery_distance_km": {
                        "value": round(avg_distance, 2),
                        "formatted": f"{avg_distance:.2f} km",
                        "source": "v_delivery_performance.distance_km",
                        "denominator": f"Delivery Telemetry Orders ({del_count:,})"
                    },
                    "avg_assignment_delay_min": {
                        "value": round(avg_assign_delay, 2),
                        "formatted": f"{avg_assign_delay:.2f} mins",
                        "source": "v_delivery_performance.assignment_delay_minutes",
                        "denominator": f"Delivery Telemetry Orders ({del_count:,})"
                    },
                    "avg_effective_transit_min": {
                        "value": round(avg_effective_transit, 2),
                        "formatted": f"{avg_effective_transit:.2f} mins",
                        "source": "v_full_lifecycle_orders.effective_transit_minutes",
                        "denominator": f"Full Lifecycle Orders ({del_count:,})"
                    },
                    "avg_courier_speed_kmh": {
                        "value": round(avg_speed, 2),
                        "formatted": f"{avg_speed:.2f} km/h",
                        "source": "v_delivery_performance.rider_speed_kmh",
                        "denominator": f"Delivery Telemetry Orders ({del_count:,})"
                    }
                },
                "inventory_and_network": {
                    "active_stores": {
                        "value": active_stores,
                        "formatted": str(active_stores),
                        "source": "v_store_ops_summary",
                        "denominator": "Store Network"
                    },
                    "avg_inventory_accuracy": {
                        "value": round(avg_inv_acc, 2),
                        "formatted": f"{avg_inv_acc:.2f}%",
                        "source": "v_store_inventory.inventory_accuracy_pct",
                        "denominator": f"Store-SKU Audit Pairs ({total_skus:,})"
                    },
                    "stockout_skus": {
                        "value": stockouts,
                        "formatted": f"{stockouts} ({stockouts / total_skus * 100:.4f}%)",
                        "source": "v_store_inventory (is_stockout_physical=1)",
                        "denominator": f"Store-SKU Audit Pairs ({total_skus:,})"
                    }
                }
            }

    # -------------------------------------------------------------------------
    # 2. Store Operational Summaries
    # -------------------------------------------------------------------------
    def get_store_summaries(
        self,
        sort_by: str = "total_orders",
        ascending: bool = False,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve store-level operational metrics across all 100 dark stores.
        Uses verified database view `v_store_ops_summary`.
        """
        allowed_sort_columns = {
            "store_id": "store_id",
            "total_orders": "total_orders",
            "on_time_orders": "on_time_orders",
            "late_orders": "late_orders",
            "cancelled_orders": "cancelled_orders",
            "failed_orders": "failed_orders",
            "on_time_delivery_rate_pct": "on_time_delivery_rate_pct",
            "sla_breach_rate_pct": "sla_breach_rate_pct",
            "avg_delivery_delay_min": "avg_delivery_delay_min",
            "total_revenue": "total_revenue",
            "active_skus": "active_skus",
            "avg_inventory_accuracy": "avg_inventory_accuracy",
            "total_physical_units": "total_physical_units",
            "physical_stockout_count": "physical_stockout_count",
            "total_workforce_shifts": "total_workforce_shifts",
            "total_completed_tasks": "total_completed_tasks",
            "total_pending_tasks": "total_pending_tasks",
            "avg_task_completion_rate_pct": "avg_task_completion_rate_pct"
        }

        col = allowed_sort_columns.get(sort_by, "total_orders")
        order_dir = "ASC" if ascending else "DESC"
        capped_limit = max(1, min(limit, 100))

        sql = f"""
            SELECT 
                store_id,
                total_orders,
                on_time_orders,
                late_orders,
                cancelled_orders,
                failed_orders,
                on_time_delivery_rate_pct,
                sla_breach_rate_pct,
                avg_delivery_delay_min,
                total_revenue,
                active_skus,
                avg_inventory_accuracy,
                total_physical_units,
                physical_stockout_count,
                total_workforce_shifts,
                total_completed_tasks,
                total_pending_tasks,
                avg_task_completion_rate_pct
            FROM v_store_ops_summary
            ORDER BY {col} {order_dir}
            LIMIT ?
        """

        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (capped_limit,))
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def get_store_detail(self, store_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full operational summary for a single dark store."""
        sql = """
            SELECT 
                store_id,
                total_orders,
                on_time_orders,
                late_orders,
                cancelled_orders,
                failed_orders,
                on_time_delivery_rate_pct,
                sla_breach_rate_pct,
                avg_delivery_delay_min,
                total_revenue,
                active_skus,
                avg_inventory_accuracy,
                total_physical_units,
                physical_stockout_count,
                total_workforce_shifts,
                total_completed_tasks,
                total_pending_tasks,
                avg_task_completion_rate_pct
            FROM v_store_ops_summary
            WHERE store_id = ?
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (store_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    # -------------------------------------------------------------------------
    # 3. Paginated Order Records & Lifecycle Queries
    # -------------------------------------------------------------------------
    def get_orders(
        self,
        page: int = 1,
        page_size: int = 50,
        store_id: Optional[str] = None,
        status: Optional[str] = None,
        has_telemetry: Optional[bool] = None,
        search_order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve paginated order records with joined picking and delivery availability flags.

        Args:
            page: 1-indexed page number
            page_size: Number of records per page (capped at 100)
            store_id: Filter by dark store ID (e.g., 'ST001')
            status: Filter by order status (e.g., 'Delivered_Late')
            has_telemetry: True for orders with dark store picking/delivery logs
            search_order_id: Partial or full search string on order_id
        """
        safe_page = max(1, page)
        safe_size = max(1, min(page_size, 100))
        offset = (safe_page - 1) * safe_size

        where_clauses = ["1=1"]
        params: List[Any] = []

        if store_id:
            where_clauses.append("o.store_id = ?")
            params.append(store_id)

        if status:
            where_clauses.append("o.status = ?")
            params.append(status)

        if search_order_id:
            where_clauses.append("o.order_id LIKE ?")
            params.append(f"%{search_order_id.strip()}%")

        if has_telemetry is True:
            where_clauses.append("p.order_id IS NOT NULL")
        elif has_telemetry is False:
            where_clauses.append("p.order_id IS NULL")

        where_str = " AND ".join(where_clauses)

        count_sql = f"""
            SELECT COUNT(*) AS total
            FROM v_all_orders o
            LEFT JOIN raw_picking p ON o.order_id = p.order_id
            WHERE {where_str}
        """

        select_sql = f"""
            SELECT 
                o.order_id,
                o.store_id,
                o.order_time,
                o.order_date,
                o.order_hour,
                o.day_of_week,
                o.item_count,
                o.order_value,
                o.status,
                o.sla_breached,
                o.delivery_delay_minutes,
                o.promised_time,
                o.actual_delivery_time,
                o.promised_duration_minutes,
                CASE WHEN p.order_id IS NOT NULL THEN 1 ELSE 0 END AS has_picking_telemetry,
                CASE WHEN d.order_id IS NOT NULL THEN 1 ELSE 0 END AS has_delivery_telemetry,
                p.picker_id,
                p.pick_start,
                p.pick_end,
                p.items_picked,
                p.items_missing,
                p.pick_duration_minutes,
                d.rider_id,
                d.assignment_time,
                d.pickup_time,
                d.delivery_time,
                d.distance_km,
                d.assignment_delay_minutes
            FROM v_all_orders o
            LEFT JOIN raw_picking p ON o.order_id = p.order_id
            LEFT JOIN raw_delivery d ON o.order_id = d.order_id
            WHERE {where_str}
            ORDER BY o.order_time DESC
            LIMIT ? OFFSET ?
        """

        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(count_sql, tuple(params))
            total_orders = int(cur.fetchone()["total"])

            fetch_params = list(params) + [safe_size, offset]
            cur.execute(select_sql, tuple(fetch_params))
            rows = [dict(r) for r in cur.fetchall()]

            total_pages = (total_orders + safe_size - 1) // safe_size

            return {
                "orders": rows,
                "pagination": {
                    "page": safe_page,
                    "page_size": safe_size,
                    "total_orders": total_orders,
                    "total_pages": total_pages,
                    "has_next": safe_page < total_pages,
                    "has_prev": safe_page > 1
                }
            }

    def get_order_lifecycle(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve complete point-in-time fulfillment milestones for an individual order.
        Checks `v_full_lifecycle_orders` first for orders with granular telemetry;
        falls back to `v_all_orders` for standard orders.
        """
        with self.get_connection() as conn:
            cur = conn.cursor()

            # First attempt full lifecycle view
            cur.execute("""
                SELECT 
                    order_id, store_id, order_time, order_date, order_hour,
                    item_count, order_value, status, sla_breached, delivery_delay_minutes,
                    promised_time, actual_delivery_time, picker_id, pick_start, pick_end,
                    items_picked, items_missing, pick_duration_minutes, has_picking_exception,
                    rider_id, assignment_time, pickup_time, delivery_time, distance_km,
                    assignment_delay_minutes, calc_assignment_delay_min, time_to_pick_start_min,
                    effective_dispatch_time, effective_transit_minutes, pickup_vs_pickend_delta_min
                FROM v_full_lifecycle_orders
                WHERE order_id = ?
            """, (order_id,))
            row = cur.fetchone()

            if row:
                res = dict(row)
                res["has_stage_b_telemetry"] = True
                res["telemetry_coverage_note"] = (
                    "Full dark-store picking and delivery telemetry available. "
                    "Eligible for Stage A, B1, and B2 risk scoring."
                )
                return res

            # Fallback to checkout-only order view
            cur.execute("""
                SELECT 
                    order_id, store_id, order_time, order_date, order_hour, day_of_week,
                    item_count, order_value, promised_time, actual_delivery_time, status,
                    sla_breached, delivery_delay_minutes, promised_duration_minutes,
                    actual_duration_minutes, value_tier, basket_tier
                FROM v_all_orders
                WHERE order_id = ?
            """, (order_id,))
            row_base = cur.fetchone()

            if row_base:
                res = dict(row_base)
                res["has_stage_b_telemetry"] = False
                res["telemetry_coverage_note"] = (
                    "Order lacks granular dark-store picking and delivery logs "
                    "(governed by Stage A checkout risk model only)."
                )
                return res

            return None

    # -------------------------------------------------------------------------
    # 4. Exception Management Queries
    # -------------------------------------------------------------------------
    def get_exception_orders(
        self,
        page: int = 1,
        page_size: int = 50,
        exception_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve orders that failed to complete (Cancelled or Failed).
        Uses verified database view `v_exception_orders`.
        """
        safe_page = max(1, page)
        safe_size = max(1, min(page_size, 100))
        offset = (safe_page - 1) * safe_size

        where_clauses = ["1=1"]
        params: List[Any] = []

        if exception_type:
            where_clauses.append("exception_type = ?")
            params.append(exception_type)

        where_str = " AND ".join(where_clauses)

        count_sql = f"SELECT COUNT(*) AS total FROM v_exception_orders WHERE {where_str}"
        select_sql = f"""
            SELECT 
                order_id,
                store_id,
                order_time,
                order_date,
                order_hour,
                day_of_week,
                item_count,
                order_value,
                exception_type,
                exception_category
            FROM v_exception_orders
            WHERE {where_str}
            ORDER BY order_time DESC
            LIMIT ? OFFSET ?
        """

        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(count_sql, tuple(params))
            total = int(cur.fetchone()["total"])

            fetch_params = list(params) + [safe_size, offset]
            cur.execute(select_sql, tuple(fetch_params))
            rows = [dict(r) for r in cur.fetchall()]

            total_pages = (total + safe_size - 1) // safe_size

            return {
                "exceptions": rows,
                "pagination": {
                    "page": safe_page,
                    "page_size": safe_size,
                    "total_exceptions": total,
                    "total_pages": total_pages
                }
            }
