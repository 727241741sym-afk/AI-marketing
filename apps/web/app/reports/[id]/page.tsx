import { AppShell } from "@/components/AppShell";
import { DownloadIcon } from "@/components/Icons";
import { latestReport } from "@/lib/sampleData";

export default async function ReportDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  return (
    <AppShell
      active="/reports"
      title={`${latestReport.ticker} 研究報告`}
      description={`報告 ID：${id} · ${latestReport.reportDate}`}
    >
      <section className="panel page-panel report-detail">
        <div className="panel-heading">
          <div>
            <h2>{latestReport.company}</h2>
            <p>資料來源：{latestReport.sources.join("、")} · 成本：{latestReport.costCents} 美分</p>
          </div>
          <button className="secondary-action" type="button">
            <DownloadIcon size={17} />
            下載 PDF
          </button>
        </div>
        <div className="report-sections expanded">
          {latestReport.sections.map((section) => (
            <article key={section.title}>
              <h3>{section.title}</h3>
              <p>{section.content}</p>
            </article>
          ))}
        </div>
        <footer className="disclaimer">僅供研究用途，不構成投資建議或交易建議。</footer>
      </section>
    </AppShell>
  );
}
