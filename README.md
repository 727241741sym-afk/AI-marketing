# Atlas Research

繁體中文 AI 股票研究報告 SaaS，將 `tauricresearch/tradingagents` 包成月費制 Web App。第一版只提供研究報告、風險辯論與綜合摘要，不提供自動下單、券商連接或投資建議。

## 架構

- `apps/web`: Next.js App Router 前端，所有產品 UI 文案使用繁體中文。
- `apps/api`: FastAPI 後端，封裝研究任務、配額、Stripe Billing webhook 與 TradingAgents adapter。
- `infra/postgres`: 商業版資料表 schema，涵蓋 users、subscriptions、research_runs、reports、watchlist_items、usage_events。
- `docker-compose.yml`: Postgres、Redis、API、Web 的本地部署拓撲。

## 本地開發

1. 複製環境變數：

```bash
cp .env.example .env
```

2. 安裝前端依賴：

```bash
npm install
```

3. 安裝後端依賴：

```bash
cd apps/api
python -m venv .venv
.venv/Scripts/activate
pip install -e ".[dev]"
```

4. 啟動服務：

```bash
docker compose up postgres redis
npm run dev:web
cd apps/api && uvicorn app.main:app --reload --port 8000
```

`DEMO_MODE=true` 時後端會使用內建示範研究結果，不需要真實 OpenAI/Finnhub/Reddit/TradingAgents keys。Production 接入上游引擎時改用：

```bash
pip install -e ".[dev,tradingagents]"
```

## 測試

```bash
npm run test:web
cd apps/api && python -m pytest tests -q
```

目前測試覆蓋配額限制、訂閱狀態、TradingAgents 結果轉換與前端用量格式化。

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

回傳結果會轉成繁體中文產品需要的四個區塊：多頭觀點、空頭觀點、風險辯論、最終綜合。
