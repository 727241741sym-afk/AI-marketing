"use client";

import { useEffect, useState } from "react";
import { apiRequest, type ResearchReport } from "@/lib/api";
import { DownloadIcon } from "./Icons";

export function ReportDetail({ reportId }: { reportId: string }) {
  const [report, setReport] = useState<ResearchReport | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiRequest<ResearchReport>(`/api/reports/${reportId}`)
      .then(setReport)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [reportId]);

  return (
    <section className="panel page-panel report-detail">
      <div className="panel-heading">
        <div>
          <h2>{report ? `${report.ticker} 研究報告` : "研究報告"}</h2>
          <p>
            {report
              ? `資料來源：${report.sources.join("、")} · 成本：${report.costCents} 美分`
              : `報告 ID：${reportId}`}
          </p>
        </div>
        <button className="secondary-action" disabled={!report} type="button">
          <DownloadIcon size={17} />
          下載 PDF
        </button>
      </div>

      {loading ? <p className="empty-state padded">載入報告中...</p> : null}
      {error ? <p className="form-message padded">{error}</p> : null}
      {report ? (
        <>
          <div className="report-sections expanded">
            {Object.values(report.sections).map((section) => (
              <article key={section.title}>
                <h3>{section.title}</h3>
                <p>{section.content}</p>
              </article>
            ))}
          </div>
          <footer className="disclaimer">{report.disclaimer}</footer>
        </>
      ) : null}
    </section>
  );
}
