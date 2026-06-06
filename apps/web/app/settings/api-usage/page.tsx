import { AppShell } from "@/components/AppShell";
import { quota } from "@/lib/sampleData";

const usageRows = [
  { label: "TradingAgents 研究任務", value: "38 次", cost: "US$31.92" },
  { label: "LLM tokens", value: "1.8M", cost: "US$24.10" },
  { label: "市場資料請求", value: "412 次", cost: "US$7.82" },
];

export default function ApiUsagePage() {
  return (
    <AppShell active="/settings/api-usage" title="API 用量" description="追蹤平台吸收的 LLM 與市場資料成本。">
      <section className="panel page-panel">
        <div className="panel-heading">
          <div>
            <h2>本帳期成本</h2>
            <p>{quota.plan} · 用量由平台 API keys 支付並受月度配額限制。</p>
          </div>
        </div>
        <div className="table-list">
          {usageRows.map((row) => (
            <div className="table-row" key={row.label}>
              <strong>{row.label}</strong>
              <span>{row.value}</span>
              <span>{row.cost}</span>
            </div>
          ))}
        </div>
      </section>
    </AppShell>
  );
}
