import type { ResearchStatus } from "@/lib/sampleData";

const labelMap: Record<ResearchStatus, string> = {
  queued: "佇列中",
  running: "執行中",
  completed: "已完成",
  failed: "失敗",
};

export function StatusBadge({ status }: { status: ResearchStatus }) {
  return <span className={`status-badge ${status}`}>{labelMap[status]}</span>;
}
