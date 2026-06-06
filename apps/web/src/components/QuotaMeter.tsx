import { formatQuota, getQuotaState } from "@/lib/usage.mjs";

export function QuotaMeter({ used, limit }: { used: number; limit: number }) {
  const quota = getQuotaState(used, limit);

  return (
    <section className={`panel quota ${quota.tone}`}>
      <div className="panel-heading">
        <div>
          <h2>本月用量</h2>
          <p>{formatQuota(used, limit)}</p>
        </div>
        <strong>{quota.remaining}</strong>
      </div>
      <div className="meter" aria-label="本月報告用量">
        <span style={{ width: `${quota.percentUsed}%` }} />
      </div>
      <p className="quota-note">剩餘 {quota.remaining} 份研究報告，超出後需升級或等下一個帳期。</p>
    </section>
  );
}
