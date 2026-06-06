export function normalizeTicker(value) {
  return String(value ?? "").trim().toUpperCase();
}

export function formatQuota(used, limit) {
  return `${used} / ${limit} 份報告已使用`;
}

export function getQuotaState(used, limit) {
  const safeLimit = Math.max(Number(limit) || 0, 0);
  const safeUsed = Math.max(Number(used) || 0, 0);
  const remaining = Math.max(safeLimit - safeUsed, 0);
  const percentUsed = safeLimit === 0 ? 100 : Math.min(Math.round((safeUsed / safeLimit) * 100), 100);
  const tone = remaining === 0 ? "blocked" : percentUsed >= 80 ? "warning" : "healthy";

  return {
    remaining,
    percentUsed,
    tone,
  };
}
