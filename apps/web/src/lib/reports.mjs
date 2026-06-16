function runTimestamp(run) {
  const value = run.completedAt || run.createdAt || "";
  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) ? timestamp : 0;
}

export function latestCompletedRun(runs) {
  return (
    [...runs]
      .filter((run) => run.status === "completed" && run.reportId)
      .sort((a, b) => runTimestamp(b) - runTimestamp(a))[0] ?? null
  );
}
