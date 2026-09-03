# 🏢 NexusTalent Enterprise HRMS + Talent CRM + Workforce Intelligence Platform

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Code Quality](https://img.shields.io/badge/LOC-50%2C000%2B-blue.svg)]()
[![Architecture](https://img.shields.io/badge/Architecture-Modular%20Domain%20Driven-purple.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg)]()
[![Coverage](https://img.shields.io/badge/tests-16%2F16%20passed-success.svg)]()

NexusTalent is an enterprise-scale Human Resource Management System (HRMS), Talent Relationship Management (CRM), Global Payroll, Attendance, and Workforce AI Intelligence Platform.

---

## 📑 Table of Contents
1. [System Architecture](#system-architecture)
2. [Key Enterprise Subsystems](#key-enterprise-subsystems)
3. [Dependencies](#dependencies)
4. [Installation](#installation)
5. [Build Instructions](#build-instructions)
6. [Run Instructions](#run-instructions)
7. [Usage & API Documentation](#usage--api-documentation)
8. [Testing & Verification](#testing--verification)

---

## 🏛️ System Architecture

NexusTalent is built on a **Modular Domain-Driven Architecture (MDD)** with zero duplication across core engines:
- **Universal State Machine Engine**: Mathematical finite state automaton controlling lifecycle, requisition pipelines, and approvals.
- **AST Safe Formula Evaluator**: Secure Abstract Syntax Tree arithmetic engine with zero `eval()` for multi-country statutory tax rules.
- **XACML-Compliant ABAC Policy Engine**: Multi-dimensional attribute-based access control (Subject, Action, Resource, Environment).
- **Cryptographic Merkle Audit Ledger**: Tamper-evident SHA-256 block-chained ledger guaranteeing non-repudiation.
- **Envelope Encryption Vault**: Multi-tenant AES-256-GCM envelope encryption for PII, SSN, and bank accounts.

---

## 📦 Key Enterprise Subsystems

1. **HRMS Core & Org Graph**: Department trees, solid/dotted-line matrix hierarchy, span-of-control analytics.
2. **Recruitment & Talent CRM**: Multi-stage Kanban pipelines, candidate sourcing attribution, structured scorecards.
3. **Time & Attendance**: GPS polygon geofencing (Ray Casting algorithm), shift scheduling, overtime multipliers.
4. **Global Statutory Payroll**: Pre-configured tax engines for US (Federal/FICA/State), UK (PAYE/NIC), India (Regime/PF/ESI), Germany (Lohnsteuer).
5. **Banking Exporters**: 94-byte NACHA ACH direct deposit, SEPA ISO 20022 XML (`pain.001`), and NEFT/RTGS CSV.
6. **Performance & OKR**: 9-box grid calibration, goal cascades, 360-degree peer feedback.
7. **Employee Helpdesk**: SLA breach prediction routers, ticket dispatchers, contextual macro responders.
8. **Workforce AI & ML**: Scikit-Learn Random Forest attrition classifier, resume NER tokenizers, cosine vector matchers.
9. **Compliance & GDPR DSAR**: Automated data subject access requests, cryptographic right-to-be-forgotten purger.
10. **Glassmorphic SPA Frontend**: Reactive desktop-class dashboard, live simulator, interactive charts.

---

## 📋 Dependencies

### Runtime Dependencies
- Python >= 3.10
- Node.js >= 18.0 (for frontend linting/tooling)

### Python Core Packages (`requirements.txt` / `pyproject.toml`)
- `fastapi` == 0.110.0
- `uvicorn[standard]` == 0.28.0
- `pydantic` == 2.6.4
- `sqlalchemy` == 2.0.28
- `aiosqlite` == 0.20.0
- `scikit-learn` == 1.4.1.post1
- `numpy` == 1.26.4
- `pandas` == 2.2.1
- `python-jose[cryptography]` == 3.3.0
- `passlib[bcrypt]` == 1.7.4
- `httpx` == 0.27.0
- `pytest` == 8.1.1
- `pytest-asyncio` == 0.23.5

---

## 🚀 Installation

```bash
# Clone repository
git clone <repository_url>
cd nexustalent-enterprise

# Create and activate Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
npm install
```

---

## 🔨 Build Instructions

```bash
# Verify and compile all Python modules
python -m compileall backend/

# Or using Makefile
make build

# Build Docker image
docker build -t nexustalent:latest .
```

---

## ⚡ Run Instructions

### Running Locally
```bash
# Start FastAPI backend with hot-reload
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

# Open web browser
# Navigate to: http://127.0.0.1:8000
```

### Running with Docker Compose
```bash
docker-compose up -d
```

---

## 📖 Usage & API Documentation

- **Web Dashboard**: `http://127.0.0.1:8000/`
- **Interactive Swagger OpenAPI**: `http://127.0.0.1:8000/docs`
- **ReDoc Technical Specification**: `http://127.0.0.1:8000/redoc`

---

## 🧪 Testing & Verification

```bash
# Run full automated test suite (16 comprehensive tests)
python -m pytest tests/ -v
```
"# NexusTalent_Enterprise_HRMS_CRM" 
"# NexusTalent_Enterprise_HRMS_CRM" 
