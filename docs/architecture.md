# Atlas Research Architecture

## Request Flow

1. 使用者透過 Supabase Auth 登入，Next.js SSR middleware 維持 cookie session。
2. Next.js 儀表板用 Supabase access token 呼叫 FastAPI。
3. FastAPI 驗證 `Authorization: Bearer <token>`，只信任 Supabase 回傳的 `user.id`。
4. `POST /api/research-runs` 在同一個 Postgres transaction 中鎖定訂閱、檢查配額、扣一次月度額度、建立研究任務與 usage event。
5. 後端建立 `atlas_research_runs`，並將 run id 放進 Redis/RQ queue。
6. Railway worker 取出 job，透過 TradingAgents adapter 與 MiniMax M3 取得 `state` 與 `decision`。
7. `report_mapper` 將結果轉成繁體中文報告區塊並寫入 `atlas_reports`。
8. 前端輪詢 `GET /api/research-runs/:id`，完成後導向 `GET /api/reports/:id`。

## Production Notes

- Runtime 預設使用 `PostgresRepository`；`InMemoryRepository` 僅保留給單元測試或明確設定 `REPOSITORY_BACKEND=memory` 的本地實驗。
- Postgres 表定義在 `infra/postgres/001_init.sql`，所有 app-owned 表使用 `atlas_` 前綴，避免碰到同一 Supabase project 裡既有 schema。
- Supabase exposed schema 中的 user-owned 表都啟用 RLS，policy 使用 `(select auth.uid()) = user_id`，並對 `user_id` 建索引。
- Staging 使用 Redis/RQ，不用 FastAPI BackgroundTasks；API 只負責排程，worker 負責長任務、失敗寫回與報告持久化。
- TradingAgents staging 預設 `llm_provider=minimax`、`deep_think_llm=MiniMax-M3`、`quick_think_llm=MiniMax-M3`、`output_language=Traditional Chinese`。
- Stripe webhook 必須驗證簽章，並以 `stripe_customer_id` 同步訂閱狀態。
- 所有報告讀取都必須以已驗證的 Supabase `user.id` 篩選，避免跨用戶資料外洩。
