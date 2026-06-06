import test from "node:test";
import assert from "node:assert/strict";
import {
  formatQuota,
  getQuotaState,
  normalizeTicker,
} from "./usage.mjs";

test("formatQuota renders Traditional Chinese report usage text", () => {
  assert.equal(formatQuota(38, 50), "38 / 50 份報告已使用");
});

test("getQuotaState reports warning before quota is exhausted", () => {
  assert.deepEqual(getQuotaState(45, 50), {
    remaining: 5,
    percentUsed: 90,
    tone: "warning",
  });
});

test("getQuotaState reports blocked when quota is exhausted", () => {
  assert.deepEqual(getQuotaState(50, 50), {
    remaining: 0,
    percentUsed: 100,
    tone: "blocked",
  });
});

test("normalizeTicker trims and uppercases ticker symbols", () => {
  assert.equal(normalizeTicker(" aapl "), "AAPL");
});
