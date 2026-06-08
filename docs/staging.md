# Staging Deployment

本文件描述 Atlas Research staging 拓撲：Vercel 只部署 `apps/web`，Railway 部署 FastAPI API 與 RQ worker，Supabase `Atlas Research` project 提供 Auth/Postgres。

## Supabase

- Project ref: `vgjwrvjhlnevarvimmce`
- API URL: `https://vgjwrvjhlnevarvimmce.supabase.co`
- Auth redirect URL 加入 Vercel preview callback，例如：

```text
https://<vercel-preview-url>/auth/callback
```

## Railway

建立同一 repo 的兩個 Railway services，兩者 Root Directory 都設為 `/apps/api`，Config File 設為 `/apps/api/railway.json`。

API service:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Worker service:

```text
python -m app.worker
```

API service 可設定 HTTP healthcheck path `/healthz`；worker service 不設定 HTTP healthcheck。

Railway staging env:

```text
APP_ENV=staging
DEMO_MODE=false
REPOSITORY_BACKEND=postgres
QUEUE_BACKEND=rq
RQ_QUEUE_NAME=atlas-research
FRONTEND_URL=https://<vercel-preview-url>
CORS_ORIGINS=https://<vercel-preview-url>
CORS_ORIGIN_REGEX=https://.*\.vercel\.app
DATABASE_URL=<Supabase pooled Postgres URL>
REDIS_URL=<Railway Redis URL>
SUPABASE_URL=https://vgjwrvjhlnevarvimmce.supabase.co
SUPABASE_PUBLISHABLE_KEY=<Supabase publishable key>
MINIMAX_API_KEY=<secret>
TRADINGAGENTS_LLM_PROVIDER=minimax
TRADINGAGENTS_DEEP_THINK_LLM=MiniMax-M3
TRADINGAGENTS_QUICK_THINK_LLM=MiniMax-M3
TRADINGAGENTS_LLM_BACKEND_URL=https://api.minimax.io/v1
TRADINGAGENTS_OUTPUT_LANGUAGE=Traditional Chinese
TRADINGAGENTS_CHECKPOINT_ENABLED=true
TRADINGAGENTS_MAX_DEBATE_ROUNDS=2
TRADINGAGENTS_MAX_RISK_ROUNDS=2
TRADINGAGENTS_RESULTS_DIR=/data/tradingagents
TRADINGAGENTS_CACHE_DIR=/data/tradingagents-cache
RESEARCH_TIMEOUT_SECONDS=900
FINNHUB_API_KEY=<secret>
STRIPE_SECRET_KEY=<test secret>
STRIPE_WEBHOOK_SECRET=<test secret>
STRIPE_PRICE_PRO_MONTHLY=<test price id>
```

Staging 預設不啟用 `social` 分析代理，因此不需要 Reddit credentials。

如果 MiniMax 帳號是中國區，改用 `TRADINGAGENTS_LLM_PROVIDER=minimax-cn`、中國區 endpoint 與 `MINIMAX_CN_API_KEY`。

## Vercel Preview

Vercel project 指向 `apps/web`。使用 CLI preview：

```bash
cd apps/web
vercel deploy
```

Preview env:

```text
NEXT_PUBLIC_APP_ENV=staging
NEXT_PUBLIC_API_BASE_URL=https://<railway-api-url>
NEXT_PUBLIC_SUPABASE_URL=https://vgjwrvjhlnevarvimmce.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=<Supabase publishable key>
```

不要提交 `.vercel/`、`.env.local`、Railway token、Vercel token、MiniMax key、Supabase database password 或 Stripe secret。

## Smoke Test

1. 開啟 Vercel preview 並登入。
2. 建立 `AAPL` 標準或深度研究任務。
3. Railway API log 應顯示 task queued，worker log 應顯示 job running/completed。
4. 前端輪詢後應看到繁體中文報告，來源包含 `TradingAgents` 與 `MiniMax M3`。
5. 重新整理報告頁，確認資料仍從 Supabase/Postgres 讀回。
