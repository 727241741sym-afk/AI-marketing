import test from "node:test";
import assert from "node:assert/strict";
import { latestCompletedRun } from "./reports.mjs";

test("latestCompletedRun returns newest completed run with a report id", () => {
  const latest = latestCompletedRun([
    {
      id: "run_old",
      status: "completed",
      reportId: "report_old",
      createdAt: "2026-06-01T00:00:00.000Z",
      completedAt: "2026-06-01T00:05:00.000Z",
    },
    {
      id: "run_running",
      status: "running",
      reportId: null,
      createdAt: "2026-06-03T00:00:00.000Z",
      completedAt: null,
    },
    {
      id: "run_new",
      status: "completed",
      reportId: "report_new",
      createdAt: "2026-06-02T00:00:00.000Z",
      completedAt: "2026-06-02T00:05:00.000Z",
    },
  ]);

  assert.equal(latest?.id, "run_new");
});

test("latestCompletedRun returns null when no completed report exists", () => {
  assert.equal(
    latestCompletedRun([{ id: "run_1", status: "queued", createdAt: "2026-06-01T00:00:00.000Z" }]),
    null,
  );
});
