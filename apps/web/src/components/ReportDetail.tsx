"use client";

import { useEffect, useState } from "react";
import { apiRequest, type ResearchReport } from "@/lib/api";
import { printCurrentReport } from "@/lib/reportPrint.mjs";
import { DownloadIcon } from "./Icons";
import { ReportContent, ReportMetadata } from "./ReportContent";

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

  function printReport() {
    printCurrentReport();
  }

  return (
    <section className="panel page-panel report-detail">
      <div className="panel-heading">
        <div>
          <h2>{report ? `${report.ticker} 研究報告` : "研究報告"}</h2>
          {report ? <ReportMetadata report={report} /> : <p>報告 ID：{reportId}</p>}
        </div>
        <button
          className="secondary-action no-print"
          disabled={!report}
          onClick={printReport}
          type="button"
        >
          <DownloadIcon size={17} />
          下載 PDF
        </button>
      </div>

      {loading ? <p className="empty-state padded">載入報告中...</p> : null}
      {error ? <p className="form-message padded">{error}</p> : null}
      {report ? (
        <>
          <ReportContent expanded report={report} />
          <footer className="disclaimer">{report.disclaimer}</footer>
        </>
      ) : null}
    </section>
  );
}
