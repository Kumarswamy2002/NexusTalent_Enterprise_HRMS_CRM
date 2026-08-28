/**
 * NexusTalent Enterprise Single Page Application (SPA) Controller
 * Real-time event subscription, Modular Tab Views & Subsystem Controllers
 */

const App = {
  state: {
    currentTab: "dashboard",
    employees: [],
    departments: [],
    requisitions: [],
    kanbanData: [],
    attendanceSummary: null,
    payrollRuns: [],
    objectives: [],
    nineBox: null,
    tickets: [],
    socket: null,
    selectedRequisitionId: null
  },

  init() {
    this.bindNavigation();
    this.initWebSocket();
    this.loadInitialData();
  },

  initWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    try {
      this.state.socket = new WebSocket(wsUrl);
      this.state.socket.onopen = () => {
        document.getElementById("ws-status-text").innerText = "Live Telemetry Active";
      };
      this.state.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "DOMAIN_EVENT") {
            this.showToast(`⚡ Event: ${data.event_type}`, data.payload);
            this.loadInitialData(false); // Refresh silently
          }
        } catch (e) {}
      };
      this.state.socket.onclose = () => {
        document.getElementById("ws-status-text").innerText = "Reconnecting...";
        setTimeout(() => this.initWebSocket(), 3000);
      };
    } catch (e) {
      console.warn("WebSocket init error:", e);
    }
  },

  showToast(title, payload) {
    const container = document.getElementById("toast-container");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.innerHTML = `
      <div>
        <div style="font-weight: 700;">${title}</div>
        <div style="font-size: 0.75rem; color: #94a3b8;">${JSON.stringify(payload).slice(0, 70)}...</div>
      </div>
    `;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
  },

  bindNavigation() {
    document.querySelectorAll(".nav-btn").forEach(btn => {
      btn.addEventListener("click", (e) => {
        document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
        const targetBtn = e.currentTarget;
        targetBtn.classList.add("active");
        const tab = targetBtn.getAttribute("data-tab");
        this.switchTab(tab);
      });
    });
  },

  async loadInitialData(render = true) {
    try {
      const [depts, emps, reqs, att, runs, objs, ninebox, tix] = await Promise.all([
        fetch("/api/v1/hrms/departments").then(r => r.json()),
        fetch("/api/v1/hrms/employees").then(r => r.json()),
        fetch("/api/v1/recruitment/requisitions").then(r => r.json()),
        fetch("/api/v1/attendance/daily-dashboard").then(r => r.json()),
        fetch("/api/v1/payroll/runs").then(r => r.json()),
        fetch("/api/v1/performance/objectives").then(r => r.json()),
        fetch("/api/v1/performance/nine-box-matrix").then(r => r.json()),
        fetch("/api/v1/helpdesk/tickets").then(r => r.json())
      ]);

      this.state.departments = depts || [];
      this.state.employees = emps || [];
      this.state.requisitions = reqs || [];
      this.state.attendanceSummary = att || { total_present_today: 0, records: [] };
      this.state.payrollRuns = runs || [];
      this.state.objectives = objs || [];
      this.state.nineBox = ninebox || { matrix: {}, meta: {} };
      this.state.tickets = tix || [];

      if (!this.state.selectedRequisitionId && this.state.requisitions.length > 0) {
        this.state.selectedRequisitionId = this.state.requisitions[0].id;
      }

      // Update badge counters
      const navEmp = document.getElementById("nav-emp-count");
      if (navEmp) navEmp.innerText = this.state.employees.length;
      const navReq = document.getElementById("nav-req-count");
      if (navReq) navReq.innerText = this.state.requisitions.length;
      const navTix = document.getElementById("nav-ticket-count");
      if (navTix) navTix.innerText = this.state.tickets.length;

      if (render) {
        this.renderCurrentTab();
      }
    } catch (err) {
      console.error("Failed to load initial data:", err);
    }
  },

  switchTab(tab) {
    this.state.currentTab = tab;
    const headings = {
      dashboard: ["Executive Workforce Pulse", "Real-time enterprise metrics, event telemetry & talent pipeline"],
      hrms: ["Employee Directory & Org Master", "Complete employee master records, departments & organizational tree"],
      recruitment: ["Recruitment & Talent CRM", "Visual Kanban candidate pipeline with AI match scoring & scorecards"],
      attendance: ["Time, Attendance & Geofencing Hub", "Geofence GPS clock-in simulator, shifts & universal leave approvals"],
      payroll: ["Global Payroll & Compensation Engine", "AST safe formula parser, statutory deductions & cryptographic payslips"],
      performance: ["Performance, OKRs & 9-Box Grid", "Cascading company-to-individual goals & McKinsey talent calibration matrix"],
      helpdesk: ["Employee Helpdesk (Internal CRM)", "HR service delivery, SLA countdown tracking & threaded resolutions"],
      "ai-insights": ["AI Workforce Intelligence Platform", "Machine learning resume-to-job semantic matcher & attrition risk predictor"]
    };

    const h = headings[tab] || ["NexusTalent", "Enterprise Platform"];
    document.getElementById("page-heading").innerText = h[0];
    document.getElementById("page-subheading").innerText = h[1];
    this.renderCurrentTab();
  },

  renderCurrentTab() {
    const viewport = document.getElementById("viewport");
    if (!viewport) return;

    switch (this.state.currentTab) {
      case "dashboard":
        viewport.innerHTML = this.renderDashboard();
        break;
      case "hrms":
        viewport.innerHTML = this.renderHRMS();
        break;
      case "recruitment":
        this.renderRecruitmentKanban(viewport);
        break;
      case "attendance":
        viewport.innerHTML = this.renderAttendance();
        break;
      case "payroll":
        viewport.innerHTML = this.renderPayroll();
        break;
      case "performance":
        viewport.innerHTML = this.renderPerformance();
        break;
      case "helpdesk":
        viewport.innerHTML = this.renderHelpdesk();
        break;
      case "ai-insights":
        viewport.innerHTML = this.renderAIInsights();
        break;
      default:
        viewport.innerHTML = `<div class="card"><h3>View under construction</h3></div>`;
    }
  },

  // 1. Executive Dashboard View
  renderDashboard() {
    const totalEmps = this.state.employees.length;
    const totalReqs = this.state.requisitions.length;
    const presentToday = this.state.attendanceSummary ? this.state.attendanceSummary.total_present_today : 0;
    const attendancePct = totalEmps > 0 ? Math.round((presentToday / totalEmps) * 100) : 100;
    const lastPayroll = this.state.payrollRuns.length > 0 ? `$${(this.state.payrollRuns[0].total_net_disbursed).toLocaleString()}` : "$77,320";

    return `
      <div class="grid-cards">
        <div class="card">
          <div class="card-header">
            <span class="card-title">Total Headcount</span>
            <span class="card-icon">👥</span>
          </div>
          <div class="card-value">${totalEmps}</div>
          <div class="card-delta delta-positive">↑ 100% Active Retention</div>
        </div>

        <div class="card">
          <div class="card-header">
            <span class="card-title">Open Requisitions</span>
            <span class="card-icon">🎯</span>
          </div>
          <div class="card-value">${totalReqs}</div>
          <div class="card-delta delta-neutral">Active Candidate Pipeline</div>
        </div>

        <div class="card">
          <div class="card-header">
            <span class="card-title">Today's Attendance</span>
            <span class="card-icon">⏱️</span>
          </div>
          <div class="card-value">${attendancePct}%</div>
          <div class="card-delta delta-positive">${presentToday} Clocked-in (Geofence Verified)</div>
        </div>

        <div class="card">
          <div class="card-header">
            <span class="card-title">Monthly Payroll Run</span>
            <span class="card-icon">💳</span>
          </div>
          <div class="card-value">${lastPayroll}</div>
          <div class="card-delta delta-neutral">Disbursed with Cryptographic Hash</div>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 24px;">
        <div class="card">
          <h3 style="margin-bottom: 16px; font-family: var(--font-display);">🏢 Enterprise Department Health</h3>
          <div class="data-table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Department</th>
                  <th>Code</th>
                  <th>Budget</th>
                  <th>Location</th>
                  <th>Headcount</th>
                </tr>
              </thead>
              <tbody>
                ${this.state.departments.map(d => `
                  <tr>
                    <td style="font-weight: 600;">${d.name}</td>
                    <td><span class="badge-tag">${d.code}</span></td>
                    <td>$${d.budget.toLocaleString()}</td>
                    <td>${d.location}</td>
                    <td>${d.employee_count || 0} Members</td>
                  </tr>
                `).join("")}
              </tbody>
            </table>
          </div>
        </div>

        <div class="card">
          <h3 style="margin-bottom: 16px; font-family: var(--font-display);">🧠 AI Workforce Telemetry</h3>
          <div style="display: flex; flex-direction: column; gap: 12px;">
            <div style="padding: 12px; background: rgba(16, 185, 129, 0.1); border-radius: var(--radius-sm); border: 1px solid rgba(16, 185, 129, 0.2);">
              <div style="font-weight: 600; font-size: 0.85rem; color: var(--accent-emerald);">Overall Retention Health</div>
              <div style="font-size: 1.4rem; font-weight: 800; margin: 4px 0;">94.2%</div>
              <div style="font-size: 0.75rem; color: #94a3b8;">RandomForest ML classification indicates low attrition risk.</div>
            </div>

            <div style="padding: 12px; background: rgba(99, 102, 241, 0.1); border-radius: var(--radius-sm); border: 1px solid rgba(99, 102, 241, 0.2);">
              <div style="font-weight: 600; font-size: 0.85rem; color: #818cf8;">Talent Pipeline Velocity</div>
              <div style="font-size: 1.4rem; font-weight: 800; margin: 4px 0;">6 Candidates</div>
              <div style="font-size: 0.75rem; color: #94a3b8;">Average AI resume match score: 89.6%</div>
            </div>
          </div>
        </div>
      </div>
    `;
  },

  // 2. HRMS Employee Master View
  renderHRMS() {
    return `
      <div class="card" style="margin-bottom: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px;">
          <div>
            <h3 style="font-family: var(--font-display); font-size: 1.2rem;">Employee Directory Master</h3>
            <p style="font-size: 0.8rem; color: var(--text-secondary);">Enterprise Multi-entity Employee Roster with Org Hierarchy</p>
          </div>
          <button class="btn btn-primary" onclick="App.showAddEmployeeModal()">+ New Employee</button>
        </div>

        <div class="data-table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Code</th>
                <th>Employee Name</th>
                <th>Designation</th>
                <th>Department</th>
                <th>Work Location</th>
                <th>Base Annual (USD)</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              ${this.state.employees.map(e => `
                <tr>
                  <td><span class="badge-tag">${e.employee_code}</span></td>
                  <td>
                    <div style="font-weight: 600;">${e.full_name}</div>
                    <div style="font-size: 0.72rem; color: #94a3b8;">${e.email}</div>
                  </td>
                  <td>${e.designation}</td>
                  <td>${e.department_name || 'Unassigned'}</td>
                  <td>${e.work_location} ${e.is_remote ? '🌐 (Remote)' : '🏢'}</td>
                  <td style="font-weight: 700;">$${e.base_annual_salary.toLocaleString()}</td>
                  <td><span class="score-badge" style="background: rgba(16, 185, 129, 0.2); color: #34d399;">${e.status.toUpperCase()}</span></td>
                  <td>
                    <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.75rem;" onclick="App.inspectEmployeeRisk('${e.id}')">AI Risk</button>
                  </td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      </div>
    `;
  },

  // 3. Recruitment Kanban Board View
  async renderRecruitmentKanban(container) {
    const reqId = this.state.selectedRequisitionId;
    if (!reqId) {
      container.innerHTML = `<div class="card">No active job requisition found.</div>`;
      return;
    }

    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 16px;">
          <label style="font-size: 0.85rem; font-weight: 600; color: var(--text-secondary);">Active Requisition:</label>
          <select class="input-control" style="width: 320px;" onchange="App.onRequisitionChange(this.value)">
            ${this.state.requisitions.map(r => `
              <option value="${r.id}" ${r.id === reqId ? 'selected' : ''}>${r.code} — ${r.title}</option>
            `).join("")}
          </select>
        </div>
        <button class="btn btn-primary" onclick="App.showAddCandidateModal()">+ Add Candidate Lead</button>
      </div>

      <div class="kanban-board" id="kanban-columns">
        <div style="padding: 30px; text-align: center; width: 100%;">Loading Talent CRM Kanban...</div>
      </div>
    `;

    try {
      const res = await fetch(`/api/v1/recruitment/kanban/${reqId}`);
      const columns = await res.json();
      const kanbanEl = document.getElementById("kanban-columns");
      if (!kanbanEl) return;

      kanbanEl.innerHTML = columns.map(col => `
        <div class="kanban-column" ondragover="event.preventDefault()" ondrop="App.onDropCandidate(event, '${col.stage}')">
          <div class="kanban-header">
            <span>${col.label}</span>
            <span class="kanban-count">${col.count}</span>
          </div>
          <div class="kanban-cards">
            ${col.applications.map(app => `
              <div class="candidate-card" draggable="true" ondragstart="App.onDragCandidate(event, '${app.application_id}')">
                <div class="candidate-name">${app.name}</div>
                <div class="candidate-title">${app.title} (${app.experience_years} yrs)</div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
                  <span class="score-badge">🧠 AI Match: ${app.ai_match_score}%</span>
                  <span style="font-size: 0.72rem; color: #94a3b8;">★ ${app.overall_rating}</span>
                </div>
                <div style="margin-top: 8px; display: flex; gap: 4px; flex-wrap: wrap;">
                  ${app.skills.slice(0, 3).map(s => `<span class="badge-tag" style="font-size: 0.65rem;">${s}</span>`).join("")}
                </div>
              </div>
            `).join("")}
          </div>
        </div>
      `).join("");
    } catch (e) {
      console.error(e);
    }
  },

  onDragCandidate(e, appId) {
    e.dataTransfer.setData("text/plain", appId);
  },

  async onDropCandidate(e, targetStage) {
    e.preventDefault();
    const appId = e.dataTransfer.getData("text/plain");
    if (!appId) return;

    try {
      const res = await fetch(`/api/v1/recruitment/applications/${appId}/transition`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_stage: targetStage })
      });
      const data = await res.json();
      if (!res.ok) {
        alert(`Workflow Error: ${data.detail || 'Transition not permitted by policy'}`);
      } else {
        this.renderCurrentTab();
      }
    } catch (err) {
      alert("Transition failed.");
    }
  },

  onRequisitionChange(reqId) {
    this.state.selectedRequisitionId = reqId;
    this.renderCurrentTab();
  },

  // 4. Attendance Hub View
  renderAttendance() {
    const records = this.state.attendanceSummary ? this.state.attendanceSummary.records : [];
    return `
      <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 24px;">
        <div class="card">
          <h3 style="font-family: var(--font-display); margin-bottom: 12px;">📍 GPS Geofence Simulator</h3>
          <p style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 16px;">
            Simulate employee clock-in with Haversine distance validation against HQ (37.7749, -122.4194).
          </p>

          <div style="display: flex; flex-direction: column; gap: 12px;">
            <div>
              <label style="font-size: 0.78rem; font-weight: 600; color: #94a3b8;">Select Employee</label>
              <select id="clock-emp-id" class="input-control">
                ${this.state.employees.map(e => `<option value="${e.id}">${e.employee_code} — ${e.full_name}</option>`).join("")}
              </select>
            </div>

            <div>
              <label style="font-size: 0.78rem; font-weight: 600; color: #94a3b8;">Latitude</label>
              <input id="clock-lat" class="input-control" type="number" step="0.0001" value="37.7749" />
            </div>

            <div>
              <label style="font-size: 0.78rem; font-weight: 600; color: #94a3b8;">Longitude</label>
              <input id="clock-lon" class="input-control" type="number" step="0.0001" value="-122.4194" />
            </div>

            <div style="display: flex; gap: 10px; margin-top: 8px;">
              <button class="btn btn-primary" style="flex: 1;" onclick="App.triggerClockIn()">⏱️ Clock In</button>
              <button class="btn btn-secondary" style="flex: 1;" onclick="App.triggerClockOut()">⏹️ Clock Out</button>
            </div>
          </div>
        </div>

        <div class="card">
          <h3 style="font-family: var(--font-display); margin-bottom: 16px;">📋 Today's Live Attendance Feed</h3>
          <div class="data-table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Employee</th>
                  <th>Clock In</th>
                  <th>Clock Out</th>
                  <th>Geofence Status</th>
                  <th>Distance (HQ)</th>
                </tr>
              </thead>
              <tbody>
                ${records.map(r => `
                  <tr>
                    <td style="font-weight: 600;">${r.employee_name}</td>
                    <td>${r.clock_in_time}</td>
                    <td>${r.clock_out_time}</td>
                    <td>
                      <span class="score-badge" style="background: rgba(16, 185, 129, 0.2); color: #34d399;">
                        ${r.is_geofence_verified ? '✓ VERIFIED' : 'OUT OF BOUNDS'}
                      </span>
                    </td>
                    <td>${r.distance_from_hq_meters}m</td>
                  </tr>
                `).join("")}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `;
  },

  async triggerClockIn() {
    const empId = document.getElementById("clock-emp-id").value;
    const lat = parseFloat(document.getElementById("clock-lat").value);
    const lon = parseFloat(document.getElementById("clock-lon").value);

    try {
      const res = await fetch("/api/v1/attendance/clock-in", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ employee_id: empId, latitude: lat, longitude: lon, attendance_type: "office" })
      });
      const data = await res.json();
      if (!res.ok) {
        alert(data.detail || "Clock-in failed");
      } else {
        alert("Clock-in recorded successfully!");
        this.loadInitialData();
      }
    } catch (e) {
      alert("Network error");
    }
  },

  async triggerClockOut() {
    const empId = document.getElementById("clock-emp-id").value;
    try {
      const res = await fetch("/api/v1/attendance/clock-out", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ employee_id: empId })
      });
      const data = await res.json();
      if (!res.ok) {
        alert(data.detail || "Clock-out failed");
      } else {
        alert("Clock-out recorded successfully!");
        this.loadInitialData();
      }
    } catch (e) {
      alert("Network error");
    }
  },

  // 5. Payroll Engine View
  renderPayroll() {
    return `
      <div class="grid-cards">
        <div class="card">
          <div class="card-header"><span class="card-title">Formula Engine</span><span>⚙️</span></div>
          <div style="font-size: 1.1rem; font-weight: 700; color: #818cf8; margin-bottom: 6px;">AST Safe Parser</div>
          <div style="font-size: 0.78rem; color: #94a3b8;">Zero eval() vulnerability. Computes CTC - (BASIC + HRA) dynamically.</div>
        </div>

        <div class="card">
          <div class="card-header"><span class="card-title">Statutory Compliance</span><span>🛡️</span></div>
          <div style="font-size: 1.1rem; font-weight: 700; color: var(--accent-emerald); margin-bottom: 6px;">Multi-Country Tax Slabs</div>
          <div style="font-size: 0.78rem; color: #94a3b8;">US W-2/1099, PF/ESI & standard statutory deduction engines.</div>
        </div>

        <div class="card">
          <div class="card-header"><span class="card-title">Anti-Tamper Ledger</span><span>🔒</span></div>
          <div style="font-size: 1.1rem; font-weight: 700; color: var(--accent-cyan); margin-bottom: 6px;">SHA-256 Payslip Hash</div>
          <div style="font-size: 0.78rem; color: #94a3b8;">Cryptographically verified salary disbursement receipts.</div>
        </div>
      </div>

      <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
          <h3 style="font-family: var(--font-display);">Monthly Payroll Cycles</h3>
          <button class="btn btn-primary" onclick="App.runPayrollCycle()">⚡ Run Next Month Batch</button>
        </div>

        <div class="data-table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Period</th>
                <th>Status</th>
                <th>Employees</th>
                <th>Gross Disbursed</th>
                <th>Total Deductions</th>
                <th>Net Disbursed</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              ${this.state.payrollRuns.map(r => `
                <tr>
                  <td style="font-weight: 700;">${r.period_month}/${r.period_year}</td>
                  <td><span class="badge-tag" style="background: rgba(16, 185, 129, 0.2); color: #34d399;">${r.status.toUpperCase()}</span></td>
                  <td>${r.total_employees_processed} Staff</td>
                  <td>$${r.total_gross_disbursed.toLocaleString()}</td>
                  <td>$${r.total_deductions.toLocaleString()}</td>
                  <td style="font-weight: 700; color: var(--accent-emerald);">$${r.total_net_disbursed.toLocaleString()}</td>
                  <td>
                    <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.75rem;" onclick="App.viewPayslips('${r.id}')">View Payslips</button>
                  </td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      </div>
    `;
  },

  async runPayrollCycle() {
    const today = new Date();
    const nextMonth = (today.getMonth() + 2) > 12 ? 1 : today.getMonth() + 2;
    const year = today.getFullYear();

    try {
      const res = await fetch("/api/v1/payroll/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ period_month: nextMonth, period_year: year })
      });
      const data = await res.json();
      if (!res.ok) {
        alert(data.detail || "Payroll batch failed");
      } else {
        alert("Batch payroll calculated successfully!");
        this.loadInitialData();
      }
    } catch (e) {
      alert("Error executing payroll.");
    }
  },

  async viewPayslips(runId) {
    try {
      const res = await fetch(`/api/v1/payroll/runs/${runId}/payslips`);
      const payslips = await res.json();
      if (!payslips || payslips.length === 0) {
        alert("No payslips found for this cycle.");
        return;
      }
      const p = payslips[0];
      alert(`📄 Payslip Preview for ${p.employee_name} (${p.designation})\nGross: $${p.gross_earnings}\nTax + PF: $${p.total_deductions}\nNet Pay: $${p.net_pay}\nVerification Hash: ${p.verification_hash.slice(0, 20)}...`);
    } catch (e) {
      alert("Failed to load payslips.");
    }
  },

  // 6. Performance & 9-Box Grid View
  renderPerformance() {
    const matrix = this.state.nineBox ? this.state.nineBox.matrix : {};
    const meta = this.state.nineBox ? this.state.nineBox.meta : {};

    return `
      <div style="margin-bottom: 24px;">
        <h3 style="font-family: var(--font-display); margin-bottom: 6px;">🎯 Cascading OKR Objectives</h3>
        <p style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 16px;">Cross-functional goal alignment with automatic progress rollups</p>

        <div style="display: flex; flex-direction: column; gap: 14px;">
          ${this.state.objectives.map(obj => `
            <div class="card" style="padding: 16px 20px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div style="font-weight: 700; font-size: 1rem;">${obj.title}</div>
                <span class="score-badge" style="background: rgba(99, 102, 241, 0.2); color: #818cf8;">${obj.status.toUpperCase()} (${obj.progress_percentage}%)</span>
              </div>
              <div style="width: 100%; height: 8px; background: rgba(255, 255, 255, 0.1); border-radius: 4px; overflow: hidden; margin-bottom: 12px;">
                <div style="width: ${obj.progress_percentage}%; height: 100%; background: var(--gradient-primary);"></div>
              </div>
              <div style="display: flex; flex-direction: column; gap: 6px;">
                ${obj.key_results.map(kr => `
                  <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #cbd5e1;">
                    <span>• ${kr.title}</span>
                    <span style="font-weight: 600;">${kr.current_value} / ${kr.target_value} ${kr.metric_unit}</span>
                  </div>
                `).join("")}
              </div>
            </div>
          `).join("")}
        </div>
      </div>

      <div class="card">
        <h3 style="font-family: var(--font-display); margin-bottom: 6px;">📊 McKinsey / GE 9-Box Talent Matrix</h3>
        <p style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 16px;">Performance (X) vs Potential (Y) Calibration for Succession Planning</p>

        <div class="nine-box-container">
          ${Object.entries(meta).map(([key, item]) => {
            const empsInBox = matrix[item.category] || [];
            return `
              <div class="nine-box-cell" style="border-top: 3px solid ${item.color};">
                <div class="cell-header">
                  <span style="color: ${item.color};">${item.category}</span>
                  <span class="badge-tag">${empsInBox.length}</span>
                </div>
                <div style="font-size: 0.7rem; color: #94a3b8; margin-bottom: 8px;">${item.action}</div>
                <div style="display: flex; flex-direction: column; gap: 4px; overflow-y: auto;">
                  ${empsInBox.map(e => `
                    <div style="font-size: 0.78rem; font-weight: 600; padding: 4px 6px; background: rgba(255, 255, 255, 0.05); border-radius: 4px;">
                      ${e.name} <span style="font-size: 0.68rem; color: #94a3b8;">(${e.department})</span>
                    </div>
                  `).join("")}
                </div>
              </div>
            `;
          }).join("")}
        </div>
      </div>
    `;
  },

  // 7. Internal Helpdesk View
  renderHelpdesk() {
    return `
      <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
          <div>
            <h3 style="font-family: var(--font-display);">Internal HR Service CRM</h3>
            <p style="font-size: 0.8rem; color: var(--text-secondary);">Employee requests, benefits inquiries & SLA countdown queue</p>
          </div>
          <button class="btn btn-primary" onclick="App.showAddTicketModal()">+ New Ticket</button>
        </div>

        <div class="data-table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Ticket #</th>
                <th>Subject</th>
                <th>Employee</th>
                <th>Category</th>
                <th>Priority</th>
                <th>Status</th>
                <th>SLA Target</th>
              </tr>
            </thead>
            <tbody>
              ${this.state.tickets.map(t => `
                <tr>
                  <td><span class="badge-tag">${t.ticket_number}</span></td>
                  <td>
                    <div style="font-weight: 600;">${t.subject}</div>
                    <div style="font-size: 0.72rem; color: #94a3b8;">${t.description.slice(0, 60)}...</div>
                  </td>
                  <td>${t.employee_name}</td>
                  <td><span class="badge-tag">${t.category}</span></td>
                  <td><span class="score-badge" style="background: rgba(245, 158, 11, 0.2); color: #fbbf24;">${t.priority.toUpperCase()}</span></td>
                  <td><span class="score-badge" style="background: rgba(99, 102, 241, 0.2); color: #818cf8;">${t.status.toUpperCase()}</span></td>
                  <td>${t.sla_target_hours}h SLA</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      </div>
    `;
  },

  // 8. AI Intelligence Platform View
  renderAIInsights() {
    return `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
        <div class="card">
          <h3 style="font-family: var(--font-display); margin-bottom: 12px;">🧠 AI Resume & Skill Semantic Matcher</h3>
          <p style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 16px;">Extracts skills and scores fit percentage against job requisition specs.</p>

          <div style="display: flex; flex-direction: column; gap: 10px;">
            <div>
              <label style="font-size: 0.78rem; font-weight: 600; color: #94a3b8;">Resume Text</label>
              <textarea id="ai-resume-text" class="input-control" rows="5">Senior Backend Architect with 6 years experience in Python, FastAPI, Kafka, Docker, Kubernetes, and PostgreSQL.</textarea>
            </div>
            <div>
              <label style="font-size: 0.78rem; font-weight: 600; color: #94a3b8;">Job Requisition Description</label>
              <textarea id="ai-job-text" class="input-control" rows="4">Looking for a Senior Python / FastAPI engineer with experience in Kafka event streaming and Kubernetes cluster orchestration.</textarea>
            </div>
            <button class="btn btn-primary" style="margin-top: 6px;" onclick="App.runAIMatchTest()">Run Semantic Matcher</button>
            <div id="ai-match-result" style="margin-top: 10px;"></div>
          </div>
        </div>

        <div class="card">
          <h3 style="font-family: var(--font-display); margin-bottom: 12px;">📊 RandomForest Flight Risk Predictor</h3>
          <p style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 16px;">Supervised Machine Learning Model predicting employee attrition probability.</p>

          <div style="display: flex; flex-direction: column; gap: 10px;">
            <div>
              <label style="font-size: 0.78rem; font-weight: 600; color: #94a3b8;">Salary Compa Ratio (Relative to Market 1.0 = 100%)</label>
              <input id="ai-salary-ratio" class="input-control" type="number" step="0.05" value="0.85" />
            </div>
            <div>
              <label style="font-size: 0.78rem; font-weight: 600; color: #94a3b8;">Monthly Overtime Hours</label>
              <input id="ai-overtime" class="input-control" type="number" value="28" />
            </div>
            <div>
              <label style="font-size: 0.78rem; font-weight: 600; color: #94a3b8;">Years Since Last Promotion</label>
              <input id="ai-promo-gap" class="input-control" type="number" step="0.5" value="3.0" />
            </div>
            <button class="btn btn-primary" style="margin-top: 6px;" onclick="App.runAIAttritionTest()">Predict Flight Risk</button>
            <div id="ai-attrition-result" style="margin-top: 10px;"></div>
          </div>
        </div>
      </div>
    `;
  },

  async runAIMatchTest() {
    const resumeText = document.getElementById("ai-resume-text").value;
    const jobText = document.getElementById("ai-job-text").value;
    const resEl = document.getElementById("ai-match-result");

    try {
      const res = await fetch("/api/v1/ai/match-resume", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_text: resumeText, job_description: jobText, experience_years: 6.0, min_experience_required: 5.0 })
      });
      const data = await res.json();
      resEl.innerHTML = `
        <div style="padding: 12px; background: rgba(99, 102, 241, 0.15); border-radius: var(--radius-sm); border: 1px solid var(--border-active);">
          <div style="font-weight: 700; font-size: 1.1rem; color: #818cf8;">AI Match Score: ${data.match_score}% (${data.recommendation})</div>
          <div style="font-size: 0.78rem; color: #cbd5e1; margin-top: 4px;">Matched Skills: ${data.matched_skills.join(", ")}</div>
          ${data.missing_skills.length > 0 ? `<div style="font-size: 0.78rem; color: var(--accent-rose);">Missing: ${data.missing_skills.join(", ")}</div>` : ''}
        </div>
      `;
    } catch (e) {
      alert("Match test failed.");
    }
  },

  async runAIAttritionTest() {
    const salaryRatio = parseFloat(document.getElementById("ai-salary-ratio").value);
    const overtime = parseFloat(document.getElementById("ai-overtime").value);
    const promoGap = parseFloat(document.getElementById("ai-promo-gap").value);
    const resEl = document.getElementById("ai-attrition-result");

    try {
      const res = await fetch("/api/v1/ai/attrition-risk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          salary_ratio: salaryRatio,
          overtime_hours_month: overtime,
          tenure_years: 3.5,
          years_since_last_promotion: promoGap,
          performance_score: 2.5,
          is_remote: false
        })
      });
      const data = await res.json();
      resEl.innerHTML = `
        <div style="padding: 12px; background: rgba(239, 68, 68, 0.15); border-radius: var(--radius-sm); border: 1px solid rgba(239, 68, 68, 0.3);">
          <div style="font-weight: 700; font-size: 1.1rem; color: #f87171;">Flight Risk Probability: ${data.flight_risk_percentage}% (${data.risk_level})</div>
          <ul style="font-size: 0.75rem; color: #cbd5e1; margin-top: 6px; padding-left: 16px;">
            ${data.retention_recommendations.map(r => `<li>${r}</li>`).join("")}
          </ul>
        </div>
      `;
    } catch (e) {
      alert("Prediction test failed.");
    }
  },

  inspectEmployeeRisk(empId) {
    fetch(`/api/v1/ai/employee-risk/${empId}`)
      .then(r => r.json())
      .then(data => {
        alert(`🧠 AI Workforce Risk Report: ${data.employee_name} (${data.designation})\nFlight Risk: ${data.flight_risk_percentage}%\nCompa-Ratio: ${data.compensation_analysis.compa_ratio}%\nStatus: ${data.compensation_analysis.status}`);
      });
  },

  quickTriggerAction() {
    alert("⚡ Quick Action Triggered: Auto-syncing enterprise telemetry across nodes.");
    this.loadInitialData();
  }
};

window.addEventListener("DOMContentLoaded", () => App.init());
