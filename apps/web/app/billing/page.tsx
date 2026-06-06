import { AppShell } from "@/components/AppShell";
import { CreditCardIcon } from "@/components/Icons";
import { QuotaMeter } from "@/components/QuotaMeter";
import { quota } from "@/lib/sampleData";

export default function BillingPage() {
  return (
    <AppShell active="/billing" title="帳單" description="管理月費訂閱、付款方式與報告配額。">
      <div className="billing-grid">
        <QuotaMeter used={quota.used} limit={quota.limit} />
        <section className="panel page-panel">
          <div className="panel-heading">
            <div>
              <h2>Pro 方案</h2>
              <p>每月 50 份 AI 股票研究報告，包含平台 LLM 與市場資料用量。</p>
            </div>
            <span className="price">US$49/月</span>
          </div>
          <div className="billing-actions">
            <button className="primary-action" type="button">
              <CreditCardIcon size={18} />
              開啟 Stripe 帳戶入口
            </button>
            <button className="secondary-action" type="button">升級配額</button>
          </div>
          <p className="disclaimer">付款、續訂、升降級與取消訂閱由 Stripe Billing 處理。</p>
        </section>
      </div>
    </AppShell>
  );
}
