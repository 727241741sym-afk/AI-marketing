"use client";

import { useEffect, useState } from "react";
import { apiRequest, type CheckoutSession, type Subscription } from "@/lib/api";
import { CreditCardIcon } from "./Icons";
import { QuotaMeter } from "./QuotaMeter";

export function BillingPanel() {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [error, setError] = useState("");
  const [loadingPortal, setLoadingPortal] = useState(false);
  const [loadingCheckout, setLoadingCheckout] = useState(false);

  useEffect(() => {
    apiRequest<Subscription>("/api/subscription")
      .then(setSubscription)
      .catch((err: Error) => setError(err.message));
  }, []);

  async function openPortal() {
    setLoadingPortal(true);
    setError("");
    try {
      const result = await apiRequest<{ url: string }>("/api/billing/portal");
      window.location.href = result.url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "無法開啟 Stripe 帳戶入口");
      setLoadingPortal(false);
    }
  }

  async function openCheckout() {
    setLoadingCheckout(true);
    setError("");
    try {
      const result = await apiRequest<CheckoutSession>("/api/billing/checkout", {
        method: "POST",
      });
      window.location.href = result.url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "無法開啟 Stripe 結帳流程");
      setLoadingCheckout(false);
    }
  }

  const used = subscription?.periodReportsUsed ?? 0;
  const limit = subscription?.monthlyReports ?? 5;

  return (
    <div className="billing-grid">
      <QuotaMeter used={used} limit={limit} />
      <section className="panel page-panel">
        <div className="panel-heading">
          <div>
            <h2>{subscription ? `${subscription.plan} 方案` : "訂閱方案"}</h2>
            <p>每月 AI 股票研究報告配額，包含平台 LLM 與市場資料用量。</p>
          </div>
          <span className="price">{subscription?.status ?? "載入中"}</span>
        </div>
        <div className="billing-actions">
          <button
            className="primary-action"
            disabled={loadingPortal || loadingCheckout}
            onClick={openPortal}
            type="button"
          >
            <CreditCardIcon size={18} />
            {loadingPortal ? "開啟中" : "開啟 Stripe 帳戶入口"}
          </button>
          <button
            className="secondary-action"
            disabled={loadingCheckout || loadingPortal}
            onClick={openCheckout}
            type="button"
          >
            {loadingCheckout ? "開啟中" : "升級配額"}
          </button>
        </div>
        {error ? <p className="form-message padded">{error}</p> : null}
        <p className="disclaimer">付款、續訂、升降級與取消訂閱由 Stripe Billing 處理。</p>
      </section>
    </div>
  );
}
