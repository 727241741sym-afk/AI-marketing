# Atlas Research Architecture

## Request Flow

1. 使用者在 Next.js 儀表板送出 ticker、報告日期、分析深度與分析代理。
2. FastAPI `POST /api/research-runs` 驗證訂閱狀態與剩餘配額。
3. 後端建立 `research_runs`，扣一次月度報告額度，並交給背景 worker。
4. Worker 透過 TradingAgents adapter 取得 `state` 與 `decision`。
5. `report_mapper` 將結果轉成繁體中文報告區塊並寫入 `reports`。
6. 前端輪詢 `GET /api/research-runs/:id`，完成後導向 `GET /api/reports/:id`。

## Production Notes

- Demo 模式使用 in-memory repository，方便沒有 API keys 時展示端到端 UI。
- Production 應將 repository 換成 Postgres 實作，資料表定義在 `infra/postgres/001_init.sql`。
- Redis/RQ 可替代 FastAPI BackgroundTasks，以支援多 worker、重試與任務超時。
- Stripe webhook 必須驗證簽章，並只接受來自 Stripe 的訂閱狀態變更。
- 所有報告讀取都必須以 `user_id` 篩選，避免跨用戶資料外洩。
