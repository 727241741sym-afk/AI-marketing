# Atlas Research

繁體中文 AI 股票研究報告 SaaS，將 `tauricresearch/tradingagents` 包成月費制 Web App。第一版只提供研究報告、風險辯論與綜合摘要，不提供自動下單、券商連接或投資建議。

## 架構

- `apps/web`: Next.js App Router 前端，使用 Supabase SSR Auth，所有產品 UI 文案使用繁體中文。
- `apps/api`: FastAPI 後端，驗證 Supabase bearer token，封裝研究任務、配額、Stripe Billing webhook、RQ queue/worker 與 TradingAgents adapter。
- `infra/postgres`: Atlas 專用 `atlas_` Postgres schema，涵蓋 profiles、subscriptions、research_runs、reports、watchlist_items、usage_events。
- `docker-compose.yml`: Postgres、Redis、API、Web 的本地部署拓撲。

## 本地開發

1. 複製環境變數：

```bash
cp .env.example .env
```

2. 在 `.env` 填入 Supabase URL 與 publishable key，並讓前後端共用同一組設定：

```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxx
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxx
```

3. 安裝前端依賴：

```bash
npm install
```

4. 安裝後端依賴：

```bash
cd apps/api
python -m venv .venv
.venv/Scripts/activate
pip install -e ".[dev]"
```

5. 啟動服務：

```bash
docker compose up postgres redis api worker
npm run dev:web
```

本機 Docker Postgres 會先載入 `infra/postgres/local/000_auth_stub.sql`，再載入 `infra/postgres/001_init.sql` 建立 `atlas_` 表與 RLS policies。Hosted Supabase 只套用 `infra/postgres/001_init.sql`，不要覆寫 Supabase managed `auth` schema。Docker API/worker 預設安裝已 pin commit 的上游 TradingAgents；若只想快速測 UI，可設定 `DEMO_MODE=true` 與 `QUEUE_BACKEND=inline`。

```bash
pip install -e ".[dev,tradingagents]"
```

## 測試

```bash
npm run test:web
cd apps/api && python -m pytest tests -q
```

目前測試覆蓋 Supabase token 拒絕、用戶隔離、配額限制、Stripe webhook 邊界、Postgres/RLS SQL、TradingAgents 結果轉換與前端用量格式化。

## 商業化邊界

- Stripe Billing 負責月費訂閱、付款方式、取消訂閱與升降級。
- 平台 API keys 支付 LLM 與市場資料成本，因此必須啟用月度配額、任務超時與用量事件。
- 介面與報告固定顯示「僅供研究用途，不構成投資建議或交易建議。」
- 上線前需由律師確認金融研究、資料授權、免責聲明與當地法規要求。

## TradingAgents 接入

`apps/api/app/services/tradingagents_client.py` 會在 `DEMO_MODE=false` 時載入：

```python
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph
```

並呼叫：

```python
state, decision = graph.propagate(ticker, report_date)
```

Staging 預設使用 MiniMax M3：

```bash
TRADINGAGENTS_LLM_PROVIDER=minimax
TRADINGAGENTS_DEEP_THINK_LLM=MiniMax-M3
TRADINGAGENTS_QUICK_THINK_LLM=MiniMax-M3
TRADINGAGENTS_LLM_BACKEND_URL=https://api.minimax.io/v1
TRADINGAGENTS_OUTPUT_LANGUAGE=Traditional Chinese
MINIMAX_API_KEY=...
```

回傳結果會轉成繁體中文產品需要的四個區塊：多頭觀點、空頭觀點、風險辯論、最終綜合。

## Staging

Vercel 只部署 `apps/web` preview；FastAPI API 與 RQ worker 由 Railway 容器承載。詳細步驟見 `docs/staging.md`。
