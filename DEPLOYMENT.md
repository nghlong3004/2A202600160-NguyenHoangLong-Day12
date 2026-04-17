# Deployment Information

> **Student:** Nguyễn Hoàng Long  
> **MSSV:** 2A202600160  
> **Date:** 2026-04-17  
> **Platform:** Railway

---

## Public URL

🚀 **https://day-12-cloud-and-deployment-production.up.railway.app**

---

## Test Commands

### 1. Health Check (Liveness Probe)

```bash
curl https://day-12-cloud-and-deployment-production.up.railway.app/health
```

**Response:**
```json
{"status":"ok","uptime_seconds":81.9,"platform":"Railway","timestamp":"2026-04-17T10:12:12.981549+00:00"}
```

### 2. Root Endpoint

```bash
curl https://day-12-cloud-and-deployment-production.up.railway.app/
```

**Response:**
```json
{"message":"AI Agent running on Railway!","docs":"/docs","health":"/health"}
```

### 3. Ask Endpoint (with API Key)

```bash
curl https://day-12-cloud-and-deployment-production.up.railway.app/ask \
  -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{"question": "What is Docker?"}'
```

### 4. Ask Endpoint (without API Key — expects 401/403)

```bash
curl https://day-12-cloud-and-deployment-production.up.railway.app/ask \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
```

---

## Platform: Railway

- **Builder:** Nixpacks (auto-detect Python)
- **Region:** Auto-selected
- **Health Check:** `/health`
- **Auto Deploy:** GitHub connected — push to main triggers deploy

### Environment Variables Set

| Variable | Value | Source |
|----------|-------|--------|
| `ENVIRONMENT` | `production` | Railway Dashboard |
| `AGENT_API_KEY` | `****` (secret) | Railway Dashboard |
| `PORT` | Auto-injected | Railway Platform |

---

## CI/CD Pipeline

GitHub Actions runs on every push to `main`:

1. **Production Readiness Check** — validates 20 criteria
2. **Docker Build + Test** — builds image, tests health/auth/rate-limit

See: https://github.com/nghlong3004/2A202600160-NguyenHoangLong-Day12/actions
