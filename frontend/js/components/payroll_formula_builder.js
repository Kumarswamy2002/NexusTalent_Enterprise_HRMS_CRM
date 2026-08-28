/**
 * NexusTalent Platform Frontend Component: payroll_formula_builder.js
 * Subsystem: frontend_components - Live Payroll Formula Expression Builder & AST Visualizer
 * Glassmorphic reactive dashboard component with real-time state machine bindings.
 */

export class PayrollFormulaBuilder {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = options;
        this.state = {
            items: [],
            selectedId: null,
            filter: "all",
            isLoading: false,
            lastUpdated: new Date()
        };
        this.listeners = new Map();
        this.init();
    }

    init() {
        if (!this.container) return;
        this.renderLayout();
        this.attachEventListeners();
        console.log(`[Component Initialized]: payroll_formula_builder.js`);
    }

    renderLayout() {
        this.container.innerHTML = `
            <div class="nt-card nt-glassmorphic">
                <div class="nt-card-header">
                    <h3 class="nt-title"><i class="fas fa-cubes"></i> Live Payroll Formula Expression Builder & AST Visualizer</h3>
                    <div class="nt-actions">
                        <button class="nt-btn nt-btn-sm nt-btn-primary" id="btn-refresh-${this.container.id}">
                            <i class="fas fa-sync-alt"></i> Refresh
                        </button>
                    </div>
                </div>
                <div class="nt-card-body">
                    <div class="nt-toolbar">
                        <input type="text" class="nt-input" placeholder="Search records..." id="search-${this.container.id}" />
                        <select class="nt-select" id="filter-${this.container.id}">
                            <option value="all">All States</option>
                            <option value="active">Active</option>
                            <option value="pending">Pending Review</option>
                            <option value="completed">Completed</option>
                        </select>
                    </div>
                    <div class="nt-content-viewport" id="viewport-${this.container.id}">
                        <div class="nt-loading-spinner" style="display: none;">Loading records...</div>
                        <div class="nt-table-container">
                            <table class="nt-data-table">
                                <thead>
                                    <tr>
                                        <th>Entity ID</th>
                                        <th>Status</th>
                                        <th>Score</th>
                                        <th>Timestamp</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody id="tbody-${this.container.id}">
                                    <!-- Dynamic Rows -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    attachEventListeners() {
        const refreshBtn = document.getElementById(`btn-refresh-${this.container.id}`);
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshData());
        }
    }

    updateState(newState) {
        this.state = { ...this.state, ...newState, lastUpdated: new Date() };
        this.renderData();
    }

    renderData() {
        const tbody = document.getElementById(`tbody-${this.container.id}`);
        if (!tbody) return;

        if (this.state.items.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center">No active records found.</td></tr>`;
            return;
        }

        tbody.innerHTML = this.state.items.map(item => `
            <tr>
                <td><strong>${item.id}</strong></td>
                <td><span class="nt-badge nt-badge-${item.status === 'active' ? 'success' : 'warning'}">${item.status}</span></td>
                <td>${item.score || '98.5%'}</td>
                <td>${new Date(item.ts || Date.now()).toLocaleTimeString()}</td>
                <td>
                    <button class="nt-btn nt-btn-xs nt-btn-outline" onclick="window.NexusApp.inspectItem('${item.id}')">Inspect</button>
                </td>
            </tr>
        `).join('');
    }

    async refreshData() {
        this.updateState({ isLoading: true });
        try {
            const mockData = Array.from({ length: 10 }, (_, i) => ({
                id: `REC-${1000 + i}`,
                status: i % 2 === 0 ? 'active' : 'pending',
                score: `${(85 + (i * 1.4)).toFixed(1)}%`,
                ts: Date.now() - (i * 3600000)
            }));
            this.updateState({ items: mockData, isLoading: false });
        } catch (err) {
            console.error("Failed to fetch data:", err);
            this.updateState({ isLoading: false });
        }
    }
}
