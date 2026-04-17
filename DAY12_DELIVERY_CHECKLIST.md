#  Delivery Checklist — Day 12 Lab Submission

> **Student Name:** Nguyễn Hoàng Long  
> **Student ID:** 2A202600160  
> **Date:** 2026-04-17

---

## 🔍 Part 1 Analysis — Anti-patterns found in `01-localhost-vs-production/develop/app.py`

> [!WARNING]
> Tổng cộng **9 vấn đề** được phát hiện trong file `app.py` (develop version).

| # | Vấn đề | Dòng | Mô tả | Mức độ |
|---|--------|------|-------|--------|
| 1 | **API key hardcode** | 17–18 | `OPENAI_API_KEY` và `DATABASE_URL` (kèm password) được ghi thẳng trong source code. Push lên GitHub → credentials bị lộ ngay lập tức. | 🔴 Critical |
| 2 | **Không có config management** | 21–22 | `DEBUG = True` và `MAX_TOKENS = 500` là các giá trị cố định, không đọc từ environment variables → không thể thay đổi khi deploy mà không sửa code. | 🟠 High |
| 3 | **Print thay vì structured logging** | 33, 38 | Dùng `print()` thay cho `logging` module hoặc JSON structured logging → không có log level, không filter được, không integrate với log aggregation (ELK, CloudWatch). | 🟠 High |
| 4 | **Log ra secret** | 34 | `print(f"[DEBUG] Using key: {OPENAI_API_KEY}")` — in API key ra stdout. Nếu log được thu thập bởi monitoring system, secret bị lộ ở nhiều nơi. | 🔴 Critical |
| 5 | **Không có health check endpoint** | 42–43 | Không có `/health` → platform (Railway/Render/K8s) không biết khi nào container crash để tự động restart. | 🟠 High |
| 6 | **Host bind `localhost`** | 51 | `host="localhost"` chỉ listen trên loopback interface → từ bên ngoài container (hoặc từ máy khác) không thể truy cập. Production cần `0.0.0.0`. | 🔴 Critical |
| 7 | **Port cố định** | 52 | `port=8000` hardcode, không đọc từ `os.environ.get("PORT")`. Trên Railway/Render, PORT được inject qua env var, không phải lúc nào cũng là 8000. | 🟠 High |
| 8 | **Debug reload trong production** | 53 | `reload=True` bật hot-reload — tốn tài nguyên, không ổn định, có thể gây restart bất ngờ trong production. | 🟡 Medium |
| 9 | **Không có graceful shutdown** | — | Không có signal handler cho `SIGTERM`/`SIGINT`. Khi container bị stop, requests đang xử lý sẽ bị cắt đột ngột → mất data, bad UX. | 🟠 High |

### Các vấn đề bổ sung (ngoài gợi ý của lab)

| # | Vấn đề | Mô tả |
|---|--------|-------|
| A | **Không có authentication** | Endpoint `/ask` không yêu cầu API key → ai cũng gọi được → hết tiền LLM. |
| B | **Không có rate limiting** | Không giới hạn số request/phút → dễ bị abuse hoặc DDoS. |
| C | **Không có error handling** | Nếu `ask()` (mock LLM) throw exception, server trả 500 Internal Server Error không có context. |

---

##  Submission Requirements

Submit a **GitHub repository** containing:

### 1. Mission Answers (40 points)

Create a file `MISSION_ANSWERS.md` with your answers to all exercises:

```markdown
# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. [Your answer]
2. [Your answer]
...

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config  | ...     | ...        | ...            |
...

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: [Your answer]
2. Working directory: [Your answer]
...

### Exercise 2.3: Image size comparison
- Develop: [X] MB
- Production: [Y] MB
- Difference: [Z]%

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- URL: https://your-app.railway.app
- Screenshot: [Link to screenshot in repo]

## Part 4: API Security

### Exercise 4.1-4.3: Test results
[Paste your test outputs]

### Exercise 4.4: Cost guard implementation
[Explain your approach]

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
[Your explanations and test results]
```

---

### 2. Full Source Code - Lab 06 Complete (60 points)

Your final production-ready agent with all files:

```
your-repo/
├── app/
│   ├── main.py              # Main application
│   ├── config.py            # Configuration
│   ├── auth.py              # Authentication
│   ├── rate_limiter.py      # Rate limiting
│   └── cost_guard.py        # Cost protection
├── utils/
│   └── mock_llm.py          # Mock LLM (provided)
├── Dockerfile               # Multi-stage build
├── docker-compose.yml       # Full stack
├── requirements.txt         # Dependencies
├── .env.example             # Environment template
├── .dockerignore            # Docker ignore
├── railway.toml             # Railway config (or render.yaml)
└── README.md                # Setup instructions
```

**Requirements:**
-  All code runs without errors
-  Multi-stage Dockerfile (image < 500 MB)
-  API key authentication
-  Rate limiting (10 req/min)
-  Cost guard ($10/month)
-  Health + readiness checks
-  Graceful shutdown
-  Stateless design (Redis)
-  No hardcoded secrets

---

### 3. Service Domain Link

Create a file `DEPLOYMENT.md` with your deployed service information:

```markdown
# Deployment Information

## Public URL
https://your-agent.railway.app

## Platform
Railway / Render / Cloud Run

## Test Commands

### Health Check
```bash
curl https://your-agent.railway.app/health
# Expected: {"status": "ok"}
```

### API Test (with authentication)
```bash
curl -X POST https://your-agent.railway.app/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Hello"}'
```

## Environment Variables Set
- PORT
- REDIS_URL
- AGENT_API_KEY
- LOG_LEVEL

## Screenshots
- [Deployment dashboard](screenshots/dashboard.png)
- [Service running](screenshots/running.png)
- [Test results](screenshots/test.png)
```

##  Pre-Submission Checklist

- [ ] Repository is public (or instructor has access)
- [ ] `MISSION_ANSWERS.md` completed with all exercises
- [ ] `DEPLOYMENT.md` has working public URL
- [ ] All source code in `app/` directory
- [ ] `README.md` has clear setup instructions
- [ ] No `.env` file committed (only `.env.example`)
- [ ] No hardcoded secrets in code
- [ ] Public URL is accessible and working
- [ ] Screenshots included in `screenshots/` folder
- [ ] Repository has clear commit history

---

##  Self-Test

Before submitting, verify your deployment:

```bash
# 1. Health check
curl https://your-app.railway.app/health

# 2. Authentication required
curl https://your-app.railway.app/ask
# Should return 401

# 3. With API key works
curl -H "X-API-Key: YOUR_KEY" https://your-app.railway.app/ask \
  -X POST -d '{"user_id":"test","question":"Hello"}'
# Should return 200

# 4. Rate limiting
for i in {1..15}; do 
  curl -H "X-API-Key: YOUR_KEY" https://your-app.railway.app/ask \
    -X POST -d '{"user_id":"test","question":"test"}'; 
done
# Should eventually return 429
```

---

##  Submission

**Submit your GitHub repository URL:**

```
https://github.com/your-username/day12-agent-deployment
```

**Deadline:** 17/4/2026

---

##  Quick Tips

1.  Test your public URL from a different device
2.  Make sure repository is public or instructor has access
3.  Include screenshots of working deployment
4.  Write clear commit messages
5.  Test all commands in DEPLOYMENT.md work
6.  No secrets in code or commit history

---

##  Need Help?

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Review [CODE_LAB.md](CODE_LAB.md)
- Ask in office hours
- Post in discussion forum

---

**Good luck! **
