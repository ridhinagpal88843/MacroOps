MacroOps AI — Synthetic Operational Dataset
Generated for prototype / analytics / AI evaluation use.

TOTAL ROWS: 200,000
Orders: 100,000
Inventory: 40,000
Picking: 25,000
Delivery: 25,000
Workforce: 10,000

Primary relationships:
- orders.order_id -> picking.order_id
- orders.order_id -> delivery.order_id
- orders.store_id -> inventory.store_id / workforce.store_id
- inventory.sku_id identifies products
- picker_id and rider_id identify operational resources

Purpose:
- Business analytics and KPI dashboards
- SLA risk prediction
- Exception management
- AI Operations Copilot
- RAG / GenAI demonstrations
- UAT and GenAI evaluation

All data is synthetic and should not be treated as real company data.
