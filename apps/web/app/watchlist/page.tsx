import { AppShell } from "@/components/AppShell";
import { PlusIcon } from "@/components/Icons";
import { watchlist } from "@/lib/sampleData";

export default function WatchlistPage() {
  return (
    <AppShell active="/watchlist" title="觀察清單" description="管理個人研究標的，快速建立下一份報告。">
      <section className="panel page-panel">
        <div className="panel-heading">
          <div>
            <h2>追蹤標的</h2>
            <p>觀察清單只用於研究排程，不會觸發任何交易行為。</p>
          </div>
          <button className="primary-action compact-action" type="button">
            <PlusIcon size={17} />
            新增標的
          </button>
        </div>
        <div className="table-list">
          {watchlist.map((item) => (
            <div className="table-row" key={item.ticker}>
              <strong>{item.ticker}</strong>
              <span>{item.name}</span>
              <span>下次研究：未排程</span>
              <em className={item.tone}>{item.change}</em>
            </div>
          ))}
        </div>
      </section>
    </AppShell>
  );
}
