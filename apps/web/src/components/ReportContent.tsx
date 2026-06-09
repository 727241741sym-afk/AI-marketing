"use client";

import type { ResearchReport, ReportSection } from "@/lib/api";
import {
  parseInlineFormatting,
  parseReportContent,
} from "@/lib/reportFormatting.mjs";

type ReportBlock =
  | { type: "heading"; depth: number; text: string }
  | { type: "paragraph"; text: string }
  | { type: "list"; ordered: boolean; items: string[] }
  | { type: "rule" };

type InlineToken = { type: "text" | "strong" | "code"; text: string };

function InlineText({ text }: { text: string }) {
  return (
    <>
      {(parseInlineFormatting(text) as InlineToken[]).map((token, index) => {
        if (token.type === "strong") {
          return <strong key={`${token.type}-${index}`}>{token.text}</strong>;
        }
        if (token.type === "code") {
          return <code key={`${token.type}-${index}`}>{token.text}</code>;
        }
        return <span key={`${token.type}-${index}`}>{token.text}</span>;
      })}
    </>
  );
}

function ReportBlockView({ block }: { block: ReportBlock }) {
  if (block.type === "rule") {
    return <hr />;
  }

  if (block.type === "heading") {
    return (
      <h4 className={block.depth <= 2 ? "major" : undefined}>
        <InlineText text={block.text} />
      </h4>
    );
  }

  if (block.type === "list") {
    const ListTag = block.ordered ? "ol" : "ul";
    return (
      <ListTag>
        {block.items.map((item, index) => (
          <li key={`${item}-${index}`}>
            <InlineText text={item} />
          </li>
        ))}
      </ListTag>
    );
  }

  return (
    <p>
      <InlineText text={block.text} />
    </p>
  );
}

function ReportSectionCard({ section }: { section: ReportSection }) {
  const blocks = parseReportContent(section.content) as ReportBlock[];

  return (
    <article>
      <h3>{section.title}</h3>
      <div className="report-section-body">
        {blocks.map((block, index) => (
          <ReportBlockView block={block} key={`${block.type}-${index}`} />
        ))}
      </div>
    </article>
  );
}

export function ReportMetadata({ report }: { report: ResearchReport }) {
  return (
    <div className="report-meta" aria-label="報告資訊">
      <span className="report-meta-label">資料來源</span>
      {report.sources.length ? (
        report.sources.map((source) => (
          <span className="meta-chip" key={source}>
            {source}
          </span>
        ))
      ) : (
        <span className="meta-chip">未記錄來源</span>
      )}
      <span className="meta-chip">成本：{report.costCents} 美分</span>
    </div>
  );
}

export function ReportContent({
  report,
  expanded = false,
}: {
  report: ResearchReport;
  expanded?: boolean;
}) {
  return (
    <div className={expanded ? "report-sections expanded" : "report-sections"}>
      {Object.values(report.sections).map((section) => (
        <ReportSectionCard key={section.title} section={section} />
      ))}
    </div>
  );
}
