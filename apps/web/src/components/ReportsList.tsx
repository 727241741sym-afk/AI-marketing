"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiRequest, analystLabel, depthLabel, type ResearchRun } from "@/lib/api";
import { StatusBadge } from "./StatusBadge";

export function ReportsList() {
  const [runs, setRuns] = useState<ResearchRun[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiRequest<ResearchRun[]>("/api/research-runs")
      .then(setRuns)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className="panel page-panel">
      <div className="panel-heading">
        <div>
          <h2>報告歷史</h2>
          <p>每份報告保留來源、成本與研究日期。</p>
        </div>
      </div>
      <div className="table-list">
        {loading ? <p className="empty-state">載入報告中...</p> : null}
        {error ? <p className="form-message">{error}</p> : null}
        {!loading && runs.length === 0 ? <p className="empty-state">尚未建立研究任務。</p> : null}
        {runs.map((run) => {
          const content = (
            <>
              <strong>{run.ticker}</strong>
              <span>{run.reportDate}</span>
              <span>{depthLabel(run.depth)}</span>
              <span>{run.analysts.map(analystLabel).join("、")}</span>
              <StatusBadge status={run.status} />
            </>
          );

          return run.reportId ? (
            <Link className="table-row" href={`/reports/${run.reportId}`} key={run.id}>
              {content}
            </Link>
          ) : (
            <div className="table-row" key={run.id}>
              {content}
            </div>
          );
        })}
      </div>
    </section>
  );
}
