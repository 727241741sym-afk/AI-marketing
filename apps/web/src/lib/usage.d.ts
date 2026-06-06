export function normalizeTicker(value: string): string;
export function formatQuota(used: number, limit: number): string;
export function getQuotaState(
  used: number,
  limit: number,
): {
  remaining: number;
  percentUsed: number;
  tone: "healthy" | "warning" | "blocked";
};
