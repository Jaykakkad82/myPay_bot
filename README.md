# myPayments • LLM Agents for API Products (Demo)

A full demo showcasing an **agentic orchestration pattern** over an API product.  
It includes:

- Two assistants: **single-agent** and **multi-agent** (LangGraph-based)  
- A **Spring Boot payments API** (customers, transactions, payments)  
- An **MCP server** that exposes the API as tools  
- A **React chat UI**  
- **Server-side sessions, access tiers, and usage limits** backed by DynamoDB (or DynamoDB Local)  
- Optional **email notifications** via Amazon SES SMTP for write events  

---

## 📂 What’s Inside

.
├── agent_multi/ # LangGraph multi-agent (orchestrator, data, execution, compliance, notifier, summarizer)
├── agent/ # Single-agent baseline (for comparison/testing)
├── mcpServer/ # MCP server that wraps the Spring Boot API as tools
├── frontEnd/ # Vite + React + Tailwind chat UI
└── myPayment/ # Spring Boot API (customers/transactions/payments)


---

## 🏗 Architecture (High Level)

User → frontEnd (React) → agent_multi (FastAPI)

orchestrator (planner) → plan of steps
├── data_agent (read-only tools)
├── execution_agent (write tools) → optional notifier (SES email)
└── summarizer (renders tables + follow-ups)

Agents → MCP server → Spring Boot API

Session + limits → DynamoDB (session profile + usage windows)

UI → X-Session-Id to bind requests to server-side session


---

## ⚡ Quick Start (Local)

### Prerequisites
- Node 18+  
- Java 17+  
- Python 3.11  
- Docker (for DynamoDB Local)  
- AWS CLI (optional, for local setup)  

### 1. Run DynamoDB Local
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

###  2. Start Spring Boot API
```bash
cd myPayment
./mvnw spring-boot:run   # runs on http://localhost:8080
```

### 3. Start MCP Server
```bash
cd mcpServer
# configure API base URL in env (see folder README)
uvicorn main:app --port 12136 --reload
```

### 4. Start Multi-Agent Backend
```bash
cd agent_multi
# create .env (see folder README), then:
uvicorn app:app --port 8010 --reload
```

###  5. Start Frontend
```bash
cd frontEnd
npm i
# set VITE_AGENT_API_URL=http://localhost:8010 in .env.local (optional)
npm run dev   # http://localhost:5173
```



☁️ Deployment (AWS Outline)

- API (Spring Boot): ECS/Fargate or EKS; RDS Postgres/Aurora; ALB in front

- MCP server: ECS service in same VPC (reach API via service discovery or internal ALB)

- agent_multi: ECS service with AWS_REGION, DDB_TABLE, SMTP/SES creds, MCP_URL

- DynamoDB: Managed DynamoDB (no endpoint override, TTL enabled)

- SES SMTP: Verify sender/recipient in sandbox; port 587 (STARTTLS)

- frontEnd: S3 + CloudFront or any static host; configure VITE_AGENT_API_URL



⚠️ Notes & Gotchas

- DynamoDB Numbers: boto3 requires Decimal; coercion is applied where needed

- Reserved Attributes: use ExpressionAttributeNames (e.g., #f for counter)

- Sessions: UI must call /session/start and send X-Session-Id header with every request

- Limits: Windows stored as PK=SESSION#{id}, SK=WIN#{metric}#{bucket}

- SES Sandbox: Both sender & recipient emails must be verified (or move account to prod)


📜 License

MIT 