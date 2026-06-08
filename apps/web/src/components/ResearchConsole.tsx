"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  analystLabel,
  apiRequest,
  depthLabel,
  statusProgress,
  type ApiDepth,
  type ResearchReport,
  type ResearchRun,
  type Subscription,
  type WatchlistItem,
} from "@/lib/api";
import { normalizeTicker } from "@/lib/usage.mjs";
import { DownloadIcon, PlayIcon, PlusIcon } from "./Icons";
import { QuotaMeter } from "./QuotaMeter";
import { StatusBadge } from "./StatusBadge";

const analystOptions = [
  { id: "market", label: "市場" },
  { id: "news", label: "新聞" },
  { id: "fundamentals", label: "基本面" },
  { id: "social", label: "社群" },
  { id: "risk", label: "風險" },
];

const depthOptions: { id: ApiDepth; label: "快速" | "標準" | "深度" }[] = [
  { id: "quick", label: "快速" },
  { id: "standard", label: "標準" },
  { id: "deep", label: "深度" },
];

const today = new Date().toISOString().slice(0, 10);

export function ResearchConsole() {
  const [ticker, setTicker] = useState("AAPL");
  const [reportDate, setReportDate] = useState(today);
  const [depth, setDepth] = useState<ApiDepth>("standard");
  const [analysts, setAnalysts] = useState(["market", "news", "fundamentals", "risk"]);
  const [runs, setRuns] = useState<ResearchRun[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [selectedReport, setSelectedReport] = useState<ResearchReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  const companyNames = useMemo(() => {
    return new Map(watchlist.map((item) => [item.ticker, item.companyName]));
  }, [watchlist]);

  const refresh = useCallback(async () => {
    setError("");
    const [nextSubscription, nextRuns, nextWatchlist] = await Promise.all([
      apiRequest<Subscription>("/api/subscription"),
      apiRequest<ResearchRun[]>("/api/research-runs"),
      apiRequest<WatchlistItem[]>("/api/watchlist"),
    ]);

    setSubscription(nextSubscription);
    setRuns(nextRuns);
    setWatchlist(nextWatchlist);

    const reportRun = nextRuns.find((run) => run.status === "completed" && run.reportId);
    if (reportRun?.reportId) {
      setSelectedReport(await apiRequest<ResearchReport>(`/api/reports/${reportRun.reportId}`));
    } else {
      setSelectedReport(null);
    }
  }, []);

  useEffect(() => {
    refresh()
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [refresh]);

  useEffect(() => {
    if (!runs.some((run) => run.status === "queued" || run.status === "running")) {
      return;
    }

    const timer = window.setInterval(() => {
      refresh().catch((err: Error) => setError(err.message));
    }, 2500);

    return () => window.clearInterval(timer);
  }, [refresh, runs]);

  function toggleAnalyst(name: string) {
    setAnalysts((current) =>
      current.includes(name) ? current.filter((item) => item !== name) : [...current, name],
    );
  }

  async function createRun() {
    const normalized = normalizeTicker(ticker);
    if (!normalized || creating || analysts.length === 0) {
      return;
    }

    setCreating(true);
    setError("");
    try {
      await apiRequest<ResearchRun>("/api/research-runs", {
        method: "POST",
        body: JSON.stringify({
          ticker: normalized,
          reportDate,
          depth,
          analysts,
        }),
      });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "建立研究任務失敗");
    } finally {
      setCreating(false);
    }
  }

  const quotaUsed = subscription?.periodReportsUsed ?? 0;
  const quotaLimit = subscription?.monthlyReports ?? 5;

  return (
    <div className="dashboard-grid">
      <section className="panel run-panel">
        <div className="panel-heading">
          <div>
            <h2>建立研究任務</h2>
            <p>輸入股票代號，選擇深度與代理組合。</p>
          </div>
          <button className="icon-button" aria-label="新增觀察標的">
            <PlusIcon size={18} />
          </button>
        </div>

        <div className="run-form">
          <label>
            <span>Ticker</span>
            <input value={ticker} onChange={(event) => setTicker(event.target.value)} />
          </label>
          <label>
            <span>報告日期</span>
            <input
              onChange={(event) => setReportDate(event.target.value)}
              type="date"
              value={reportDate}
            />
          </label>
          <div className="field-block">
            <span>分析深度</span>
            <div className="segments" role="group" aria-label="分析深度">
              {depthOptions.map((item) => (
                <button
                  key={item.id}
                  className={depth === item.id ? "selected" : ""}
                  onClick={() => setDepth(item.id)}
                  type="button"
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
          <div className="field-block analysts">
            <span>分析代理</span>
            <div>
              {analystOptions.map((item) => (
                <label key={item.id}>
                  <input
                    checked={analysts.includes(item.id)}
                    onChange={() => toggleAnalyst(item.id)}
                    type="checkbox"
                  />
                  {item.label}
                </label>
              ))}
            </div>
          </div>
          {error ? <p className="form-message">{error}</p> : null}
          <button className="primary-action" disabled={creating} onClick={createRun} type="button">
            <PlayIcon size={18} />
            {creating ? "建立中" : "執行研究"}
          </button>
        </div>
      </section>

      <section className="panel queue-panel">
        <div className="panel-heading">
          <div>
            <h2>研究佇列</h2>
            <p>TradingAgents 背景任務狀態</p>
          </div>
          <span className="soft-label">Postgres + worker</span>
        </div>
        <div className="run-list">
          {loading ? <p className="empty-state">載入研究任務中...</p> : null}
          {!loading && runs.length === 0 ? <p className="empty-state">尚未建立研究任務。</p> : null}
          {runs.map((run) => (
            <article className="run-row" key={run.id}>
              <div>
                <strong>{run.ticker}</strong>
                <span>{companyNames.get(run.ticker) ?? "研究標的"}</span>
              </div>
              <span>{depthLabel(run.depth)}</span>
              <span>{run.analysts.map(analystLabel).join("、")}</span>
              <StatusBadge status={run.status} />
              <div className="progress" aria-label={`${run.ticker} 進度 ${statusProgress(run.status)}%`}>
                <span style={{ width: `${statusProgress(run.status)}%` }} />
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="panel report-panel">
        <div className="panel-heading">
          <div>
            <h2>{selectedReport ? `${selectedReport.ticker} 最新研究摘要` : "最新研究摘要"}</h2>
            <p>
              {selectedReport
                ? `${selectedReport.ticker} · ${selectedReport.reportDate}`
                : "完成研究任務後會顯示最新報告。"}
            </p>
          </div>
          <button className="secondary-action" disabled={!selectedReport} type="button">
            <DownloadIcon size={17} />
            下載
          </button>
        </div>
        {selectedReport ? (
          <>
            <div className="report-sections">
              {Object.values(selectedReport.sections).map((section) => (
                <article key={section.title}>
                  <h3>{section.title}</h3>
                  <p>{section.content}</p>
                </article>
              ))}
            </div>
            <footer className="disclaimer">{selectedReport.disclaimer}</footer>
          </>
        ) : (
          <p className="empty-state padded">尚無完成報告。</p>
        )}
      </section>

      <aside className="right-rail">
        <QuotaMeter used={quotaUsed} limit={quotaLimit} />
        <section className="panel">
          <div className="panel-heading compact">
            <h2>觀察清單</h2>
          </div>
          <div className="watchlist">
            {watchlist.length === 0 ? <p className="empty-state">尚未加入標的。</p> : null}
            {watchlist.map((item) => (
              <div key={item.id}>
                <strong>{item.ticker}</strong>
                <span>{item.companyName}</span>
                <em className="positive">研究</em>
              </div>
            ))}
          </div>
        </section>
        <section className="panel billing-panel">
          <h2>訂閱狀態</h2>
          <p>
            {subscription
              ? `${subscription.plan} 方案，狀態：${subscription.status}。`
              : "正在載入訂閱狀態。"}
          </p>
          <a href="/billing">管理帳單</a>
        </section>
      </aside>
    </div>
  );
}
