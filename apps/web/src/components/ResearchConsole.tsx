"use client";

import { useMemo, useState } from "react";
import { normalizeTicker } from "@/lib/usage.mjs";
import { latestReport, quota as initialQuota, researchRuns, watchlist } from "@/lib/sampleData";
import type { ResearchRun } from "@/lib/sampleData";
import { DownloadIcon, PlayIcon, PlusIcon } from "./Icons";
import { QuotaMeter } from "./QuotaMeter";
import { StatusBadge } from "./StatusBadge";

const analystOptions = ["市場", "新聞", "基本面", "社群", "風險"];

export function ResearchConsole() {
  const [ticker, setTicker] = useState("AAPL");
  const [depth, setDepth] = useState<"快速" | "標準" | "深度">("標準");
  const [analysts, setAnalysts] = useState(["市場", "新聞", "基本面", "風險"]);
  const [runs, setRuns] = useState<ResearchRun[]>(researchRuns);
  const [used, setUsed] = useState(initialQuota.used);

  const selectedReport = useMemo(() => latestReport, []);

  function toggleAnalyst(name: string) {
    setAnalysts((current) =>
      current.includes(name) ? current.filter((item) => item !== name) : [...current, name],
    );
  }

  function createRun() {
    const normalized = normalizeTicker(ticker);
    if (!normalized || used >= initialQuota.limit) {
      return;
    }

    const nextRun: ResearchRun = {
      id: `run_${normalized.toLowerCase()}_${Date.now()}`,
      ticker: normalized,
      company: "新研究標的",
      reportDate: "2026-06-06",
      depth,
      analysts,
      status: "queued",
      progress: 8,
      createdAt: "剛剛",
    };

    setRuns((current) => [nextRun, ...current]);
    setUsed((current) => current + 1);

    window.setTimeout(() => {
      setRuns((current) =>
        current.map((run) =>
          run.id === nextRun.id ? { ...run, status: "running", progress: 48 } : run,
        ),
      );
    }, 600);

    window.setTimeout(() => {
      setRuns((current) =>
        current.map((run) =>
          run.id === nextRun.id ? { ...run, status: "completed", progress: 100 } : run,
        ),
      );
    }, 1700);
  }

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
            <input type="date" defaultValue="2026-06-06" />
          </label>
          <div className="field-block">
            <span>分析深度</span>
            <div className="segments" role="group" aria-label="分析深度">
              {(["快速", "標準", "深度"] as const).map((item) => (
                <button
                  key={item}
                  className={depth === item ? "selected" : ""}
                  onClick={() => setDepth(item)}
                  type="button"
                >
                  {item}
                </button>
              ))}
            </div>
          </div>
          <div className="field-block analysts">
            <span>分析代理</span>
            <div>
              {analystOptions.map((item) => (
                <label key={item}>
                  <input
                    checked={analysts.includes(item)}
                    onChange={() => toggleAnalyst(item)}
                    type="checkbox"
                  />
                  {item}
                </label>
              ))}
            </div>
          </div>
          <button className="primary-action" onClick={createRun} type="button">
            <PlayIcon size={18} />
            執行研究
          </button>
        </div>
      </section>

      <section className="panel queue-panel">
        <div className="panel-heading">
          <div>
            <h2>研究佇列</h2>
            <p>TradingAgents 背景任務狀態</p>
          </div>
          <span className="soft-label">Redis worker</span>
        </div>
        <div className="run-list">
          {runs.map((run) => (
            <article className="run-row" key={run.id}>
              <div>
                <strong>{run.ticker}</strong>
                <span>{run.company}</span>
              </div>
              <span>{run.depth}</span>
              <span>{run.analysts.join("、")}</span>
              <StatusBadge status={run.status} />
              <div className="progress" aria-label={`${run.ticker} 進度 ${run.progress}%`}>
                <span style={{ width: `${run.progress}%` }} />
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="panel report-panel">
        <div className="panel-heading">
          <div>
            <h2>{selectedReport.ticker} 最新研究摘要</h2>
            <p>{selectedReport.company} · {selectedReport.reportDate}</p>
          </div>
          <button className="secondary-action" type="button">
            <DownloadIcon size={17} />
            下載
          </button>
        </div>
        <div className="report-sections">
          {selectedReport.sections.map((section) => (
            <article key={section.title}>
              <h3>{section.title}</h3>
              <p>{section.content}</p>
            </article>
          ))}
        </div>
        <footer className="disclaimer">僅供研究用途，不構成投資建議或交易建議。</footer>
      </section>

      <aside className="right-rail">
        <QuotaMeter used={used} limit={initialQuota.limit} />
        <section className="panel">
          <div className="panel-heading compact">
            <h2>觀察清單</h2>
          </div>
          <div className="watchlist">
            {watchlist.map((item) => (
              <div key={item.ticker}>
                <strong>{item.ticker}</strong>
                <span>{item.name}</span>
                <em className={item.tone}>{item.change}</em>
              </div>
            ))}
          </div>
        </section>
        <section className="panel billing-panel">
          <h2>訂閱狀態</h2>
          <p>Pro 方案啟用中。可在帳單頁更新付款方式或升級配額。</p>
          <a href="/billing">管理帳單</a>
        </section>
      </aside>
    </div>
  );
}
