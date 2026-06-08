import type { ApiStatus } from "@/lib/api";

const labelMap: Record<ApiStatus, string> = {
  queued: "佇列中",
  running: "執行中",
  completed: "已完成",
  failed: "失敗",
};

export function StatusBadge({ status }: { status: ApiStatus }) {
  return <span className={`status-badge ${status}`}>{labelMap[status]}</span>;
}
