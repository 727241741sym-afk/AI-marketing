import test from "node:test";
import assert from "node:assert/strict";
import { printCurrentReport } from "./reportPrint.mjs";

test("printCurrentReport calls browser print when available", () => {
  let called = false;

  const didPrint = printCurrentReport({
    print() {
      called = true;
    },
  });

  assert.equal(didPrint, true);
  assert.equal(called, true);
});

test("printCurrentReport reports unavailable print targets", () => {
  assert.equal(printCurrentReport({}), false);
});
