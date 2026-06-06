import Link from "next/link";
import { AppShell } from "@/components/AppShell";
import { StatusBadge } from "@/components/StatusBadge";
import { latestReport, researchRuns } from "@/lib/sampleData";

export default function ReportsPage() {
  return (
    <AppShell active="/reports" title="研究報告" description="查看所有已完成與執行中的 AI 研究報告。">
      <section className="panel page-panel">
        <div className="panel-heading">
          <div>
            <h2>報告歷史</h2>
            <p>每份報告保留來源、成本與研究日期。</p>
          </div>
          <Link className="secondary-action" href={`/reports/${latestReport.id}`}>開啟最新報告</Link>
        </div>
        <div className="table-list">
          {researchRuns.map((run) => (
            <Link className="table-row" href={`/reports/${latestReport.id}`} key={run.id}>
              <strong>{run.ticker}</strong>
              <span>{run.company}</span>
              <span>{run.reportDate}</span>
              <span>{run.depth}</span>
              <StatusBadge status={run.status} />
            </Link>
          ))}
        </div>
      </section>
    </AppShell>
  );
}
