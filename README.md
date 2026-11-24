# RelayAI: Resilient LLM Gateway

> **AI, without the interruption.**

A resilient LLM gateway featuring API key failover, intelligent response caching, and multi-turn chat session management. Built for production reliability with per-request token isolation, persistent multi-turn SQLite conversation history across container restarts, and comprehensive end-to-end resilience.

---

## 1. Live URLs
- **Frontend Application:** https://relayai-frontend.onrender.com
- **Backend API Gateway:** https://relayai-backend-z6pw.onrender.com
- **Interactive API Documentation:** https://relayai-backend-z6pw.onrender.com/docs
- **Health Endpoint:** https://relayai-backend-z6pw.onrender.com/health

---

## 2. Run Locally: With Docker and Without

### Option A: With Docker (Recommended)
Prerequisites: Docker Engine 24+ and Docker Compose v2+ (or Docker Desktop).

1. Clone repository:
   ```bash
   git clone https://github.com/Shruti152004/relayai-resilient-llm-gateway.git
   cd relayai-resilient-llm-gateway
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env and supply your real API keys for LLM_API_KEYS (at least two keys separated by comma)
   ```

3. Spin up full stack:
   Using Make:
   ```bash
   make up
   ```
   Or using Docker Compose directly:
   ```bash
   docker compose up --build -d
   ```
   * **Frontend UI:** [http://localhost:3000](http://localhost:3000)
   * **Backend API:** [http://localhost:8000](http://localhost:8000)
   * **Backend Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
   * **Frontend Proxied Health Check:** [http://localhost:3000/health](http://localhost:3000/health)
   * **Interactive OpenAPI Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

4. Check container status:
   ```bash
   make status
   # or: docker compose ps
   ```

5. View live logs:
   ```bash
   make logs
   # or: docker compose logs -f
   ```

6. Tear down stack (safely preserves SQLite data volume):
   ```bash
   make down
   # or: docker compose down
   ```

---

### Option B: Without Docker (Local Development)

#### Backend Setup (Python 3.11):
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp ../.env.example .env
# Edit .env with your real API keys
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup (Node 20+):
```bash
cd frontend
npm install
npm run dev -- --port 3000
```

---

## 3. Design Decisions: Key Fallback, Caching, SQLite Session Storage

### Key Fallback Mechanism
* API keys are loaded strictly from the `LLM_API_KEYS` environment variable and mapped to internal aliases (`key_1`, `key_2`, ..., `key_N`). Raw keys are never logged, sent over the wire, or stored in frontend bundles.
* When a key returns HTTP 429, quota exhaustion, or 5xx server errors, the gateway catches the exception, increments `fallback_attempts`, and transparently routes the request to the next available key.
* If all keys fail, the API responds with HTTP 503 `{"detail": "all providers unavailable"}` and ensures no erroneous data is recorded to SQLite history.

### Response Caching & Deterministic Token Preservation
* Caching uses LiteLLM's cache subsystem keyed on `(model, system_prompt + message_history + new_message)`.
* Requests containing `X-Simulate-Failure` explicitly bypass caching to ensure failover mechanics are exercised during testing.
* Cache hits return `resolution_source: "LLM_CACHE"`, `key_id: null`, and `fallback_attempts: 0`.
* The original provider-reported `input_tokens` and `output_tokens` are preserved from the cached response object without heuristics or estimation.

### SQLite Multi-Turn Storage & Volume Persistence
* **Schema & Engine:** Storage is managed through two relational tables: `sessions` (holding active system prompts per session) and `messages` (holding chronological user and assistant records). Write-Ahead Logging (`PRAGMA journal_mode=WAL;`) and foreign key constraints (`PRAGMA foreign_keys=ON;`) are activated on startup.
* **System Prompt Isolation:** System prompts are persisted per session for subsequent conversation context but excluded from public history endpoints (`GET /sessions/{session_id}/messages`).
* **Local Docker Volume Persistence (Verified):** The application database is configured at `/data/app.db`. In `docker-compose.yml`, this path is mounted to a dedicated named volume (`lyftra_sqlite_data` mapped to `/data`). Database state strictly persists across container stopping, container removal (`docker compose down`), and container recreation (`docker compose up -d`), as verified with session `s-docker-persist`.
* **Cloud Deployment Storage Model (Render Free Tier):**
  * The cloud deployment is hosted on Render's Free tier.
  * Render Free Web Services operate on an **ephemeral container filesystem**. Render's platform architecture does not support persistent disks on the Free plan (persistent disks require a paid Starter plan of $7/mo + $0.25/GB/mo).
  * Consequently, cloud-deployed SQLite data is ephemeral: it is retained during active runtime but resets when the free container automatically spins down after 15 minutes of inactivity, restarts, or redeploys.
  * In strict adherence to assignment requirements requiring pure SQLite (without external database add-ons like PostgreSQL, Redis, or cloud storage daemons), cloud persistence is transparently bound to Render's free-tier filesystem characteristics.
  * Full, verified persistence across the tested Docker container recreation is operational via the local Docker Compose environment.

---

## 4. Verification: How to See Failover, Cache Hits and Per-Message Token Usage

### 1. Test Automatic Key Failover
Send a message with `X-Simulate-Failure: key_1=429`:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-Simulate-Failure: key_1=429" \
  -d '{"session_id": "s-test-failover", "message": "Explain quantum computing briefly."}'
```
**Expected Result:** HTTP 200 with `key_id: "key_2"`, `fallback_attempts: 1`, and `resolution_source: "LIVE_INFERENCE"`.

### 2. Test Complete Exhaustion Handling
Send a message with `X-Simulate-Failure: *=429`:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-Simulate-Failure: *=429" \
  -d '{"session_id": "s-test-exhaust", "message": "This will fail gracefully."}'
```
**Expected Result:** HTTP 503 with body `{"detail": "all providers unavailable"}`. 0 failed messages written to SQLite.

### 3. Test Response Caching
Send the same initial message in two distinct sessions:
```bash
# First Call (Live Inference)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "s-cache-1", "message": "What is the boiling point of water?"}'

# Second Call in New Session (Cache Hit)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "s-cache-2", "message": "What is the boiling point of water?"}'
```
**Expected Result:** Second response returns `resolution_source: "LLM_CACHE"`, `key_id: null`, `fallback_attempts: 0`, identical input/output token counts, and latency under 30ms.

### 4. Test Multi-Turn Conversation Memory
Send multiple messages within the same session ID:
```bash
# Turn 1
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"session_id": "s-cosmos-1", "message": "My favorite planet is Neptune."}'

# Turn 2
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"session_id": "s-cosmos-1", "message": "Which planet is my favorite?"}'
```
Retrieve full chronological history:
```bash
curl http://localhost:8000/sessions/s-cosmos-1/messages
```

### 5. Test SQLite Named-Volume Persistence Across Container Recreation (Local Docker)

Demonstrate that conversation history survives container teardown and recreation:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "s-docker-persist", "message": "Ping from Docker container test"}'

docker compose down
docker compose up -d

curl http://localhost:8000/sessions/s-docker-persist/messages
```

**Expected Result:** HTTP 200 returning the intact conversation history (`s-docker-persist` containing both user and assistant messages) directly from the mounted `/data/app.db` volume. Verified that the tested session history survived container removal and recreation.

---

## 5. Setup Used: Editor and AI Tools
* **Development Environment:** Visual Studio Code, Python 3.11, Node.js 20, Docker Desktop on Windows/Linux.
* **AI Architecture & Coding Assistant:** Antigravity (Google DeepMind).
* **Testing & Quality Tools:** Pytest, Vitest, Playwright, HTTPX, Pydantic V2, Docker Compose.

---

## 6. Bonus Features: What Was Added and Why
* **Failover Simulation Header Hook:** Top-level UI test hook dropdown to trigger `key_1=429`, `key_1=500`, and `*=429` scenarios on-demand.
* **Sensitive Log Redaction Filter:** Custom Python logging filter actively intercepting and redacting raw API keys (`AIzaSy...`, `sk-...`, `gsk-...`) across all standard and Uvicorn log streams.
* **Multi-Turn System Prompt Persona Input:** UI control to inject and persist custom personas per session across all subsequent conversation turns while keeping public message history clean.
* **Nginx Reverse Proxy in Docker:** Transparently proxies API calls from frontend to backend within Docker, eliminating hardcoded URLs and CORS issues.
