/**
 * MacroOps AI — Animated Operations Command Centre
 * Production-grade vanilla JavaScript orchestrator
 *
 * Fully integrated with Flask backend API endpoints:
 * - GET /api/health
 * - GET /api/kpis
 * - GET /api/stores
 * - GET /api/orders
 * - GET /api/order/<order_id>
 */

(function () {
  'use strict';

  // =========================================================================
  // Global State
  // =========================================================================
  const state = {
    activeTab: 'tab-overview',
    kpis: null,
    stores: [],
    orders: [],
    currentPage: 1,
    pageSize: 20,
    totalPages: 1,
    totalRecords: 0,
    filters: {
      search: '',
      storeId: '',
      status: '',
      hasTelemetry: ''
    },
    storeSortBy: 'total_orders',
    cachedValues: {},
    searchDebounceTimer: null,
    isReducedMotion: false,
    accessScenarios: [],
    complaintScenarios: [],
    batchInvestigations: []
  };

  // =========================================================================
  // DOM References
  // =========================================================================
  const dom = {
    // Nav & Utilities
    navTabs: document.querySelectorAll('.nav-tab'),
    tabPanels: document.querySelectorAll('.tab-panel'),
    btnReducedMotion: document.getElementById('btn-reduced-motion'),
    motionIcon: document.getElementById('motion-icon'),
    chipDb: document.getElementById('chip-db'),
    chipModels: document.getElementById('chip-models'),
    systemStatusText: document.getElementById('system-status-text'),

    // KPI Numbers
    kpiGrossOrders: document.getElementById('kpi-gross-orders'),
    kpiCompletedOrders: document.getElementById('kpi-completed-orders'),
    kpiBreachRate: document.getElementById('kpi-breach-rate'),
    kpiOtdRate: document.getElementById('kpi-otd-rate'),
    kpiAvgDelay: document.getElementById('kpi-avg-delay'),
    kpiPickDur: document.getElementById('kpi-pick-dur'),
    kpiTransitDur: document.getElementById('kpi-transit-dur'),
    kpiInvAcc: document.getElementById('kpi-inv-acc'),

    // Stores Table & Select
    storeSortSelect: document.getElementById('store-sort-select'),
    storeTableBody: document.getElementById('store-table-body'),
    filterStoreSelect: document.getElementById('filter-store'),

    // Order Explorer
    filterSearch: document.getElementById('filter-search'),
    filterStatus: document.getElementById('filter-status'),
    filterTelemetry: document.getElementById('filter-telemetry'),
    btnApplyFilters: document.getElementById('btn-apply-filters'),
    btnResetFilters: document.getElementById('btn-reset-filters'),
    ordersTableBody: document.getElementById('orders-table-body'),
    ordersCountLabel: document.getElementById('orders-count-label'),
    tablePaginationInfo: document.getElementById('table-pagination-info'),
    pageDisplay: document.getElementById('page-display'),
    btnPrevPage: document.getElementById('btn-prev-page'),
    btnNextPage: document.getElementById('btn-next-page'),

    // Order Intelligence Drawer / Modal
    modalBackdrop: document.getElementById('order-modal-backdrop'),
    orderDrawer: document.getElementById('order-drawer'),
    modalOrderId: document.getElementById('modal-order-id'),
    modalContentBody: document.getElementById('modal-content-body'),
    btnCloseModal: document.getElementById('btn-close-modal'),

    // Phase 03 Part 02: Access & Safety Monitor
    selectAccessScenario: document.getElementById('select-access-scenario'),
    inputAccessWeight: document.getElementById('input-access-weight'),
    inputAccessFloor: document.getElementById('input-access-floor'),
    selectAccessElevator: document.getElementById('select-access-elevator'),
    selectAccessGate: document.getElementById('select-access-gate'),
    selectAccessHazard: document.getElementById('select-access-hazard'),
    inputAccessVicinity: document.getElementById('input-access-vicinity'),
    btnEvaluateAccess: document.getElementById('btn-evaluate-access'),
    accessDecisionName: document.getElementById('access-decision-name'),
    accessDecisionReason: document.getElementById('access-decision-reason'),
    accessDoorstepSafe: document.getElementById('access-doorstep-safe'),
    accessGroundHandoff: document.getElementById('access-ground-handoff'),
    accessBriefPushed: document.getElementById('access-brief-pushed'),
    accessPenaltyProt: document.getElementById('access-penalty-prot'),
    accessActionBrief: document.getElementById('access-action-brief'),
    accessCustomerMsg: document.getElementById('access-customer-msg'),
    accessBadgeStatus: document.getElementById('access-badge-status'),

    // Phase 03 Part 02: Quality Dispute Inspector & Supplier Batches
    batchTableBody: document.getElementById('batch-table-body'),
    selectDisputeScenario: document.getElementById('select-dispute-scenario'),
    disputeEvidenceTags: document.getElementById('dispute-evidence-tags'),
    disputeSku: document.getElementById('dispute-sku'),
    disputeItem: document.getElementById('dispute-item'),
    disputeCat: document.getElementById('dispute-cat'),
    disputePrice: document.getElementById('dispute-price'),
    disputeDesc: document.getElementById('dispute-desc'),
    disputeBatch: document.getElementById('dispute-batch'),
    disputeDelayVal: document.getElementById('dispute-delay-val'),
    disputeTempVal: document.getElementById('dispute-temp-val'),
    disputeCorrVal: document.getElementById('dispute-corr-val'),
    disputeBlameVal: document.getElementById('dispute-blame-val'),
    disputeAdvisoryNote: document.getElementById('dispute-advisory-note'),
    meterThermalFill: document.getElementById('meter-thermal-fill'),
    btnSyncToAdjudication: document.getElementById('btn-sync-to-adjudication'),

    // Phase 03 Part 02: Fair Adjudication Console
    selectAdjudicationScenario: document.getElementById('select-adjudication-scenario'),
    inputAdjItemName: document.getElementById('input-adj-item-name'),
    selectAdjCategory: document.getElementById('select-adj-category'),
    inputAdjPrice: document.getElementById('input-adj-price'),
    selectAdjDefect: document.getElementById('select-adj-defect'),
    selectAdjEvidence: document.getElementById('select-adj-evidence'),
    inputAdjClaimsFreq: document.getElementById('input-adj-claims-freq'),
    inputAdjDelay: document.getElementById('input-adj-delay'),
    inputAdjTemp: document.getElementById('input-adj-temp'),
    btnEvaluateAdjudication: document.getElementById('btn-evaluate-adjudication'),
    adjActionName: document.getElementById('adj-action-name'),
    adjActionReason: document.getElementById('adj-action-reason'),
    adjPayoutAmount: document.getElementById('adj-payout-amount'),
    adjSettlementMode: document.getElementById('adj-settlement-mode'),
    adjAntibiasAudit: document.getElementById('adj-antibias-audit'),
    adjHumanReview: document.getElementById('adj-human-review'),
    adjRationaleText: document.getElementById('adj-rationale-text'),
    adjCustomerPreview: document.getElementById('adj-customer-preview'),
    adjBadgeStatus: document.getElementById('adj-badge-status')
  };

  // =========================================================================
  // Utilities & Number Formatting
  // =========================================================================
  function formatNumber(num) {
    if (num === null || num === undefined || isNaN(num)) return '0';
    return Number(num).toLocaleString('en-US');
  }

  function formatDecimal(num, decimals = 2) {
    if (num === null || num === undefined || isNaN(num)) return (0).toFixed(decimals);
    return Number(num).toFixed(decimals);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // =========================================================================
  // Kinetic Number Count-Up Animation (RAF)
  // =========================================================================
  function animateValue(element, start, end, duration, formatType) {
    if (!element) return;
    if (state.isReducedMotion) {
      applyFormattedValue(element, end, formatType);
      return;
    }

    const startTime = performance.now();

    function update(now) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Cubic ease out
      const easeOut = 1 - Math.pow(1 - progress, 3);
      const current = start + (end - start) * easeOut;

      applyFormattedValue(element, current, formatType);

      if (progress < 1) {
        requestAnimationFrame(update);
      } else {
        applyFormattedValue(element, end, formatType);
      }
    }

    requestAnimationFrame(update);
  }

  function applyFormattedValue(element, val, formatType) {
    switch (formatType) {
      case 'int':
        element.textContent = formatNumber(Math.round(val));
        break;
      case 'pct':
        element.textContent = formatDecimal(val, 2) + '%';
        break;
      case 'min':
        element.textContent = formatDecimal(val, 2) + 'm';
        break;
      default:
        element.textContent = formatDecimal(val, 2);
    }
  }

  // =========================================================================
  // Staggered Scroll Reveal Animations
  // =========================================================================
  function initRevealObserver() {
    const revealItems = document.querySelectorAll('.reveal-item');
    if ('IntersectionObserver' in window && !state.isReducedMotion) {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add('revealed');
              observer.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.1 }
      );
      revealItems.forEach((item) => observer.observe(item));
    } else {
      revealItems.forEach((item) => item.classList.add('revealed'));
    }
  }

  // =========================================================================
  // Tab Navigation
  // =========================================================================
  function switchTab(targetTabId) {
    dom.navTabs.forEach((tab) => {
      const isActive = tab.dataset.tab === targetTabId;
      tab.classList.toggle('active', isActive);
      tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    dom.tabPanels.forEach((panel) => {
      const isActive = panel.id === targetTabId;
      panel.classList.toggle('active', isActive);
      if (isActive) {
        const panelReveals = panel.querySelectorAll('.reveal-item');
        panelReveals.forEach((item) => item.classList.add('revealed'));
      }
    });

    state.activeTab = targetTabId;

    if (targetTabId === 'tab-orders' && state.orders.length === 0) {
      fetchOrders();
    }
    if (targetTabId === 'tab-access-safety' && state.accessScenarios.length === 0) {
      loadAccessScenarios();
    }
    if (targetTabId === 'tab-dispute-inspector') {
      if (state.batchInvestigations.length === 0) loadBatchInvestigations();
      if (state.complaintScenarios.length === 0) loadDisputeScenarios();
    }
    if (targetTabId === 'tab-adjudication-console') {
      if (state.complaintScenarios.length === 0) loadAdjudicationScenarios();
    }
  }

  // =========================================================================
  // API Fetcher: System Health
  // =========================================================================
  async function fetchSystemHealth() {
    try {
      const res = await fetch('/api/health');
      if (!res.ok) throw new Error('Health check failed');
      const data = await res.json();
      if (data.status === 'healthy') {
        if (dom.chipDb) dom.chipDb.className = 'status-chip chip-ready';
        if (dom.chipModels) dom.chipModels.className = 'status-chip chip-cyan';
        const thresh = data.models?.stage_a?.threshold || 0.93;
        if (dom.systemStatusText) {
          dom.systemStatusText.textContent = `OPERATIONS COMMAND CENTRE // SYNTHETIC BASELINE (τ = ${thresh.toFixed(4)})`;
        }
      }
    } catch (err) {
      console.warn('System health endpoint error:', err);
    }
  }

  // =========================================================================
  // API Fetcher: Macro KPIs
  // =========================================================================
  async function fetchKPIs() {
    try {
      const res = await fetch('/api/kpis');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const payload = await res.json();

      // Extract sections from canonical KPI schema
      const mv = payload.macro_volume || {};
      const sc = payload.sla_compliance || {};
      const ds = payload.dark_store_operations || {};
      const lm = payload.last_mile_delivery || {};
      const inv = payload.inventory_and_network || payload.inventory_and_supply || {};

      const grossOrders = mv.total_orders?.value ?? null;
      const completedOrders = mv.completed_orders?.value ?? null;
      const breachRate = sc.sla_breach_rate_pct?.value ?? null;
      const otdRate = sc.on_time_delivery_rate_pct?.value ?? null;
      const avgDelay = sc.avg_delivery_delay_min?.value ?? null;
      const avgPickDur = ds.avg_pick_duration_min?.value ?? null;
      const avgTransitDur = lm.avg_effective_transit_min?.value ?? null;
      const invAccuracy = inv.avg_inventory_accuracy?.value ?? null;

      // Noticeable, dramatic count-up duration: 1600ms
      const dur = 1600;

      // On initial load, start strictly from 0 so the user visibly watches the numbers count up
      const isInitial = !state.kpiAnimated;
      state.kpiAnimated = true;

      // Animate each metric if valid, else show error state
      if (grossOrders !== null) {
        animateValue(dom.kpiGrossOrders, isInitial ? 0 : (state.cachedValues.gross || 0), grossOrders, dur, 'int');
      } else if (dom.kpiGrossOrders) {
        dom.kpiGrossOrders.textContent = 'N/A';
      }

      if (completedOrders !== null) {
        animateValue(dom.kpiCompletedOrders, isInitial ? 0 : (state.cachedValues.completed || 0), completedOrders, dur, 'int');
      } else if (dom.kpiCompletedOrders) {
        dom.kpiCompletedOrders.textContent = 'N/A';
      }

      if (breachRate !== null) {
        animateValue(dom.kpiBreachRate, isInitial ? 0 : (state.cachedValues.breach || 0), breachRate, dur, 'pct');
      } else if (dom.kpiBreachRate) {
        dom.kpiBreachRate.textContent = 'N/A';
      }

      if (otdRate !== null) {
        animateValue(dom.kpiOtdRate, isInitial ? 0 : (state.cachedValues.otd || 0), otdRate, dur, 'pct');
      } else if (dom.kpiOtdRate) {
        dom.kpiOtdRate.textContent = 'N/A';
      }

      if (avgDelay !== null) {
        animateValue(dom.kpiAvgDelay, isInitial ? 0 : (state.cachedValues.delay || 0), avgDelay, dur, 'min');
      } else if (dom.kpiAvgDelay) {
        dom.kpiAvgDelay.textContent = 'N/A';
      }

      if (avgPickDur !== null) {
        animateValue(dom.kpiPickDur, isInitial ? 0 : (state.cachedValues.pick || 0), avgPickDur, dur, 'min');
      } else if (dom.kpiPickDur) {
        dom.kpiPickDur.textContent = 'N/A';
      }

      if (avgTransitDur !== null) {
        animateValue(dom.kpiTransitDur, isInitial ? 0 : (state.cachedValues.transit || 0), avgTransitDur, dur, 'min');
      } else if (dom.kpiTransitDur) {
        dom.kpiTransitDur.textContent = 'N/A';
      }

      if (invAccuracy !== null) {
        animateValue(dom.kpiInvAcc, isInitial ? 0 : (state.cachedValues.inv || 0), invAccuracy, dur, 'pct');
      } else if (dom.kpiInvAcc) {
        dom.kpiInvAcc.textContent = 'N/A';
      }

      state.cachedValues = {
        gross: grossOrders ?? 0,
        completed: completedOrders ?? 0,
        breach: breachRate ?? 0,
        otd: otdRate ?? 0,
        delay: avgDelay ?? 0,
        pick: avgPickDur ?? 0,
        transit: avgTransitDur ?? 0,
        inv: invAccuracy ?? 0
      };
    } catch (err) {
      console.error('Error fetching KPIs:', err);
      [dom.kpiGrossOrders, dom.kpiCompletedOrders, dom.kpiBreachRate, dom.kpiOtdRate,
       dom.kpiAvgDelay, dom.kpiPickDur, dom.kpiTransitDur, dom.kpiInvAcc].forEach((el) => {
        if (el) el.textContent = 'ERR';
      });
    }
  }

  // =========================================================================
  // API Fetcher: Dark Store Leaderboard
  // =========================================================================
  async function fetchStores() {
    try {
      const res = await fetch('/api/stores');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const payload = await res.json();
      if (!payload.stores) return;

      state.stores = payload.stores;
      populateStoreFilterSelect();
      renderStoreLeaderboard();
    } catch (err) {
      console.error('Error fetching stores:', err);
      if (dom.storeTableBody) {
        dom.storeTableBody.innerHTML = '<tr><td colspan="10" class="table-loading" style="color:var(--crimson-accent)">Failed to load store leaderboard telemetry.</td></tr>';
      }
    }
  }

  function populateStoreFilterSelect() {
    if (!dom.filterStoreSelect) return;
    const currentVal = dom.filterStoreSelect.value;
    dom.filterStoreSelect.innerHTML = '<option value="">All 100 Stores</option>';

    const sortedStores = [...state.stores].sort((a, b) => a.store_id.localeCompare(b.store_id));
    sortedStores.forEach((st) => {
      const opt = document.createElement('option');
      opt.value = st.store_id;
      opt.textContent = `${st.store_id} (${st.total_orders.toLocaleString()} orders)`;
      dom.filterStoreSelect.appendChild(opt);
    });

    if (currentVal) dom.filterStoreSelect.value = currentVal;
  }

  function renderStoreLeaderboard() {
    if (!dom.storeTableBody) return;

    const sortBy = state.storeSortBy;
    const sorted = [...state.stores].sort((a, b) => {
      const valA = a[sortBy] ?? 0;
      const valB = b[sortBy] ?? 0;
      return valB - valA;
    });

    if (sorted.length === 0) {
      dom.storeTableBody.innerHTML = '<tr><td colspan="10" class="table-loading">No dark stores registered in analytics layer.</td></tr>';
      return;
    }

    const rowsHtml = sorted
      .map((st) => {
        const breachRate = st.sla_breach_rate_pct ?? 0;
        const delay = st.avg_delivery_delay_min ?? 0;
        const accuracy = st.avg_inventory_accuracy ?? 0;
        const taskRate = st.avg_task_completion_rate_pct ?? 0;
        const onTime = st.on_time_orders ?? 0;
        const late = st.late_orders ?? 0;
        const exceptions = (st.cancelled_orders ?? 0) + (st.failed_orders ?? 0);

        const breachBar = `
          <div style="display:flex;align-items:center;gap:8px;">
            <span style="font-family:var(--font-mono);font-size:0.75rem;min-width:44px;color:${breachRate > 90 ? 'var(--crimson-accent)' : '#fff'};">
              ${breachRate.toFixed(1)}%
            </span>
            <div style="flex:1;min-width:50px;height:5px;background:rgba(255,255,255,0.08);border-radius:3px;overflow:hidden;">
              <div style="width:${Math.min(breachRate, 100)}%;height:100%;background:${breachRate > 90 ? 'var(--crimson-accent)' : 'var(--amber-accent)'};border-radius:3px;"></div>
            </div>
          </div>
        `;

        return `
          <tr data-store-id="${escapeHtml(st.store_id)}" class="store-row" title="Click to filter orders for ${escapeHtml(st.store_id)}">
            <td style="font-family:var(--font-mono);font-weight:700;color:var(--cyan-primary);">${escapeHtml(st.store_id)}</td>
            <td style="font-family:var(--font-mono);">${formatNumber(st.total_orders)}</td>
            <td style="color:var(--emerald-accent);">${formatNumber(onTime)}</td>
            <td style="color:var(--crimson-accent);">${formatNumber(late)}</td>
            <td style="color:var(--amber-accent);">${formatNumber(exceptions)}</td>
            <td>${breachBar}</td>
            <td style="font-family:var(--font-mono);">${delay.toFixed(1)}m</td>
            <td style="font-family:var(--font-mono);color:${accuracy >= 90 ? 'var(--emerald-accent)' : 'var(--amber-accent)'};">${accuracy.toFixed(1)}%</td>
            <td style="font-family:var(--font-mono);">${st.active_skus ?? '-'}</td>
            <td style="font-family:var(--font-mono);">${taskRate.toFixed(1)}%</td>
          </tr>
        `;
      })
      .join('');

    dom.storeTableBody.innerHTML = rowsHtml;

    dom.storeTableBody.querySelectorAll('.store-row').forEach((row) => {
      row.addEventListener('click', () => {
        const storeId = row.dataset.storeId;
        if (storeId) {
          if (dom.filterStoreSelect) dom.filterStoreSelect.value = storeId;
          state.filters.storeId = storeId;
          state.currentPage = 1;
          switchTab('tab-orders');
          fetchOrders();
        }
      });
    });
  }

  // =========================================================================
  // API Fetcher: Order Explorer & Multi-Stage Predictions
  // =========================================================================
  async function fetchOrders() {
    if (!dom.ordersTableBody) return;

    dom.ordersTableBody.innerHTML = '<tr><td colspan="10" class="table-loading">Querying read-only order stream...</td></tr>';
    if (dom.ordersCountLabel) dom.ordersCountLabel.textContent = 'Order Records (Searching...)';

    const params = new URLSearchParams({
      page: state.currentPage,
      page_size: state.pageSize
    });

    if (state.filters.search) params.append('search', state.filters.search);
    if (state.filters.storeId) params.append('store_id', state.filters.storeId);
    if (state.filters.status) params.append('status', state.filters.status);
    if (state.filters.hasTelemetry) params.append('has_telemetry', state.filters.hasTelemetry);

    try {
      const res = await fetch(`/api/orders?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const payload = await res.json();

      state.orders = payload.orders || [];
      const pag = payload.pagination || {};
      state.totalRecords = pag.total_orders ?? payload.total_records ?? 0;
      state.totalPages = pag.total_pages ?? payload.total_pages ?? 1;
      state.currentPage = pag.page ?? payload.page ?? 1;

      renderOrdersTable();
      updatePaginationControls();
    } catch (err) {
      console.error('Error fetching orders:', err);
      dom.ordersTableBody.innerHTML = `<tr><td colspan="10" class="table-loading" style="color:var(--crimson-accent)">Error querying orders: ${escapeHtml(err.message)}</td></tr>`;
      if (dom.ordersCountLabel) dom.ordersCountLabel.textContent = 'Order Records (Error)';
    }
  }

  function renderOrdersTable() {
    if (!dom.ordersTableBody) return;

    if (state.orders.length === 0) {
      dom.ordersTableBody.innerHTML = '<tr><td colspan="10" class="table-loading">No matching operational orders found in SQLite database.</td></tr>';
      return;
    }

    const rowsHtml = state.orders
      .map((ord) => {
        let statusBadge = '';
        if (ord.status === 'Delivered_Late') {
          statusBadge = '<span class="kpi-badge badge-crimson">LATE</span>';
        } else if (ord.status === 'Delivered_On_Time') {
          statusBadge = '<span class="kpi-badge badge-emerald">ON-TIME</span>';
        } else if (ord.status === 'Cancelled') {
          statusBadge = '<span class="kpi-badge badge-amber">CANCELLED</span>';
        } else if (ord.status === 'Failed') {
          statusBadge = '<span class="kpi-badge" style="background:rgba(168,85,247,0.2);color:#c084fc;">FAILED</span>';
        } else {
          statusBadge = `<span class="kpi-badge">${escapeHtml(ord.status || 'UNKNOWN')}</span>`;
        }

        const delayVal = ord.delivery_delay_minutes ?? ord.sla_delay_min;
        let delayText = '-';
        let delayColor = 'var(--text-dim)';
        if (delayVal !== null && delayVal !== undefined) {
          const d = Number(delayVal);
          if (d > 0) {
            delayText = `+${d.toFixed(1)}m`;
            delayColor = 'var(--crimson-accent)';
          } else {
            delayText = `${d.toFixed(1)}m`;
            delayColor = 'var(--emerald-accent)';
          }
        }

        // Stage A indicator
        const stageAScore = ord.stage_a_risk_score ?? ord.stage_a_risk?.probability;
        const isStageAAlert = ord.stage_a_alert ?? ord.stage_a_risk?.alert_triggered;
        let stageABadge = '<span class="kpi-badge">-</span>';

        if (stageAScore !== null && stageAScore !== undefined) {
          const prob = Number(stageAScore);
          if (isStageAAlert || prob >= 0.93) {
            stageABadge = `<span class="kpi-badge badge-crimson" title="Stage A Score: ${prob.toFixed(4)} (Exceeds τ=0.93)">ALERT (${(prob * 100).toFixed(1)}%)</span>`;
          } else {
            stageABadge = `<span class="kpi-badge badge-emerald" title="Stage A Score: ${prob.toFixed(4)} (Below τ=0.93)">LOW (${(prob * 100).toFixed(1)}%)</span>`;
          }
        }

        const hasTel = Boolean(ord.has_picking_telemetry);
        const telBadge = hasTel
          ? '<span class="kpi-badge badge-indigo" title="Has Picking & Dispatch logs (Stage B eligible)">T0+T1+T2</span>'
          : '<span class="kpi-badge" style="background:rgba(255,255,255,0.06);color:#94a3b8" title="Checkout only cohort (74.99%)">T0 ONLY</span>';

        return `
          <tr data-order-id="${escapeHtml(ord.order_id)}" class="order-table-row">
            <td style="font-family:var(--font-mono);font-weight:700;color:var(--cyan-primary);">${escapeHtml(ord.order_id)}</td>
            <td style="font-family:var(--font-mono);">${escapeHtml(ord.store_id)}</td>
            <td style="font-size:0.8rem;color:var(--text-muted);">${escapeHtml(ord.order_time)}</td>
            <td style="font-family:var(--font-mono);">${ord.item_count ?? ord.items_count ?? 0}</td>
            <td style="font-family:var(--font-mono);">$${formatDecimal(ord.order_value, 2)}</td>
            <td>${statusBadge}</td>
            <td style="font-family:var(--font-mono);font-weight:600;color:${delayColor};">${delayText}</td>
            <td>${stageABadge}</td>
            <td>${telBadge}</td>
            <td>
              <button class="btn btn-sm btn-secondary inspect-order-btn" data-id="${escapeHtml(ord.order_id)}">
                Inspect
              </button>
            </td>
          </tr>
        `;
      })
      .join('');

    dom.ordersTableBody.innerHTML = rowsHtml;

    dom.ordersTableBody.querySelectorAll('.order-table-row').forEach((row) => {
      row.addEventListener('click', (e) => {
        if (e.target.closest('.inspect-order-btn')) return;
        const ordId = row.dataset.orderId;
        if (ordId) openOrderDossier(ordId);
      });
    });

    dom.ordersTableBody.querySelectorAll('.inspect-order-btn').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const ordId = btn.dataset.id;
        if (ordId) openOrderDossier(ordId);
      });
    });
  }

  function updatePaginationControls() {
    const start = (state.currentPage - 1) * state.pageSize + 1;
    const end = Math.min(state.currentPage * state.pageSize, state.totalRecords);

    if (dom.ordersCountLabel) {
      dom.ordersCountLabel.textContent = `Order Records (Showing ${formatNumber(start)}–${formatNumber(end)} of ${formatNumber(state.totalRecords)})`;
    }

    if (dom.tablePaginationInfo) {
      dom.tablePaginationInfo.textContent = `Page ${state.currentPage} of ${formatNumber(state.totalPages)}`;
    }

    if (dom.pageDisplay) {
      dom.pageDisplay.textContent = `Page ${state.currentPage} of ${formatNumber(state.totalPages)}`;
    }

    if (dom.btnPrevPage) dom.btnPrevPage.disabled = state.currentPage <= 1;
    if (dom.btnNextPage) dom.btnNextPage.disabled = state.currentPage >= state.totalPages;
  }

  // =========================================================================
  // Order Intelligence Dossier Drawer / Modal
  // =========================================================================
  async function openOrderDossier(orderId) {
    if (!dom.modalBackdrop || !dom.orderDrawer || !dom.modalContentBody) return;

    dom.modalOrderId.textContent = orderId;
    dom.modalContentBody.innerHTML = `
      <div class="drawer-loading">
        <span class="status-pulse-dot" style="margin-right:8px;"></span>
        Retrieving order milestones and evaluating multi-stage checkpoint predictions...
      </div>
    `;

    dom.modalBackdrop.style.display = 'flex';
    requestAnimationFrame(() => {
      dom.modalBackdrop.classList.add('open');
      dom.modalBackdrop.setAttribute('aria-hidden', 'false');
    });

    try {
      const res = await fetch(`/api/order/${encodeURIComponent(orderId)}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const payload = await res.json();

      renderOrderDossierContent(payload);
    } catch (err) {
      console.error('Error fetching order dossier:', err);
      dom.modalContentBody.innerHTML = `
        <div class="checkpoint-card card-alert">
          <div style="color:var(--crimson-accent);font-weight:700;">Failed to load order intelligence dossier</div>
          <div style="font-size:0.82rem;color:var(--text-muted);">${escapeHtml(err.message)}</div>
        </div>
      `;
    }
  }

  function closeOrderDossier() {
    if (!dom.modalBackdrop) return;
    dom.modalBackdrop.classList.remove('open');
    dom.modalBackdrop.setAttribute('aria-hidden', 'true');
    setTimeout(() => {
      dom.modalBackdrop.style.display = 'none';
    }, 350);
  }

  function renderOrderDossierContent(payload) {
    const ms = payload.lifecycle_milestones || {};
    const risk = payload.risk_assessment || {};

    const metaHtml = `
      <div style="display:grid;grid-template-columns:repeat(2, 1fr);gap:12px;background:rgba(0,0,0,0.3);padding:14px;border-radius:10px;border:1px solid var(--border-subtle);">
        <div>
          <span style="font-size:0.7rem;color:var(--text-dim);display:block;text-transform:uppercase;">Store Identifier</span>
          <span style="font-family:var(--font-mono);font-weight:700;color:var(--cyan-primary);">${escapeHtml(ms.store_id || '-')}</span>
        </div>
        <div>
          <span style="font-size:0.7rem;color:var(--text-dim);display:block;text-transform:uppercase;">Delivery Status</span>
          <span style="font-weight:600;color:${ms.status === 'Delivered_Late' ? 'var(--crimson-accent)' : 'var(--emerald-accent)'};">${escapeHtml(ms.status || '-')}</span>
        </div>
        <div>
          <span style="font-size:0.7rem;color:var(--text-dim);display:block;text-transform:uppercase;">Items / Basket Value</span>
          <span style="font-family:var(--font-mono);">${ms.item_count ?? 0} items &bull; $${formatDecimal(ms.order_value, 2)}</span>
        </div>
        <div>
          <span style="font-size:0.7rem;color:var(--text-dim);display:block;text-transform:uppercase;">Customer Distance</span>
          <span style="font-family:var(--font-mono);">${ms.distance_km ? Number(ms.distance_km).toFixed(1) + ' km' : 'N/A'}</span>
        </div>
      </div>
    `;

    const milestonesHtml = `
      <div style="display:flex;flex-direction:column;gap:10px;">
        <div style="font-family:var(--font-heading);font-size:0.95rem;font-weight:700;color:#fff;">Fulfillment Timeline & Milestones</div>
        <div style="display:flex;flex-direction:column;gap:8px;font-size:0.82rem;background:rgba(0,0,0,0.25);padding:14px;border-radius:10px;border:1px solid var(--border-subtle);">
          <div style="display:flex;justify-content:space-between;">
            <span style="color:var(--text-muted);">&bull; T0 Checkout Timestamp:</span>
            <span style="font-family:var(--font-mono);">${escapeHtml(ms.order_time || '-')}</span>
          </div>
          <div style="display:flex;justify-content:space-between;">
            <span style="color:var(--text-muted);">&bull; Promised Delivery Time:</span>
            <span style="font-family:var(--font-mono);color:var(--amber-accent);">${escapeHtml(ms.promised_time || '-')}</span>
          </div>
          <div style="display:flex;justify-content:space-between;">
            <span style="color:var(--text-muted);">&bull; T1 Warehouse Pick End:</span>
            <span style="font-family:var(--font-mono);">${ms.pick_end ? escapeHtml(ms.pick_end) : '<em style="color:var(--text-dim)">No pick event recorded</em>'}</span>
          </div>
          ${
            ms.pick_duration_minutes !== null && ms.pick_duration_minutes !== undefined
              ? `<div style="display:flex;justify-content:space-between;padding-left:14px;color:var(--text-dim);">
                  <span>&rarr; Warehouse Pick Duration:</span>
                  <span style="font-family:var(--font-mono);">${Number(ms.pick_duration_minutes).toFixed(1)} min</span>
                 </div>`
              : ''
          }
          <div style="display:flex;justify-content:space-between;">
            <span style="color:var(--text-muted);">&bull; T2 Dispatch Proxy Time:</span>
            <span style="font-family:var(--font-mono);">${ms.effective_dispatch_time ? escapeHtml(ms.effective_dispatch_time) : '<em style="color:var(--text-dim)">No dispatch event recorded</em>'}</span>
          </div>
          ${
            ms.effective_transit_minutes !== null && ms.effective_transit_minutes !== undefined
              ? `<div style="display:flex;justify-content:space-between;padding-left:14px;color:var(--text-dim);">
                  <span>&rarr; Effective Transit Duration:</span>
                  <span style="font-family:var(--font-mono);">${Number(ms.effective_transit_minutes).toFixed(1)} min</span>
                 </div>`
              : ''
          }
          <div style="display:flex;justify-content:space-between;">
            <span style="color:var(--text-muted);">&bull; T3 Actual Drop-off Time:</span>
            <span style="font-family:var(--font-mono);">${ms.actual_delivery_time ? escapeHtml(ms.actual_delivery_time) : '<em style="color:var(--text-dim)">Pending / Unrecorded</em>'}</span>
          </div>
        </div>
      </div>
    `;

    // Multi-Stage Risk Assessments
    // Stage A
    const stageA = risk.stage_a || {};
    const probA = typeof stageA.risk_probability === 'number' ? stageA.risk_probability : 0;
    const isAlertA = Boolean(stageA.alert_triggered);

    const stageAHtml = `
      <div class="checkpoint-card ${isAlertA ? 'card-alert' : 'card-ok'}">
        <div class="checkpoint-card-header">
          <div>
            <div style="font-size:0.68rem;font-family:var(--font-mono);color:var(--text-dim);">CHECKPOINT T0 // CHECKOUT</div>
            <div class="checkpoint-name">Stage A Pre-Fulfillment Assessment</div>
          </div>
          <span class="kpi-badge ${isAlertA ? 'badge-crimson' : 'badge-emerald'}">
            ${isAlertA ? 'ALERT TRIGGERED' : 'STANDARD RISK'}
          </span>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:4px;">
          <span style="font-size:0.8rem;color:var(--text-muted);">Calculated Risk Probability</span>
          <span style="font-family:var(--font-mono);font-size:1.1rem;font-weight:700;color:${isAlertA ? 'var(--crimson-accent)' : 'var(--emerald-accent)'};">
            ${(probA * 100).toFixed(2)}%
          </span>
        </div>
        <div class="prob-meter-box">
          <div class="prob-meter-fill ${isAlertA ? 'fill-alert' : 'fill-ok'}" style="width:${Math.min(probA * 100, 100)}%;"></div>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:0.72rem;color:var(--text-dim);font-family:var(--font-mono);">
          <span>Operating Threshold: τ = 0.9300 (Frozen)</span>
          <span>Model: LightGBM (7 Features)</span>
        </div>
      </div>
    `;

    // Stage B1
    const stageB1 = risk.stage_b1 || {};
    let stageB1Html = '';
    if (!stageB1.checkpoint_available) {
      stageB1Html = `
        <div class="checkpoint-card" style="opacity:0.75;background:rgba(255,255,255,0.02);">
          <div class="checkpoint-card-header">
            <div>
              <div style="font-size:0.68rem;font-family:var(--font-mono);color:var(--text-dim);">CHECKPOINT T1 // POST-PICKING</div>
              <div class="checkpoint-name">Stage B1 Warehouse Pick Assessment</div>
            </div>
            <span class="kpi-badge" style="background:rgba(255,255,255,0.07);color:var(--text-dim);">NOT APPLICABLE</span>
          </div>
          <p style="font-size:0.8rem;color:var(--text-dim);margin-top:6px;">
            ⚠️ <strong>Telemetry Not Available</strong>: Order belongs to the 74.99% network cohort without sensor picking logs. Governed exclusively by Stage A checkout risk prediction.
          </p>
        </div>
      `;
    } else {
      const probB1 = typeof stageB1.risk_probability === 'number' ? stageB1.risk_probability : 0;
      const isAlertB1 = Boolean(stageB1.alert_triggered);
      const deltaB1 = stageB1.delta_vs_stage_a !== undefined && stageB1.delta_vs_stage_a !== null
        ? `${stageB1.delta_vs_stage_a >= 0 ? '+' : ''}${(stageB1.delta_vs_stage_a * 100).toFixed(1)}% vs T0`
        : '';

      stageB1Html = `
        <div class="checkpoint-card ${isAlertB1 ? 'card-alert' : 'card-ok'}">
          <div class="checkpoint-card-header">
            <div>
              <div style="font-size:0.68rem;font-family:var(--font-mono);color:var(--text-dim);">CHECKPOINT T1 // POST-PICKING</div>
              <div class="checkpoint-name">Stage B1 Warehouse Pick Assessment</div>
            </div>
            <span class="kpi-badge ${isAlertB1 ? 'badge-crimson' : 'badge-emerald'}">
              ${isAlertB1 ? 'ALERT TRIGGERED' : 'STANDARD RISK'}
            </span>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:4px;">
            <span style="font-size:0.8rem;color:var(--text-muted);">Updated Risk Probability ${deltaB1 ? `(${deltaB1})` : ''}</span>
            <span style="font-family:var(--font-mono);font-size:1.1rem;font-weight:700;color:${isAlertB1 ? 'var(--crimson-accent)' : 'var(--emerald-accent)'};">
              ${(probB1 * 100).toFixed(2)}%
            </span>
          </div>
          <div class="prob-meter-box">
            <div class="prob-meter-fill ${isAlertB1 ? 'fill-alert' : 'fill-ok'}" style="width:${Math.min(probB1 * 100, 100)}%;"></div>
          </div>
          <div style="display:flex;justify-content:space-between;font-size:0.72rem;color:var(--text-dim);font-family:var(--font-mono);">
            <span>Operating Threshold: τ = 0.9300 (Frozen)</span>
            <span>Model: LightGBM (23 Features)</span>
          </div>
        </div>
      `;
    }

    // Stage B2
    const stageB2 = risk.stage_b2 || {};
    let stageB2Html = '';
    if (!stageB2.checkpoint_available) {
      stageB2Html = `
        <div class="checkpoint-card" style="opacity:0.75;background:rgba(255,255,255,0.02);">
          <div class="checkpoint-card-header">
            <div>
              <div style="font-size:0.68rem;font-family:var(--font-mono);color:var(--text-dim);">CHECKPOINT T2 // DISPATCH PROXY</div>
              <div class="checkpoint-name">Stage B2 In-Transit Synchronization</div>
            </div>
            <span class="kpi-badge" style="background:rgba(255,255,255,0.07);color:var(--text-dim);">NOT APPLICABLE</span>
          </div>
          <p style="font-size:0.8rem;color:var(--text-dim);margin-top:6px;">
            ⚠️ <strong>Telemetry Not Available</strong>: Order belongs to the 74.99% network cohort without courier pickup timestamps.
          </p>
        </div>
      `;
    } else {
      const isDetOverride = Boolean(stageB2.is_deterministic_override);
      const probB2 = typeof stageB2.risk_probability === 'number' ? stageB2.risk_probability : 0;
      const isAlertB2 = Boolean(stageB2.alert_triggered);
      const deltaB2 = stageB2.delta_vs_stage_a !== undefined && stageB2.delta_vs_stage_a !== null
        ? `${stageB2.delta_vs_stage_a >= 0 ? '+' : ''}${(stageB2.delta_vs_stage_a * 100).toFixed(1)}% vs T0`
        : '';

      stageB2Html = `
        <div class="checkpoint-card ${isDetOverride || isAlertB2 ? 'card-alert' : 'card-ok'}">
          <div class="checkpoint-card-header">
            <div>
              <div style="font-size:0.68rem;font-family:var(--font-mono);color:var(--text-dim);">CHECKPOINT T2 // DISPATCH PROXY</div>
              <div class="checkpoint-name">Stage B2 In-Transit Synchronization</div>
            </div>
            ${
              isDetOverride
                ? '<span class="kpi-badge badge-crimson" style="background:#ef4444;color:#fff;font-weight:800;">CERTAIN BREACH (OVERDUE) &bull; P=1.0</span>'
                : `<span class="kpi-badge ${isAlertB2 ? 'badge-crimson' : 'badge-emerald'}">${isAlertB2 ? 'ALERT TRIGGERED' : 'STANDARD RISK'}</span>`
            }
          </div>
          
          <div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:4px;">
            <span style="font-size:0.8rem;color:var(--text-muted);">${isDetOverride ? 'Deterministic Policy Override' : `Model Risk Probability ${deltaB2 ? `(${deltaB2})` : ''}`}</span>
            <span style="font-family:var(--font-mono);font-size:1.1rem;font-weight:700;color:${isDetOverride || isAlertB2 ? 'var(--crimson-accent)' : 'var(--emerald-accent)'};">
              ${(probB2 * 100).toFixed(2)}%
            </span>
          </div>
          
          <div class="prob-meter-box">
            <div class="prob-meter-fill ${isDetOverride || isAlertB2 ? 'fill-alert' : 'fill-ok'}" style="width:${Math.min(probB2 * 100, 100)}%;"></div>
          </div>
          
          <div style="display:flex;justify-content:space-between;font-size:0.72rem;color:var(--text-dim);font-family:var(--font-mono);">
            <span>${isDetOverride ? 'Remaining SLA Budget ≤ 0m' : 'Operating Threshold: τ = 0.9300'}</span>
            <span>Model: Hybrid Deterministic (27 Features)</span>
          </div>

          <div style="font-size:0.74rem;color:var(--text-dim);background:rgba(0,0,0,0.3);padding:8px 10px;border-radius:6px;border-left:2px solid var(--blue-accent);margin-top:4px;line-height:1.4;">
            <strong>Dispatch Proxy Clarification:</strong> Fulfillment synchronization proxy between picking completion and courier pickup. Does not represent confirmed physical transit departure.
          </div>
        </div>
      `;
    }

    dom.modalContentBody.innerHTML = `
      ${metaHtml}
      ${milestonesHtml}
      <div style="display:flex;flex-direction:column;gap:12px;">
        <div style="font-family:var(--font-heading);font-size:0.95rem;font-weight:700;color:#fff;">Multi-Stage Checkpoint Risk Scores</div>
        ${stageAHtml}
        ${stageB1Html}
        ${stageB2Html}
      </div>
    `;
  }

  // =========================================================================
  // Reduced Motion Toggle
  // =========================================================================
  function initReducedMotion() {
    // Default experience is always visibly animated unless the user explicitly
    // disabled motion via the dashboard toggle button
    const saved = localStorage.getItem('macroops_reduced_motion');
    state.isReducedMotion = (saved === 'true');
    applyReducedMotion();
  }

  function toggleReducedMotion() {
    state.isReducedMotion = !state.isReducedMotion;
    localStorage.setItem('macroops_reduced_motion', String(state.isReducedMotion));
    applyReducedMotion();
  }

  function applyReducedMotion() {
    document.body.classList.toggle('reduced-motion', state.isReducedMotion);
    if (dom.motionIcon) {
      dom.motionIcon.textContent = state.isReducedMotion ? '⏸️' : '🌀';
    }
    const label = document.getElementById('motion-label');
    if (label) {
      label.textContent = state.isReducedMotion ? 'MOTION: OFF' : 'MOTION: ON';
    }
    if (dom.btnReducedMotion) {
      dom.btnReducedMotion.title = state.isReducedMotion
        ? 'Dashboard Animations Paused (Click to enable motion)'
        : 'Dashboard Animations Active (Click to reduce motion)';
      dom.btnReducedMotion.classList.toggle('motion-off', state.isReducedMotion);
    }
  }

  // =========================================================================
  // Circular Order Fulfillment Journey Synchronizer
  // Cycles through: 1. Order Placed -> 2. Packing -> 3. Dispatched -> 4. Delivered & Unboxed
  // Every 3.0 seconds (12s complete cycle), matching CSS keyframe animations
  // =========================================================================
  function initOrderLifecycleLoop() {
    const stageDot = document.getElementById('stage-dot');
    const stageText = document.getElementById('stage-text');
    const clockChip = document.getElementById('core-live-clock');
    const valueEl = clockChip ? clockChip.querySelector('.chip-value') : null;

    const stages = [
      {
        id: 1,
        title: '1. ORDER PLACED (T0)',
        dotColor: '#00f2fe',
        dotShadow: '0 0 10px #00f2fe',
        nodeId: 'node-st-1',
        pillId: 'step-pill-1'
      },
      {
        id: 2,
        title: '2. PACKING IN DARK STORE (T1)',
        dotColor: '#818cf8',
        dotShadow: '0 0 10px #818cf8',
        nodeId: 'node-st-2',
        pillId: 'step-pill-2'
      },
      {
        id: 3,
        title: '3. DISPATCHED // IN-TRANSIT (T2)',
        dotColor: '#f59e0b',
        dotShadow: '0 0 10px #f59e0b',
        nodeId: 'node-st-3',
        pillId: 'step-pill-3'
      },
      {
        id: 4,
        title: '4. DELIVERED & UNBOXED (T3)',
        dotColor: '#10b981',
        dotShadow: '0 0 12px #10b981',
        nodeId: 'node-st-4',
        pillId: 'step-pill-4'
      }
    ];

    let currentStageIndex = 0;
    const stageNodes = stages.map(s => document.getElementById(s.nodeId));
    const stepPills = stages.map(s => document.getElementById(s.pillId));

    function setStage(idx) {
      currentStageIndex = idx % stages.length;
      const st = stages[currentStageIndex];

      if (stageText) stageText.textContent = st.title;
      if (stageDot) {
        stageDot.style.backgroundColor = st.dotColor;
        stageDot.style.boxShadow = st.dotShadow;
      }

      stageNodes.forEach((node, i) => {
        if (node) node.classList.toggle('active', i === currentStageIndex);
      });

      stepPills.forEach((pill, i) => {
        if (pill) pill.classList.toggle('active-step', i === currentStageIndex);
      });
    }

    // Set initial stage
    setStage(0);

    // Interactive clicking on station nodes or step pills
    stageNodes.forEach((node, i) => {
      if (node) {
        node.addEventListener('click', () => setStage(i));
      }
    });

    stepPills.forEach((pill, i) => {
      if (pill) {
        pill.addEventListener('click', () => setStage(i));
      }
    });

    // 12s synchronized timer (changes station every 3.0 seconds)
    setInterval(() => {
      if (state.isReducedMotion) return;
      setStage((currentStageIndex + 1) % stages.length);
    }, 3000);

    // Live clock ticker
    if (valueEl) {
      let seconds = 0;
      setInterval(() => {
        seconds++;
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        const timeStr = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
        valueEl.textContent = `LIVE (${timeStr} // 60 FPS)`;
      }, 1000);
    }
  }

  // =========================================================================
  // Phase 03 Part 02: Access & Safety Monitor
  // =========================================================================
  async function loadAccessScenarios() {
    try {
      const res = await fetch('/api/prototypes/delivery-access/scenarios');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      state.accessScenarios = data.scenarios || [];

      if (dom.selectAccessScenario) {
        dom.selectAccessScenario.innerHTML = '';
        state.accessScenarios.forEach((s) => {
          const opt = document.createElement('option');
          opt.value = s.scenario_id;
          opt.textContent = `${s.scenario_id} — ${s.building_type} (Fl ${s.floor_number}, ${s.parcel_weight_kg}kg, Lift: ${s.elevator_available ? 'Yes' : 'No'})`;
          dom.selectAccessScenario.appendChild(opt);
        });

        if (state.accessScenarios.length > 0) {
          populateAccessForm(state.accessScenarios[0]);
          evaluateAccessScenario(state.accessScenarios[0]);
        }
      }
    } catch (err) {
      console.warn('Failed to load access scenarios:', err);
    }
  }

  function populateAccessForm(s) {
    if (dom.inputAccessWeight) dom.inputAccessWeight.value = s.parcel_weight_kg;
    if (dom.inputAccessFloor) dom.inputAccessFloor.value = s.floor_number;
    if (dom.selectAccessElevator) dom.selectAccessElevator.value = String(Boolean(s.elevator_available));
    if (dom.selectAccessGate) dom.selectAccessGate.value = String(Boolean(s.gate_code_required));
    if (dom.selectAccessHazard) dom.selectAccessHazard.value = s.hazard_reported || 'none';
    if (dom.inputAccessVicinity) dom.inputAccessVicinity.value = s.courier_distance_meters || 120;
  }

  function getAccessFormPayload() {
    return {
      parcel_weight_kg: parseFloat(dom.inputAccessWeight ? dom.inputAccessWeight.value : 18.5) || 18.5,
      floor_number: parseInt(dom.inputAccessFloor ? dom.inputAccessFloor.value : 4, 10) || 4,
      elevator_available: dom.selectAccessElevator ? dom.selectAccessElevator.value === 'true' : false,
      gate_code_required: dom.selectAccessGate ? dom.selectAccessGate.value === 'true' : true,
      hazard_reported: dom.selectAccessHazard ? dom.selectAccessHazard.value : 'none',
      courier_distance_meters: parseFloat(dom.inputAccessVicinity ? dom.inputAccessVicinity.value : 120) || 120
    };
  }

  async function evaluateAccessScenario(payload) {
    try {
      if (dom.accessBadgeStatus) dom.accessBadgeStatus.textContent = 'EVALUATING...';
      const res = await fetch('/api/prototypes/delivery-access/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const decision = await res.json();

      renderAccessDecision(decision);
    } catch (err) {
      console.warn('Access evaluation error:', err);
    }
  }

  function renderAccessDecision(dec) {
    if (dom.accessBadgeStatus) dom.accessBadgeStatus.textContent = 'POLICY ACTIVE';
    if (dom.accessDecisionName) {
      dom.accessDecisionName.textContent = dec.decision;
      dom.accessDecisionName.className = 'decision-main-badge';
      if (dec.decision === 'SAFE_DOORSTEP_PROCEED') dom.accessDecisionName.classList.add('tier-safe');
      else if (dec.decision === 'PRE_ARRIVAL_ACCESS_BRIEF') dom.accessDecisionName.classList.add('tier-brief');
      else if (dec.decision === 'GROUND_FLOOR_HANDOFF') dom.accessDecisionName.classList.add('tier-handoff');
      else dom.accessDecisionName.classList.add('tier-review');
    }

    if (dom.accessDecisionReason) dom.accessDecisionReason.textContent = dec.decision_reason;

    if (dom.accessDoorstepSafe) {
      dom.accessDoorstepSafe.textContent = dec.is_doorstep_safe ? 'YES ✓' : 'NO ✕';
      dom.accessDoorstepSafe.className = `tile-value ${dec.is_doorstep_safe ? 'text-emerald' : 'text-crimson'}`;
    }

    if (dom.accessGroundHandoff) {
      dom.accessGroundHandoff.textContent = dec.ground_floor_handoff_authorized ? 'AUTHORIZED ✓' : 'OPTIONAL';
      dom.accessGroundHandoff.className = `tile-value ${dec.ground_floor_handoff_authorized ? 'text-emerald' : 'text-muted'}`;
    }

    if (dom.accessBriefPushed) {
      dom.accessBriefPushed.textContent = dec.pre_arrival_brief_pushed ? 'SENT (< 200m)' : 'PENDING';
      dom.accessBriefPushed.className = `tile-value ${dec.pre_arrival_brief_pushed ? 'text-cyan' : 'text-muted'}`;
    }

    if (dom.accessPenaltyProt) {
      dom.accessPenaltyProt.textContent = dec.courier_penalty_protection ? 'PROTECTED' : 'STANDARD';
      dom.accessPenaltyProt.className = `tile-value ${dec.courier_penalty_protection ? 'text-amber' : 'text-muted'}`;
    }

    if (dom.accessActionBrief) dom.accessActionBrief.textContent = dec.courier_action_brief;
    if (dom.accessCustomerMsg) dom.accessCustomerMsg.textContent = `"${dec.customer_coordination_message}"`;
  }

  // =========================================================================
  // Phase 03 Part 02: Dispute Inspector & Supplier Batch Leaderboard
  // =========================================================================
  async function loadBatchInvestigations() {
    try {
      const res = await fetch('/api/prototypes/disputes/batch-investigations');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      state.batchInvestigations = data.batch_investigations || [];

      renderBatchTable();
    } catch (err) {
      console.warn('Failed to load batch investigations:', err);
    }
  }

  function renderBatchTable() {
    if (!dom.batchTableBody) return;
    if (state.batchInvestigations.length === 0) {
      dom.batchTableBody.innerHTML = '<tr><td colspan="8" class="table-loading">No emerging supplier defect clusters.</td></tr>';
      return;
    }

    dom.batchTableBody.innerHTML = state.batchInvestigations.map((b) => {
      const isAdvisory = b.recommendation === 'RECOMMEND_SUPPLIER_BATCH_INVESTIGATION';
      const badgeClass = isAdvisory ? 'badge-crimson' : 'badge-emerald';
      const badgeText = isAdvisory ? 'INVESTIGATE BATCH' : 'NORMAL MONITORING';
      const sigs = (b.defect_signatures || []).map(s => `<span class="tag-badge">${escapeHtml(s)}</span>`).join(' ');

      return `
        <tr>
          <td><strong>${escapeHtml(b.batch_id)}</strong></td>
          <td><span class="code-pill">${escapeHtml(b.supplier_id)}</span></td>
          <td>${escapeHtml(b.category)}</td>
          <td>${b.affected_skus_count} SKUs</td>
          <td>${b.complaint_count} / ${formatNumber(b.sampled_units_count)}</td>
          <td><strong>${b.defect_rate_pct.toFixed(2)}%</strong></td>
          <td>${sigs}</td>
          <td><span class="kpi-badge ${badgeClass}">${badgeText}</span></td>
        </tr>
      `;
    }).join('');
  }

  async function loadDisputeScenarios() {
    try {
      const res = await fetch('/api/prototypes/disputes/scenarios');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      state.complaintScenarios = data.scenarios || [];

      if (dom.selectDisputeScenario) {
        dom.selectDisputeScenario.innerHTML = '';
        state.complaintScenarios.forEach((c) => {
          const opt = document.createElement('option');
          opt.value = c.complaint_id;
          opt.textContent = `${c.complaint_id} — ${c.item_name} (₹${c.item_price_inr}, ${c.complaint_category})`;
          dom.selectDisputeScenario.appendChild(opt);
        });

        if (state.complaintScenarios.length > 0) {
          inspectDisputeScenario(state.complaintScenarios[0]);
        }
      }
    } catch (err) {
      console.warn('Failed to load dispute scenarios:', err);
    }
  }

  function inspectDisputeScenario(c) {
    if (dom.disputeSku) dom.disputeSku.textContent = c.sku_id;
    if (dom.disputeItem) dom.disputeItem.textContent = c.item_name;
    if (dom.disputeCat) dom.disputeCat.textContent = c.item_category;
    if (dom.disputePrice) dom.disputePrice.textContent = `₹${c.item_price_inr.toFixed(2)}`;
    if (dom.disputeDesc) dom.disputeDesc.textContent = c.defect_description;
    if (dom.disputeBatch) dom.disputeBatch.textContent = c.batch_id;

    const delay = c.delivery_delay_minutes || 0;
    const temp = c.ambient_temp_c || 30.0;
    if (dom.disputeDelayVal) dom.disputeDelayVal.textContent = `+${delay.toFixed(1)} min`;
    if (dom.disputeTempVal) dom.disputeTempVal.textContent = `${temp.toFixed(1)}°C`;

    const isPerishableDelay = (c.item_category === 'dairy_chilled' || c.item_category === 'perishable_produce') && delay > 15;
    if (dom.disputeCorrVal) {
      dom.disputeCorrVal.textContent = isPerishableDelay ? 'STRONG (Transit Spoilage)' : 'LOW / AMBIENT';
      dom.disputeCorrVal.className = `tile-value ${isPerishableDelay ? 'text-crimson' : 'text-cyan'}`;
    }

    if (dom.disputeBlameVal) {
      dom.disputeBlameVal.textContent = isPerishableDelay ? 'EXONERATED' : 'STANDARD';
      dom.disputeBlameVal.className = `tile-value ${isPerishableDelay ? 'text-emerald' : 'text-secondary'}`;
    }

    if (dom.meterThermalFill) {
      const fillPct = Math.min(100, Math.max(15, (delay / 30.0) * 100));
      dom.meterThermalFill.style.width = `${fillPct}%`;
    }

    if (dom.disputeEvidenceTags) {
      const tags = [];
      if (c.evidence_attached) tags.push('PHOTO_ATTACHED');
      else tags.push('NO_PHOTO_ATTACHED');
      if (c.evidence_tags) {
        c.evidence_tags.forEach(t => tags.push(t.toUpperCase()));
      }
      dom.disputeEvidenceTags.innerHTML = tags.map(t => `<span class="tag-badge">${escapeHtml(t)}</span>`).join('');
    }

    if (dom.disputeAdvisoryNote) {
      if (isPerishableDelay) {
        dom.disputeAdvisoryNote.textContent = `Perishable product degradation strongly correlated with severe fulfillment delay (+${delay.toFixed(1)}m at ${temp.toFixed(1)}°C ambient). Customer exonerated. Dark store cold-box packing procedure flagged for review.`;
      } else {
        dom.disputeAdvisoryNote.textContent = `Claim logged under ${c.complaint_category}. Supplier batch ${c.batch_id} monitored in cluster registry.`;
      }
    }
  }

  // =========================================================================
  // Phase 03 Part 02: Fair Adjudication Console
  // =========================================================================
  async function loadAdjudicationScenarios() {
    try {
      if (state.complaintScenarios.length === 0) {
        const res = await fetch('/api/prototypes/disputes/scenarios');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        state.complaintScenarios = data.scenarios || [];
      }

      if (dom.selectAdjudicationScenario) {
        dom.selectAdjudicationScenario.innerHTML = '';
        state.complaintScenarios.forEach((c) => {
          const opt = document.createElement('option');
          opt.value = c.complaint_id;
          opt.textContent = `${c.complaint_id} — ${c.item_name} (₹${c.item_price_inr}, ${c.complaint_category})`;
          dom.selectAdjudicationScenario.appendChild(opt);
        });

        if (state.complaintScenarios.length > 0) {
          populateAdjudicationForm(state.complaintScenarios[0]);
          evaluateAdjudication(state.complaintScenarios[0]);
        }
      }
    } catch (err) {
      console.warn('Failed to load adjudication scenarios:', err);
    }
  }

  function populateAdjudicationForm(c) {
    if (dom.inputAdjItemName) dom.inputAdjItemName.value = c.item_name;
    if (dom.selectAdjCategory) dom.selectAdjCategory.value = c.item_category;
    if (dom.inputAdjPrice) dom.inputAdjPrice.value = c.item_price_inr;
    if (dom.selectAdjDefect) dom.selectAdjDefect.value = c.complaint_category;
    if (dom.selectAdjEvidence) dom.selectAdjEvidence.value = String(Boolean(c.evidence_attached));
    if (dom.inputAdjClaimsFreq) dom.inputAdjClaimsFreq.value = c.customer_claims_90d || 2;
    if (dom.inputAdjDelay) dom.inputAdjDelay.value = c.delivery_delay_minutes || 0;
    if (dom.inputAdjTemp) dom.inputAdjTemp.value = c.ambient_temp_c || 30.0;
  }

  function getAdjudicationFormPayload() {
    return {
      item_name: dom.inputAdjItemName ? dom.inputAdjItemName.value.trim() : 'Organic Milk',
      item_category: dom.selectAdjCategory ? dom.selectAdjCategory.value : 'dairy_chilled',
      item_price_inr: parseFloat(dom.inputAdjPrice ? dom.inputAdjPrice.value : 85.0) || 85.0,
      complaint_category: dom.selectAdjDefect ? dom.selectAdjDefect.value : 'spoiled_perishable',
      evidence_attached: dom.selectAdjEvidence ? dom.selectAdjEvidence.value === 'true' : true,
      customer_claims_90d: parseInt(dom.inputAdjClaimsFreq ? dom.inputAdjClaimsFreq.value : 2, 10) || 2,
      delivery_delay_minutes: parseFloat(dom.inputAdjDelay ? dom.inputAdjDelay.value : 22.0) || 22.0,
      ambient_temp_c: parseFloat(dom.inputAdjTemp ? dom.inputAdjTemp.value : 34.0) || 34.0
    };
  }

  async function evaluateAdjudication(payload) {
    try {
      if (dom.adjBadgeStatus) dom.adjBadgeStatus.textContent = 'EVALUATING...';
      const res = await fetch('/api/prototypes/disputes/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const decision = await res.json();

      renderAdjudicationDecision(decision);
    } catch (err) {
      console.warn('Adjudication evaluation error:', err);
    }
  }

  function renderAdjudicationDecision(dec) {
    if (dom.adjBadgeStatus) dom.adjBadgeStatus.textContent = dec.adjudication_status || 'RECOMMENDED_BY_POLICY';

    if (dom.adjActionName) {
      dom.adjActionName.textContent = dec.recommended_action;
      dom.adjActionName.className = 'decision-main-badge';

      if (dec.recommended_action === 'IMMEDIATE_REFUND') dom.adjActionName.classList.add('tier-refund');
      else if (dec.recommended_action === 'PRIORITY_REPLACEMENT') dom.adjActionName.classList.add('tier-replacement');
      else if (dec.recommended_action === 'PARTIAL_COMPENSATION') dom.adjActionName.classList.add('tier-partial');
      else if (dec.recommended_action === 'REQUEST_EVIDENCE') dom.adjActionName.classList.add('tier-evidence');
      else dom.adjActionName.classList.add('tier-review');
    }

    if (dom.adjActionReason) dom.adjActionReason.textContent = dec.policy_rationale;

    const fin = dec.financial_assessment || {};
    if (dom.adjPayoutAmount) dom.adjPayoutAmount.textContent = `₹${formatDecimal(fin.recommended_payout_inr, 2)} (${fin.payout_percentage ?? 100}%)`;
    if (dom.adjSettlementMode) dom.adjSettlementMode.textContent = fin.settlement_channel || 'ORIGINAL_PAYMENT';

    const fair = dec.fairness_audit || {};
    if (dom.adjAntibiasAudit) {
      dom.adjAntibiasAudit.textContent = fair.automated_rejection_prohibited ? 'PASSED ✓' : 'VIOLATION ✕';
      dom.adjAntibiasAudit.className = `tile-value ${fair.automated_rejection_prohibited ? 'text-emerald' : 'text-crimson'}`;
    }

    if (dom.adjHumanReview) {
      const isReview = dec.recommended_action === 'HUMAN_REVIEW';
      dom.adjHumanReview.textContent = isReview ? 'REQUIRED' : 'NOT REQUIRED';
      dom.adjHumanReview.className = `tile-value ${isReview ? 'text-amber' : 'text-emerald'}`;
    }

    if (dom.adjRationaleText) dom.adjRationaleText.textContent = dec.policy_rationale;
    if (dom.adjCustomerPreview) dom.adjCustomerPreview.textContent = `"${dec.customer_plain_language_explanation}"`;
  }

  // =========================================================================
  // Event Listeners & Initialization
  // =========================================================================
  function initEventListeners() {
    dom.navTabs.forEach((tab) => {
      tab.addEventListener('click', () => {
        const target = tab.dataset.tab;
        if (target) switchTab(target);
      });
    });

    if (dom.storeSortSelect) {
      dom.storeSortSelect.addEventListener('change', (e) => {
        state.storeSortBy = e.target.value;
        renderStoreLeaderboard();
      });
    }

    if (dom.btnApplyFilters) {
      dom.btnApplyFilters.addEventListener('click', () => {
        state.filters.search = dom.filterSearch ? dom.filterSearch.value.trim() : '';
        state.filters.storeId = dom.filterStoreSelect ? dom.filterStoreSelect.value : '';
        state.filters.status = dom.filterStatus ? dom.filterStatus.value : '';
        state.filters.hasTelemetry = dom.filterTelemetry ? dom.filterTelemetry.value : '';
        state.currentPage = 1;
        fetchOrders();
      });
    }

    if (dom.btnResetFilters) {
      dom.btnResetFilters.addEventListener('click', () => {
        if (dom.filterSearch) dom.filterSearch.value = '';
        if (dom.filterStoreSelect) dom.filterStoreSelect.value = '';
        if (dom.filterStatus) dom.filterStatus.value = '';
        if (dom.filterTelemetry) dom.filterTelemetry.value = '';

        state.filters = {
          search: '',
          storeId: '',
          status: '',
          hasTelemetry: ''
        };
        state.currentPage = 1;
        fetchOrders();
      });
    }

    if (dom.filterSearch) {
      dom.filterSearch.addEventListener('input', (e) => {
        clearTimeout(state.searchDebounceTimer);
        state.searchDebounceTimer = setTimeout(() => {
          state.filters.search = e.target.value.trim();
          state.currentPage = 1;
          fetchOrders();
        }, 400);
      });
    }

    if (dom.btnPrevPage) {
      dom.btnPrevPage.addEventListener('click', () => {
        if (state.currentPage > 1) {
          state.currentPage -= 1;
          fetchOrders();
        }
      });
    }

    if (dom.btnNextPage) {
      dom.btnNextPage.addEventListener('click', () => {
        if (state.currentPage < state.totalPages) {
          state.currentPage += 1;
          fetchOrders();
        }
      });
    }

    if (dom.btnCloseModal) {
      dom.btnCloseModal.addEventListener('click', closeOrderDossier);
    }

    if (dom.modalBackdrop) {
      dom.modalBackdrop.addEventListener('click', (e) => {
        if (e.target === dom.modalBackdrop) {
          closeOrderDossier();
        }
      });
    }

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && dom.modalBackdrop && dom.modalBackdrop.classList.contains('open')) {
        closeOrderDossier();
      }
    });

    if (dom.btnReducedMotion) {
      dom.btnReducedMotion.addEventListener('click', toggleReducedMotion);
    }

    // Phase 03 Part 02 Event Listeners
    if (dom.selectAccessScenario) {
      dom.selectAccessScenario.addEventListener('change', (e) => {
        const found = state.accessScenarios.find(s => s.scenario_id === e.target.value);
        if (found) {
          populateAccessForm(found);
          evaluateAccessScenario(found);
        }
      });
    }

    if (dom.btnEvaluateAccess) {
      dom.btnEvaluateAccess.addEventListener('click', () => {
        const payload = getAccessFormPayload();
        evaluateAccessScenario(payload);
      });
    }

    if (dom.selectDisputeScenario) {
      dom.selectDisputeScenario.addEventListener('change', (e) => {
        const found = state.complaintScenarios.find(c => c.complaint_id === e.target.value);
        if (found) {
          inspectDisputeScenario(found);
        }
      });
    }

    if (dom.btnSyncToAdjudication) {
      dom.btnSyncToAdjudication.addEventListener('click', () => {
        switchTab('tab-adjudication-console');
        if (dom.selectDisputeScenario && dom.selectAdjudicationScenario) {
          dom.selectAdjudicationScenario.value = dom.selectDisputeScenario.value;
          const found = state.complaintScenarios.find(c => c.complaint_id === dom.selectDisputeScenario.value);
          if (found) {
            populateAdjudicationForm(found);
            evaluateAdjudication(found);
          }
        }
      });
    }

    if (dom.selectAdjudicationScenario) {
      dom.selectAdjudicationScenario.addEventListener('change', (e) => {
        const found = state.complaintScenarios.find(c => c.complaint_id === e.target.value);
        if (found) {
          populateAdjudicationForm(found);
          evaluateAdjudication(found);
        }
      });
    }

    if (dom.btnEvaluateAdjudication) {
      dom.btnEvaluateAdjudication.addEventListener('click', () => {
        const payload = getAdjudicationFormPayload();
        evaluateAdjudication(payload);
      });
    }
  }

  // =========================================================================
  // Bootstrap Application
  // =========================================================================
  async function init() {
    initReducedMotion();
    initRevealObserver();
    initEventListeners();
    initOrderLifecycleLoop();

    await Promise.allSettled([
      fetchSystemHealth(),
      fetchKPIs(),
      fetchStores(),
      fetchOrders(),
      loadAccessScenarios(),
      loadBatchInvestigations(),
      loadDisputeScenarios()
    ]);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
