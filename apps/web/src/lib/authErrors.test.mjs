import test from "node:test";
import assert from "node:assert/strict";
import { authErrorMessage } from "./authErrors.mjs";

test("authErrorMessage explains Supabase network failures in Chinese", () => {
  assert.match(authErrorMessage({ message: "Failed to fetch" }), /無法連線到登入服務/);
  assert.match(authErrorMessage({ message: "fetch failed" }), /Supabase 專案已啟用/);
});

test("authErrorMessage keeps actionable auth API messages", () => {
  assert.equal(authErrorMessage({ message: "Invalid login credentials" }), "Invalid login credentials");
});

test("authErrorMessage falls back for unknown errors", () => {
  assert.equal(authErrorMessage(null), "登入失敗，請稍後再試。");
});
