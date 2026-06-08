"use client";

import { useEffect, useState } from "react";
import { apiRequest, type Subscription } from "@/lib/api";

const usageRows = [
  { label: "TradingAgents 研究任務", value: "依報告次數計量", cost: "平台吸收" },
  { label: "LLM tokens", value: "依每份報告記錄", cost: "平台吸收" },
  { label: "市場資料請求", value: "依代理工作流記錄", cost: "平台吸收" },
];

export function ApiUsagePanel() {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiRequest<Subscription>("/api/subscription")
      .then(setSubscription)
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <section className="panel page-panel">
      <div className="panel-heading">
        <div>
          <h2>本帳期成本</h2>
          <p>
            {subscription
              ? `${subscription.plan} 方案 · ${subscription.periodReportsUsed} / ${subscription.monthlyReports} 份報告`
              : "載入用量中..."}
          </p>
        </div>
      </div>
      {error ? <p className="form-message padded">{error}</p> : null}
      <div className="table-list">
        {usageRows.map((row) => (
          <div className="table-row usage-row" key={row.label}>
            <strong>{row.label}</strong>
            <span>{row.value}</span>
            <span>{row.cost}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
