# Deployment Information

> **Student:** Nguyễn Hoàng Long  
> **MSSV:** 2A202600160  
> **Date:** 2026-04-17  
> **Platform:** Railway

---

## Public URL

🚀 **https://day12-cloud-and-deployment-production.up.railway.app**

---

## Test Commands

### 1. Health Check (Liveness Probe)

```bash
curl https://day12-cloud-and-deployment-production.up.railway.app/health
```

**Expected Response:**
```json
{
  "status": "ok",
  "uptime_seconds": 39.3,
  "platform": "Railway",
  "timestamp": "2026-04-17T08:41:18.132758+00:00"
}
```

### 2. Root Endpoint

```bash
curl https://day12-cloud-and-deployment-production.up.railway.app/
```

**Expected Response:**
```json
{
  "message": "AI Agent running on Railway!",
  "docs": "/docs",
  "health": "/health"
}
```

### 3. Ask Endpoint (with API Key)

```bash
curl https://day12-cloud-and-deployment-production.up.railway.app/ask \
  -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{"question": "What is Docker?"}'
```

### 4. Ask Endpoint (without API Key — expects 401)

```bash
curl https://day12-cloud-and-deployment-production.up.railway.app/ask \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
```

**Expected Response:**
```json
{"detail": "Invalid or missing API key"}
```

---

## Deployment Configuration

### Platform: Railway

- **Project:** day12-cloud-and-deployment
- **Builder:** Nixpacks (auto-detect Python)
- **Region:** Auto-selected
- **Health Check:** `/health`

### Environment Variables

| Variable | Value | Source |
|----------|-------|--------|
| `ENVIRONMENT` | `production` | Railway Dashboard |
| `AGENT_API_KEY` | `****` (secret) | Railway Dashboard |
| `PORT` | Auto-injected | Railway Platform |

### Railway Project URL

https://railway.com/project/c2fb27fa-99c0-4c63-aaab-f466064136e9

---

## Deployment Steps

```bash
# 1. Login
railway login

# 2. Init project
railway init
# → Project name: day12-cloud-and-deployment

# 3. Deploy
railway up

# 4. Get domain
railway domain
# → https://day12-cloud-and-deployment-production.up.railway.app

# 5. Set env vars (via Dashboard)
# Railway Dashboard → Variables → AGENT_API_KEY, ENVIRONMENT
```
