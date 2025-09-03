# myPayments • Agentic API Demo

<p align="left">
  <img alt="status" src="https://img.shields.io/badge/status-active-22c55e" />
  <img alt="python" src="https://img.shields.io/badge/Python-3.11+-3776AB" />
  <img alt="node" src="https://img.shields.io/badge/Node-18+-43853d" />
  <img alt="license" src="https://img.shields.io/badge/license-MIT-000" />
</p>

A production-leaning **agentic demo** for API products. It showcases:
- **Multi‑agent orchestration** (LangGraph) vs **single agent** baseline
- **MCP server** wrapping a Spring Boot API (customers / transactions / payments)
- **Front‑end chat UI** with session limits, access tiers, and approval flow
- Optional **notifier** via SMTP/SES (email on write events)

---

## 🧭 What’s Inside

```
.
├── agent_multi/    # LangGraph multi-agent (orchestrator, data, execution, compliance, notifier, summarizer)
├── agent/          # Single-agent baseline (for comparison/testing)
├── mcpServer/      # MCP server that wraps the Spring Boot API
├── frontEnd/       # Vite + React + Tailwind chat UI
└── myPayment/      # Spring Boot API (customers/transactions/payments)
```

---

## 🏗️ Architecture (High Level)

```mermaid
graph TD;
  U[User] --> FE[FrontEnd React];
  FE --> API[agent_multi FastAPI];
  API --> ORCH[Orchestrator];
  ORCH --> DATA[Data Agent];
  ORCH --> EXEC[Execution Agent];
  EXEC --> COMP[Compliance];
  EXEC --> NOTIF[Notifier SES];
  DATA --> MCP[MCP Server];
  EXEC --> MCP;
  MCP --> SB[Spring Boot API];
  SB --> APPDB [PostgreSQL or mySQL];
  ORCH --> SUM[Summarizer];
  DATA --> SUM;
  EXEC --> SUM;
  API --> DDB[DynamoDB];
  FE -.-> DDB;

  classDef dim fill:#f6f6f7,stroke:#d1d5db,color:#111;
  classDef core fill:#eef2ff,stroke:#818cf8,color:#111;
  classDef integ fill:#ecfeff,stroke:#06b6d4,color:#111;
  class API,FE dim;
  class ORCH,DATA,EXEC,COMP,NOTIF,SUM core;
  class MCP,SB,DDB integ;
```

---

## ✨ Features

- **Agentic workflow**: Orchestrator → Data/Execution agents → Summarizer
- **Approvals**: Compliance node requests human approval before writes
- **Notifications**: SES/SMTP email on payment/transaction writes
- **Sessions & limits**: X‑Session‑Id header, access tiers, per‑minute/day meters in DynamoDB
- **Observability**: Trace chips, tool‑call viewer, frontend turn latency chip
- **Deterministic prompts**: Zero‑temperature routing with explicit op mapping

---

## 🚀 Quickstart (Local)

> Prereqs: Python 3.11+, Node 18+, Java 17+, Docker (for DynamoDB Local), AWS CLI v2 (optional for SES)

### 1) Backend: DynamoDB Local
```bash
docker run -d --name dynamodb-local -p 8000:8000 amazon/dynamodb-local

aws dynamodb create-table \
  --endpoint-url http://localhost:8000 \
  --table-name mp-runtime \
  --attribute-definitions AttributeName=PK,AttributeType=S AttributeName=SK,AttributeType=S \
  --key-schema AttributeName=PK,KeyType=HASH AttributeName=SK,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST

aws dynamodb update-time-to-live \
  --endpoint-url http://localhost:8000 \
  --table-name mp-runtime \
  --time-to-live-specification '{"Enabled":true,"AttributeName":"expiresAt"}'
```

Set env for local endpoint:
```bash
export AWS_REGION=us-east-1
export DDB_TABLE=mp-runtime
export DDB_ENDPOINT=http://localhost:8000
```

### 2) Spring Boot API (myPayment)
```bash
cd myPayment
./mvnw spring-boot:run
# API default: http://localhost:8080
```

### 3) MCP Server
```bash
cd mcpServer
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 12136
# MCP API default: http://localhost:12136
```

### 4) Agentic Backends
```bash
cd agent_multi
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=...

# Optional SES for email notifier
export SMTP_HOST=email-smtp.us-east-1.amazonaws.com
export SMTP_USER=AKIA...
export SMTP_PASS=xxxx
export SMTP_PORT=587
export SMTP_FROM=verified@yourdomain.com
export SMTP_TO=you@yourdomain.com

uvicorn main:app --reload --port 8010
# Health: http://localhost:8010/health
```

### 5) Frontend
```bash
cd frontEnd
npm i
VITE_AGENT_API_URL=http://localhost:8010 npm run dev
# Open http://localhost:5173
```

---

## 🔐 Sessions, Tiers & Limits

- UI calls **POST /session/start**, stores `mp_server_session_id` in localStorage
- Every request includes **X‑Session‑Id**
- **/session/limits** shows live meters (requests/min, tools/min, tokens/day)
- **/session/upgrade** accepts an access key → elevated/admin tier
- Counters & TTL windows are persisted in **DynamoDB** (per session)

---

## ⚙️ Configuration (env)

| Var | Default | Notes |
|---|---|---|
| `OPENAI_API_KEY` | — | LLM calls (LangChain / LangGraph) |
| `AWS_REGION` | `us-east-1` | For DynamoDB / SES |
| `DDB_TABLE` | `mp-runtime` | Session & usage store |
| `DDB_ENDPOINT` | *(unset)* | Set to `http://localhost:8000` for local |
| `SMTP_HOST` | — | SES SMTP endpoint |
| `SMTP_USER` / `SMTP_PASS` | — | SMTP creds |
| `SMTP_FROM` / `SMTP_TO` | — | Verified SES identities |

---

## 🧪 Try These

- “Show spend for customer 1 from 2025‑07‑01 to 2025‑07‑31 in USD.”  
- “Search transactions for customer 1 status COMPLETED.”  
- “Create a $45 USD groceries transaction for customer 1.” *(triggers approval + email)*

---

## 🩺 Troubleshooting

- **429 Too Many Requests:** You hit limits. Use “Enter access key,” or wait for the window to reset.  
- **SES 530 Authentication required:** Verify `SMTP_FROM` identity; use STARTTLS on 587.  
- **DynamoDB float error:** Use `Decimal` types (handled in code) for numeric counters.  
- **Same session in multiple tabs:** LocalStorage is per‑origin; use Incognito or clear key `mp_server_session_id`.

---

## 📄 License

MIT — do whatever you want; attribution appreciated.
