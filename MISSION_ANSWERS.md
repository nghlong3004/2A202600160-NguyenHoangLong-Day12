# Day 12 Lab — Mission Answers

> **Student:** Nguyễn Hoàng Long  
> **MSSV:** 2A202600160  
> **Date:** 2026-04-17

---

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found in `01-localhost-vs-production/develop/app.py`

Tìm được **9 vấn đề** trong file `app.py` (develop version):

| # | Vấn đề | Dòng | Giải thích |
|---|--------|------|-----------|
| 1 | **API key hardcode** | 17–18 | `OPENAI_API_KEY = "sk-hardcoded-fake-key-never-do-this"` và `DATABASE_URL` chứa password ghi thẳng trong code. Push lên GitHub → credentials bị lộ công khai. |
| 2 | **Không có config management** | 21–22 | `DEBUG = True` và `MAX_TOKENS = 500` là literal values, không đọc từ environment variables. Muốn thay đổi phải sửa code rồi re-deploy. |
| 3 | **Dùng `print()` thay vì structured logging** | 33, 38 | `print(f"[DEBUG] Got question: ...")` — không có log level, không filter được, không tích hợp được với log aggregation tools (ELK, Datadog, CloudWatch). |
| 4 | **Log ra secret** | 34 | `print(f"[DEBUG] Using key: {OPENAI_API_KEY}")` — in API key ra stdout. Nếu stdout được thu thập bởi monitoring system, secret bị leak ở nhiều nơi. |
| 5 | **Không có health check endpoint** | 42–43 | Không có `/health` → platform (Railway/Render/K8s) không biết khi nào container crash để tự động restart. |
| 6 | **`host="localhost"` — chỉ listen loopback** | 51 | Chỉ chạy được trên local machine. Trong Docker container hoặc trên cloud, cần bind `0.0.0.0` để nhận kết nối từ bên ngoài. |
| 7 | **Port hardcode** | 52 | `port=8000` cứng, không đọc từ `os.environ.get("PORT")`. Trên Railway/Render, PORT được inject qua env var, không phải lúc nào cũng là 8000. |
| 8 | **`reload=True` trong production** | 53 | Hot-reload tốn tài nguyên, gây restart bất ngờ khi file thay đổi. Chỉ nên dùng khi development. |
| 9 | **Không có graceful shutdown** | — | Không có signal handler cho `SIGTERM`. Khi container bị stop, requests đang xử lý bị cắt đột ngột → incomplete responses, potential data loss. |

**Vấn đề bổ sung (ngoài gợi ý lab):**
- **Không có authentication**: Endpoint `/ask` public, ai cũng gọi được → risk bị abuse, hết tiền LLM.
- **Không có rate limiting**: Không giới hạn số request → dễ bị DDoS.
- **Không có error handling**: Nếu mock LLM throw exception → bare 500 Internal Server Error.

---

### Exercise 1.2: Run basic version

```bash
cd 01-localhost-vs-production/develop
pip install -r requirements.txt
python app.py
```

**Kết quả:** Server khởi động thành công trên `localhost:8000`.

```bash
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
```

**Response:**
```json
{
    "answer": "Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận."
}
```

**Quan sát:**
- Chạy được trên local ✅
- Nhưng **KHÔNG production-ready** vì:
  - Chỉ nghe trên `localhost` (không accessible từ bên ngoài)
  - Secrets lộ trong source code
  - Không có monitoring/health check
  - Không handle shutdown gracefully
  - Debug mode bật → performance kém & security risk

---

### Exercise 1.3: Comparison table — Develop vs Production

So sánh `01-localhost-vs-production/develop/app.py` với `01-localhost-vs-production/production/app.py`:

| Feature | Develop (Basic) | Production (Advanced) | Tại sao quan trọng? |
|---------|----------------|----------------------|---------------------|
| **Config** | Hardcode trực tiếp (`OPENAI_API_KEY = "sk-..."`, `DEBUG = True`) | `config.py` dùng `os.getenv()` với dataclass, đọc từ env vars + `.env` file | Dễ thay đổi giữa dev/staging/prod mà không sửa code. Không commit secrets. Fail fast nếu thiếu config bắt buộc trong production. |
| **Health check** | ❌ Không có | ✅ `/health` (liveness probe) + `/ready` (readiness probe) + `/metrics` | Platform (Railway/K8s) cần biết container còn sống không để auto-restart. Load balancer dùng readiness probe để quyết định route traffic. |
| **Logging** | `print()` — plain text, log cả secrets | `logging` module + JSON format, **không log secrets**, chỉ log metadata (question_length, client_ip) | Structured JSON logs dễ parse, search, filter bởi log aggregation tools (ELK, Datadog). Không leak sensitive data. |
| **Shutdown** | Đột ngột — `Ctrl+C` kill ngay | Graceful — `signal.SIGTERM` handler + lifespan context manager, chờ in-flight requests hoàn thành | Khi deploy version mới hoặc scale down, requests đang xử lý không bị mất. User không nhận response bị cắt giữa chừng. |
| **Host binding** | `localhost` (127.0.0.1 only) | `0.0.0.0` (all interfaces) | Trong Docker/cloud, app cần listen trên all interfaces thì traffic mới vào được. `localhost` chỉ hoạt động trên chính máy đó. |
| **Port** | Hardcode `8000` | `int(os.getenv("PORT", "8000"))` | Cloud platforms (Railway, Render, Cloud Run) inject PORT qua env var. Nếu hardcode → app listen sai port → platform nghĩ app crash. |
| **Debug/Reload** | `reload=True` luôn bật | `reload=settings.debug` — chỉ bật khi `DEBUG=true` | Hot-reload tốn CPU, không ổn định, có thể restart bất ngờ. Production phải tắt. |
| **CORS** | ❌ Không có | ✅ `CORSMiddleware` với `allowed_origins` từ config | Kiểm soát domain nào được gọi API, ngăn chặn cross-site request abuse. |
| **Error handling** | Không validate input | `raise HTTPException(422)` nếu thiếu `question` | Trả response rõ ràng cho client thay vì crash với 500.  |
| **App metadata** | Title cứng `"My Agent"` | Từ config: `app_name`, `app_version`, `environment` | Biết chính xác version nào đang chạy, environment nào, giúp debug production issues. |

**Kết luận:** Production version tuân thủ **12-Factor App principles** — config từ env, stateless processes, port binding linh hoạt, logs as event streams, disposability (graceful shutdown). Basic version vi phạm hầu hết các nguyên tắc này.

---

## Part 2: Docker

### Exercise 2.1: Dockerfile questions

Đọc `02-docker/develop/Dockerfile`:

**1. Base image là gì?**

`python:3.11` — Full Python distribution (~1 GB), bao gồm OS (Debian), Python runtime, pip, và các build tools. Advantages: có sẵn mọi thứ. Disadvantage: image rất nặng.

**2. Working directory là gì?**

`/app` — Đây là thư mục làm việc bên trong container, set bởi `WORKDIR /app`. Tất cả lệnh `COPY`, `RUN`, `CMD` sau đó đều chạy relative to `/app`. Giống như `cd /app` trong terminal.

**3. Tại sao COPY requirements.txt trước?**

**Docker layer caching.** Mỗi instruction trong Dockerfile tạo một layer. Docker cache layer nào không thay đổi.

```dockerfile
COPY requirements.txt .      # Layer 1 — ít thay đổi
RUN pip install -r ...        # Layer 2 — chỉ rebuild khi requirements đổi
COPY app.py .                 # Layer 3 — thay đổi thường xuyên
```

Nếu chỉ sửa `app.py` mà không đổi `requirements.txt`, Docker skip Layer 1–2 (dùng cache) → build nhanh hơn nhiều. Nếu COPY tất cả cùng lúc → thay đổi bất kỳ file → phải install lại tất cả dependencies.

**4. CMD vs ENTRYPOINT khác nhau thế nào?**

| | `CMD` | `ENTRYPOINT` |
|---|-------|-------------|
| **Mục đích** | Default command khi container start | Fixed executable |
| **Override** | Dễ dàng bằng `docker run <image> <new-cmd>` | Phải dùng `--entrypoint` flag |
| **Kết hợp** | Nếu có cả 2: CMD trở thành arguments cho ENTRYPOINT | ENTRYPOINT là lệnh chính |
| **Use case** | Cho phép user chạy lệnh khác từ cùng image | Lock container vào 1 executable cố định |

Ví dụ:
```dockerfile
# CMD: user có thể override
CMD ["python", "app.py"]
# docker run myimage python test.py  → chạy test.py

# ENTRYPOINT: fixed
ENTRYPOINT ["python"]
CMD ["app.py"]
# docker run myimage test.py  → chạy python test.py
```

---

### Exercise 2.2: Build and run

```bash
# Build image (từ project root)
docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .

# Run container
docker run -p 8000:8000 my-agent:develop
```

Test:
```bash
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
```

**Response:**
```json
{
    "answer": "Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!"
}
```

**Kết quả:** Agent chạy thành công trong container, response giống khi chạy trực tiếp.

**Image size:**
```bash
docker images my-agent:develop
# REPOSITORY      TAG       SIZE
# my-agent        develop   ~1.0 GB
```

**Quan sát:** Image ~1 GB vì dùng `python:3.11` (full) — quá lớn cho production.

---

### Exercise 2.3: Multi-stage build

Đọc `02-docker/production/Dockerfile`:

**Stage 1 (Builder) làm gì?**
- Base: `python:3.11-slim AS builder`
- Cài build tools (`gcc`, `libpq-dev`) cần thiết để compile native dependencies
- `pip install --user` vào `/root/.local` — isolate packages
- Stage này **KHÔNG** được deploy, chỉ dùng để build

**Stage 2 (Runtime) làm gì?**
- Base: `python:3.11-slim AS runtime` — fresh, clean image
- `COPY --from=builder /root/.local` — chỉ copy compiled packages, bỏ lại build tools
- Tạo non-root user `appuser` — security best practice
- Thêm `HEALTHCHECK` instruction — Docker auto-restart nếu health check fail
- Chạy với `uvicorn --workers 2` — multi-worker for concurrency

**Tại sao image nhỏ hơn?**

| Factor | Develop | Production |
|--------|---------|-----------|
| Base image | `python:3.11` (~1 GB) | `python:3.11-slim` (~150 MB) |
| Build tools | Included in final image | Discarded (only in builder stage) |
| Cache | pip cache included | `--no-cache-dir` |
| User | root | non-root `appuser` |
| **Est. size** | **~1.0 GB** | **~200–300 MB** |

Reduction: **~50–70%** smaller.

Multi-stage build loại bỏ mọi thứ **chỉ cần khi build** (gcc, headers, pip cache) khỏi final image → nhỏ hơn, ít attack surface hơn, deploy nhanh hơn.

---

### Exercise 2.4: Docker Compose stack

Đọc `02-docker/production/docker-compose.yml`:

**Architecture Diagram:**

```
                          ┌──────────────────────────┐
                          │        Client            │
                          └────────────┬─────────────┘
                                       │
                                  HTTP :80/:443
                                       │
                          ┌────────────▼─────────────┐
                          │    Nginx (Load Balancer)  │
                          │    nginx:alpine           │
                          │    Reverse proxy          │
                          └────────────┬─────────────┘
                                       │
                          ┌────────────┼────────────┐
                          │            │            │
                    ┌─────▼────┐ ┌─────▼────┐      │
                    │ Agent #1 │ │ Agent #2 │ ... (scalable)
                    │ FastAPI  │ │ FastAPI  │
                    │ :8000    │ │ :8000    │
                    └──┬───┬──┘ └──┬───┬──┘
                       │   │       │   │
              ┌────────▼───▼───────▼───▼────────┐
              │                                  │
    ┌─────────▼──────────┐     ┌─────────────────▼──┐
    │   Redis (Cache)    │     │  Qdrant (Vector DB) │
    │  redis:7-alpine    │     │  qdrant:v1.9.0      │
    │  :6379             │     │  :6333               │
    │  Session + Rate    │     │  RAG embeddings      │
    │  limiting          │     │                      │
    └────────────────────┘     └──────────────────────┘
```

**Services được start:**

| Service | Image | Port | Vai trò |
|---------|-------|------|---------|
| `agent` | Custom build (multi-stage) | 8000 (internal) | FastAPI AI agent, xử lý requests |
| `redis` | `redis:7-alpine` | 6379 (internal) | Session cache, rate limiting storage |
| `qdrant` | `qdrant/qdrant:v1.9.0` | 6333 (internal) | Vector database cho RAG |
| `nginx` | `nginx:alpine` | 80, 443 (exposed) | Reverse proxy, load balancer |

**Cách communicate:**
- Tất cả services cùng network `internal` (bridge driver) → resolve nhau bằng service name (DNS)
- Agent gọi Redis qua `redis://redis:6379/0`
- Agent gọi Qdrant qua `http://qdrant:6333`
- Nginx route traffic đến agent instances qua upstream config
- Chỉ Nginx expose port ra ngoài (80/443) — agents không accessible trực tiếp
- Health checks đảm bảo agent chỉ nhận traffic khi Redis và Qdrant đã ready (`depends_on: condition: service_healthy`)
- Persistent data qua named volumes: `redis_data`, `qdrant_data`

---

## Part 3: Cloud Deployment

### Exercise 3.1: Deploy Railway

**Các bước thực hiện:**

```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login (mở browser)
railway login

# 3. Initialize project
cd 03-cloud-deployment/railway
railway init

# 4. Set environment variables
railway variables set PORT=8000
railway variables set AGENT_API_KEY=minh-la-long-ne-hihi
railway variables set ENVIRONMENT=production

# 5. Deploy
railway up

# 6. Get public URL
railway domain
```

**Kết quả:**
- Public URL: `https://day-12-cloud-and-deployment-production.up.railway.app`
- Deploy tự động detect Python app, dùng Nixpacks builder

**Test public URL:**
```bash
# Health check
curl https://day-12-cloud-and-deployment-production.up.railway.app/health
# Expected: {"status":"ok","uptime_seconds":80.1,"platform":"Railway","timestamp":"2026-04-17T08:41:58.925698+00:00"}

# Agent endpoint
curl https://day-12-cloud-and-deployment-production.up.railway.app/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Am I on the cloud?"}'
# Expected: {"answer": "Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận."}
```

**Cấu hình `railway.toml`:**
- `builder = "NIXPACKS"` — Railway auto-detect Python, install dependencies
- `startCommand` — dùng `uvicorn` với `$PORT` (Railway inject tự động)
- `healthcheckPath = "/health"` — Railway ping endpoint này để check container health
- `restartPolicyType = "ON_FAILURE"` — auto-restart khi crash, tối đa 3 lần

---

### Exercise 3.2: So sánh `render.yaml` vs `railway.toml`

| Aspect | `railway.toml` | `render.yaml` |
|--------|---------------|--------------|
| **Format** | TOML (key-value đơn giản) | YAML (hierarchical, phức tạp hơn) |
| **Builder** | Nixpacks (auto-detect) | Native Python runtime |
| **Start command** | `startCommand` trong `[deploy]` | `startCommand` trong service definition |
| **Health check** | `healthcheckPath = "/health"` | `healthCheckPath: /health` |
| **Env vars** | Set qua CLI (`railway variables set`) hoặc Dashboard | Định nghĩa trong YAML (`envVars` array), có thể dùng `generateValue: true` để auto-generate |
| **Secrets** | Qua Dashboard/CLI (không trong file) | `sync: false` → set thủ công trên Dashboard |
| **Multi-service** | Không hỗ trợ trong 1 file (mỗi service 1 project) | ✅ Blueprint hỗ trợ nhiều services (web + redis) trong 1 file |
| **Redis** | Thêm Redis plugin qua Dashboard | Khai báo `type: redis` trong cùng render.yaml |
| **Auto-deploy** | Tự động khi push (hoặc `railway up`) | `autoDeploy: true` — auto khi push GitHub |
| **Region** | Tự chọn trên Dashboard | `region: singapore` trong YAML |
| **Pricing** | $5 credit free | `plan: free` (750h/month) |
| **Restart policy** | `restartPolicyType = "ON_FAILURE"` | Tự động (platform managed) |

**Nhận xét:**
- **Railway** đơn giản hơn — ít config, nhanh hơn cho prototypes. Chỉ cần `railway up`.
- **Render** mạnh hơn cho multi-service — có thể khai báo web + redis trong cùng 1 file YAML. Infrastructure as Code hoàn chỉnh hơn.
- Cả hai đều hỗ trợ auto-deploy từ GitHub, health checks, và env vars injection.

---

### Exercise 3.3: (Optional) GCP Cloud Run CI/CD

Đọc `cloudbuild.yaml` — CI/CD pipeline gồm **4 steps tuần tự**:

```
Push code → Cloud Build trigger
    │
    ▼
┌─────────────────────────────────────┐
│ Step 1: TEST                        │
│ python:3.11-slim                    │
│ pip install + pytest                │
│ ✅ Tests passed → tiếp              │
│ ❌ Tests failed → pipeline dừng     │
└──────────────┬──────────────────────┘
               │ waitFor: [test]
               ▼
┌─────────────────────────────────────┐
│ Step 2: BUILD Docker image          │
│ gcr.io/cloud-builders/docker        │
│ Tag: $COMMIT_SHA + latest           │
│ --cache-from: tận dụng layer cache  │
└──────────────┬──────────────────────┘
               │ waitFor: [build]
               ▼
┌─────────────────────────────────────┐
│ Step 3: PUSH to Container Registry  │
│ gcr.io/$PROJECT_ID/ai-agent        │
│ Push all tags                       │
└──────────────┬──────────────────────┘
               │ waitFor: [push]
               ▼
┌─────────────────────────────────────┐
│ Step 4: DEPLOY to Cloud Run         │
│ Region: asia-southeast1             │
│ Min instances: 1 (tránh cold start) │
│ Max instances: 10                   │
│ Memory: 512Mi, CPU: 1              │
│ Secrets: từ Secret Manager          │
└─────────────────────────────────────┘
```

Đọc `service.yaml` — Cloud Run Service Definition (Knative format):

| Config | Giá trị | Ý nghĩa |
|--------|---------|---------|
| `minScale` | 1 | Luôn giữ 1 instance → tránh cold start |
| `maxScale` | 10 | Tối đa 10 instances khi traffic cao |
| `containerConcurrency` | 80 | Mỗi instance xử lý tối đa 80 requests đồng thời |
| `timeoutSeconds` | 60 | Request timeout 60s |
| `resources.limits` | 1 CPU, 512Mi RAM | Resource limits per instance |
| `livenessProbe` | GET `/health` mỗi 30s | Nếu fail → restart container |
| `startupProbe` | GET `/ready` mỗi 3s | Chờ app ready trước khi nhận traffic |
| Secrets | `valueFrom.secretKeyRef` | Đọc từ GCP Secret Manager, **không hardcode** |

**So sánh độ phức tạp:**

| | Railway | Render | Cloud Run |
|---|---------|--------|-----------|
| **Setup** | `railway up` (1 lệnh) | Connect GitHub + Blueprint | `gcloud builds submit` + service.yaml |
| **CI/CD** | Auto (push = deploy) | Auto (push = deploy) | Full pipeline: test → build → push → deploy |
| **Scaling** | Manual (Dashboard) | Manual (Dashboard) | Auto-scaling 1–10 instances |
| **Secrets** | Dashboard/CLI | Dashboard + render.yaml | GCP Secret Manager (enterprise-grade) |
| **Best for** | Prototypes | Side projects | Production at scale |

---

## Part 4: API Security

### Exercise 4.1: API Key authentication

Đọc `04-api-gateway/develop/app.py`:

**API key được check ở đâu?**

Trong function `verify_api_key()` — được inject vào endpoint `/ask` qua FastAPI `Depends()`:

```python
API_KEY = os.getenv("AGENT_API_KEY", "demo-key-change-in-production")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@app.post("/ask")
async def ask_agent(question: str, _key: str = Depends(verify_api_key)):
    ...
```

**Điều gì xảy ra nếu sai key?**
- Không gửi key → `401 Unauthorized` ("Missing API key")
- Sai key → `403 Forbidden` ("Invalid API key")
- Đúng key → `200 OK` + response bình thường

**Test results:**

```bash
# ❌ Không có key → 401
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
# Response: {"detail": "Missing API key. Include header: X-API-Key: <your-key>"}

# ✅ Có key → 200
curl http://localhost:8000/ask -X POST \
  -H "X-API-Key: demo-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
# Response: {"question": "Hello", "answer": "Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic."}
```

**Làm sao rotate key?**

Thay đổi env var `AGENT_API_KEY` và restart service. Không cần sửa code vì key đọc từ `os.getenv()`.

```bash
# Railway
railway variables set AGENT_API_KEY=new-rotated-key-456
railway up

# Docker
docker run -e AGENT_API_KEY=new-rotated-key-456 my-agent
```

---

### Exercise 4.2: JWT authentication

Đọc `04-api-gateway/production/auth.py` — JWT flow:

```
┌──────────┐     POST /auth/token          ┌──────────┐
│  Client  │ ──── username + password ────→ │  Server  │
│          │ ←─── JWT token ──────────────  │          │
└──────────┘                                └──────────┘
     │
     │  POST /ask
     │  Authorization: Bearer <token>
     ▼
┌──────────┐                                ┌──────────┐
│  Client  │ ──── JWT in header ──────────→ │  Server  │
│          │                                │ verify() │
│          │ ←─── response ───────────────  │          │
└──────────┘                                └──────────┘
```

**JWT Token chứa gì?**

```json
{
  "sub": "student",           // subject — username
  "role": "user",             // role — user hoặc admin
  "iat": 1713340000,          // issued at — thời điểm tạo
  "exp": 1713343600           // expiry — hết hạn sau 60 phút
}
```

**Token được sign bằng `HS256` với `SECRET_KEY` từ env var `JWT_SECRET`.**

**Test:**

```bash
# 1. Lấy token
curl http://localhost:8000/auth/token -X POST \
  -H "Content-Type: application/json" \
  -d '{"username": "student", "password": "demo123"}'
# Response: {"access_token": "eyJhbGciOiJI...", "token_type": "bearer"}

# 2. Dùng token gọi API
TOKEN="eyJhbGciOiJI..."
curl http://localhost:8000/ask -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain JWT"}'
# Response: 200 OK

# 3. Token expired / invalid → 401
curl http://localhost:8000/ask -X POST \
  -H "Authorization: Bearer invalid-token" \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'
# Response: {"detail": "Invalid token."}
```

**So sánh API Key vs JWT:**

| | API Key | JWT |
|---|---------|-----|
| **Stateless** | Server phải biết key | ✅ Server chỉ cần verify signature |
| **Expiry** | Không tự hết hạn | ✅ Có `exp` claim |
| **User info** | Chỉ là string | ✅ Chứa username, role, metadata |
| **Rotate** | Đổi key = tất cả client bị ảnh hưởng | Đổi secret = chỉ token mới bị ảnh hưởng |
| **Use case** | B2B, internal API | User-facing, multi-role |

---

### Exercise 4.3: Rate limiting

Đọc `04-api-gateway/production/rate_limiter.py`:

**Algorithm: Sliding Window Counter**

Cách hoạt động:
1. Mỗi user có 1 `deque` (double-ended queue) chứa timestamps của requests
2. Khi nhận request mới, loại bỏ timestamps cũ hơn `window_seconds` (60s)
3. Đếm số timestamps còn lại trong window
4. Nếu ≥ `max_requests` → raise `429 Too Many Requests`
5. Nếu chưa đạt → append timestamp mới, cho phép request

```
Timeline (window = 60s, limit = 10):

t=0s   t=10s  t=20s  ... t=55s  t=60s  t=61s
 R1     R2     R3    ... R10   [R1 expired]  R11 OK (R1 ra khỏi window)
                          ↑
                     Nếu thêm R11 ở t=59s → 429!
```

**Limit:** 10 requests/minute cho user, 100 requests/minute cho admin.

```python
rate_limiter_user = RateLimiter(max_requests=10, window_seconds=60)
rate_limiter_admin = RateLimiter(max_requests=100, window_seconds=60)
```

**Response khi hit limit:**

```json
{
  "detail": {
    "error": "Rate limit exceeded",
    "limit": 10,
    "window_seconds": 60,
    "retry_after_seconds": 45
  }
}
```

Headers trả về: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `Retry-After`.

**Bypass limit cho admin:** Dùng `rate_limiter_admin` (100 req/min) thay vì `rate_limiter_user` (10 req/min). Server check role từ JWT token để chọn limiter phù hợp.

---

### Exercise 4.4: Cost guard implementation

Đọc `04-api-gateway/production/cost_guard.py`:

**Approach:** Track token usage per user per day, tính cost dựa trên pricing model.

**Cấu trúc `CostGuard`:**

```python
class CostGuard:
    daily_budget_usd = 1.0        # $1/ngày per user
    global_daily_budget_usd = 10.0 # $10/ngày tổng tất cả users
    warn_at_pct = 0.8              # Warning khi dùng 80% budget
```

**Logic `check_budget()` — chạy TRƯỚC khi gọi LLM:**

1. Lấy `UsageRecord` của user cho ngày hôm nay (reset mỗi ngày mới)
2. Check **global budget** trước: nếu tổng chi phí ≥ $10 → `503 Service Unavailable`
3. Check **per-user budget**: nếu user đã dùng ≥ $1 → `402 Payment Required`
4. Warning nếu đạt 80% budget → log warning

**Logic `record_usage()` — chạy SAU khi gọi LLM:**

1. Cộng `input_tokens` + `output_tokens` vào record
2. Tính cost: `(input_tokens / 1000 × $0.00015) + (output_tokens / 1000 × $0.0006)`
3. Cộng vào `_global_cost`
4. Log usage info

**Flow trong endpoint `/ask`:**

```
Request → Auth → Rate Limit → Cost Guard check → Call LLM → Cost Guard record → Response
                                    ↓                              ↓
                              402 nếu vượt              Ghi nhận tokens đã dùng
```

**Lưu ý: Version này dùng in-memory** (dict). Trong production cần thay bằng Redis để:
- Persist data qua restarts
- Share state giữa multiple instances (stateless design)
- Atomic operations (tránh race conditions)

---

## Part 5: Scaling & Reliability

### Exercise 5.1: Health checks

Đọc `05-scaling-reliability/develop/app.py`:

**Implementation:**

```python
@app.get("/health")
def health():
    """LIVENESS PROBE — Agent có còn sống không?"""
    uptime = round(time.time() - START_TIME, 1)
    # Check memory, dependencies
    return {
        "status": "ok",            # hoặc "degraded"
        "uptime_seconds": uptime,
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": { ... },         # sub-checks (memory, etc.)
    }

@app.get("/ready")
def ready():
    """READINESS PROBE — Agent sẵn sàng nhận request chưa?"""
    if not _is_ready:
        raise HTTPException(503, "Agent not ready")
    return {"ready": True, "in_flight_requests": _in_flight_requests}
```

**Sự khác biệt giữa 2 endpoints:**

| | `/health` (Liveness) | `/ready` (Readiness) |
|---|---------------------|---------------------|
| **Hỏi gì?** | "Container còn sống không?" | "Sẵn sàng nhận traffic chưa?" |
| **Ai gọi?** | Platform (K8s, Railway) | Load balancer |
| **Fail → ?** | **Restart** container | **Stop routing** traffic vào instance |
| **Khi nào fail?** | Process crash, deadlock | Đang startup, dependencies chưa ready |
| **Return** | 200 luôn (nếu process sống) | 503 khi chưa ready |

**Test:**
```bash
curl http://localhost:8000/health
# {"status": "ok", "uptime_seconds": 12.5, ...}

curl http://localhost:8000/ready
# {"ready": true, "in_flight_requests": 0}
# Hoặc khi đang startup: 503 "Agent not ready"
```

---

### Exercise 5.2: Graceful shutdown

**Implementation:**

```python
_in_flight_requests = 0  # đếm request đang xử lý

@app.middleware("http")
async def track_requests(request, call_next):
    global _in_flight_requests
    _in_flight_requests += 1
    try:
        response = await call_next(request)
        return response
    finally:
        _in_flight_requests -= 1

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    _is_ready = True
    yield
    # Shutdown
    _is_ready = False                    # 1. Stop accepting new requests
    while _in_flight_requests > 0:       # 2. Wait for in-flight requests
        time.sleep(1)                    #    (max 30 seconds)
    # 3. Close connections               → done by lifespan exit
    # 4. Exit                            → done by uvicorn

signal.signal(signal.SIGTERM, handle_sigterm)  # Catch SIGTERM from platform
```

**Shutdown flow:**

```
Platform gửi SIGTERM
        │
        ▼
1. _is_ready = False         → /ready trả 503 → LB stop routing traffic
2. Chờ _in_flight_requests   → Requests hiện tại hoàn thành
   (max 30 seconds)
3. Close connections          → Redis, DB, etc.
4. Process exit               → Container stopped cleanly
```

**Test:**
```bash
python app.py &
PID=$!

# Gửi request (giả lập đang xử lý)
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Long task"}' &

# Gửi SIGTERM
kill -TERM $PID

# Quan sát logs:
# "🔄 Graceful shutdown initiated..."
# "Waiting for 1 in-flight requests..."
# "✅ Shutdown complete"
```

**Kết quả:** Request đang xử lý hoàn thành trước khi process tắt. Không có request bị cắt giữa chừng.

---

### Exercise 5.3: Stateless design

Đọc `05-scaling-reliability/production/app.py`:

**Anti-pattern (Stateful):**
```python
# ❌ State trong memory — mất khi restart, không share giữa instances
conversations = {}

@app.post("/ask")
def ask(user_id: str, question: str):
    history = conversations.get(user_id, [])  # Instance 2 không có data này!
```

**Correct (Stateless với Redis):**
```python
# ✅ State trong Redis — persist qua restarts, share giữa instances
def save_session(session_id: str, data: dict, ttl_seconds: int = 3600):
    _redis.setex(f"session:{session_id}", ttl_seconds, json.dumps(data))

def load_session(session_id: str) -> dict:
    data = _redis.get(f"session:{session_id}")
    return json.loads(data) if data else {}

def append_to_history(session_id: str, role: str, content: str):
    session = load_session(session_id)
    history = session.get("history", [])
    history.append({"role": role, "content": content, "timestamp": "..."})
    if len(history) > 20:       # Giữ tối đa 20 messages
        history = history[-20:]
    session["history"] = history
    save_session(session_id, session)
```

**Tại sao stateless quan trọng khi scale?**

```
Stateful (❌):
  User: "Tôi là Alice"    → Instance 1 (lưu trong memory)
  User: "Tên tôi là gì?"  → Instance 2 (không biết! → bug)

Stateless (✅):
  User: "Tôi là Alice"    → Instance 1 → lưu vào Redis
  User: "Tên tôi là gì?"  → Instance 2 → đọc từ Redis → "Alice"
```

Mỗi instance có thể xử lý bất kỳ request nào vì tất cả state nằm trong Redis — shared, persistent, atomic.

---

### Exercise 5.4: Load balancing

Chạy stack với Nginx load balancer:

```bash
docker compose up --scale agent=3
```

**Stack:**

```
Client → Nginx (:8080) ─── round-robin ──→ Agent 1 (:8000)
                                        ──→ Agent 2 (:8000)
                                        ──→ Agent 3 (:8000)
                                              │
                                              ▼
                                          Redis (:6379)
```

**Quan sát:**
- 3 agent instances được start, mỗi instance có `INSTANCE_ID` riêng
- Nginx phân tán requests theo round-robin
- Response chứa `"served_by": "instance-abc123"` → thấy rõ instance nào xử lý
- Nếu 1 instance die → Nginx tự chuyển traffic sang instances còn sống
- Resource limits: mỗi instance max 0.5 CPU, 256 MB RAM

**Test:**
```bash
# Gọi 10 requests
for i in {1..10}; do
  curl -s http://localhost:8080/chat -X POST \
    -H "Content-Type: application/json" \
    -d '{"question": "Request '$i'"}' | python -c "import sys,json; print(json.load(sys.stdin)['served_by'])"
done

# Output (mỗi request đến instance khác):
# instance-a1b2c3
# instance-d4e5f6
# instance-g7h8i9
# instance-a1b2c3  ← round-robin quay lại
# ...
```

---

### Exercise 5.5: Test stateless

Chạy `test_stateless.py`:

```bash
python test_stateless.py
```

**Script thực hiện:**
1. Tạo session mới bằng request đầu tiên
2. Gửi 5 requests liên tiếp với cùng `session_id`
3. Mỗi request có thể đến instance khác nhau (do round-robin)
4. Sau 5 requests, kiểm tra conversation history

**Expected output:**

```
============================================================
Stateless Scaling Demo
============================================================

Session ID: 5a3e7c2d-a1b2-4c3d-8e9f-123456789abc

Request 1: [instance-a1b2c3]
  Q: What is Docker?
  A: Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!

Request 2: [instance-d4e5f6]    ← instance khác!
  Q: Why do we need containers?
  A: Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic.

Request 3: [instance-g7h8i9]
  Q: What is Kubernetes?
  A: Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé.

Request 4: [instance-a1b2c3]    ← round-robin quay lại
  Q: How does load balancing work?
  A: Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.

Request 5: [instance-d4e5f6]
  Q: What is Redis used for?
  A: Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic.

------------------------------------------------------------
Total requests: 5
Instances used: {'instance-a1b2c3', 'instance-d4e5f6', 'instance-g7h8i9'}
✅ All requests served despite different instances!

--- Conversation History ---
Total messages: 10
  [user]: What is Docker?
  [assistant]: Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!
  [user]: Why do we need containers?
  [assistant]: Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic.
  [user]: What is Kubernetes?
  [assistant]: Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé.
  [user]: How does load balancing work?
  [assistant]: Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.
  [user]: What is Redis used for?
  [assistant]: Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic.

✅ Session history preserved across all instances via Redis!
```

**Kết luận:** Dù requests được xử lý bởi 3 instances khác nhau, conversation history vẫn đầy đủ vì tất cả đều đọc/ghi từ cùng một Redis instance. Đây chính là sức mạnh của **stateless design**.
