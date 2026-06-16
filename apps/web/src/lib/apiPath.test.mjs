import test from "node:test";
import assert from "node:assert/strict";
import { apiPath } from "./apiPath.mjs";

test("apiPath normalizes API requests to same-origin paths", () => {
  assert.equal(apiPath("/api/subscription"), "/api/subscription");
  assert.equal(apiPath("api/research-runs"), "/api/research-runs");
});

test("apiPath rejects absolute API URLs", () => {
  assert.throws(() => apiPath("https://api.example.test/api/subscription"), /same-origin/);
});
