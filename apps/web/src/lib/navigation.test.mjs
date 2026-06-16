import test from "node:test";
import assert from "node:assert/strict";
import { safeRedirectPath } from "./navigation.mjs";

test("safeRedirectPath allows same-site relative paths", () => {
  assert.equal(safeRedirectPath("/dashboard"), "/dashboard");
  assert.equal(safeRedirectPath("/reports/report_123?print=1"), "/reports/report_123?print=1");
});

test("safeRedirectPath rejects absolute and protocol-relative URLs", () => {
  assert.equal(safeRedirectPath("https://evil.example/phish"), "/dashboard");
  assert.equal(safeRedirectPath("//evil.example/phish"), "/dashboard");
  assert.equal(safeRedirectPath("javascript:alert(1)"), "/dashboard");
});
