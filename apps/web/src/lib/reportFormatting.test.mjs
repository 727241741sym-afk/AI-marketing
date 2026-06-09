import test from "node:test";
import assert from "node:assert/strict";
import {
  parseInlineFormatting,
  parseReportContent,
} from "./reportFormatting.mjs";

test("parseReportContent separates markdown headings, paragraphs, lists, and rules", () => {
  const blocks = parseReportContent(
    "Bull Analyst: # AAPL 牛市觀點\n\n" +
      "營收仍具韌性，**服務毛利率**改善。\n\n" +
      "---\n\n" +
      "## 風險提醒\n" +
      "- 估值偏高\n" +
      "- 匯率波動",
  );

  assert.deepEqual(blocks, [
    { type: "paragraph", text: "Bull Analyst:" },
    { type: "heading", depth: 1, text: "AAPL 牛市觀點" },
    { type: "paragraph", text: "營收仍具韌性，**服務毛利率**改善。" },
    { type: "rule" },
    { type: "heading", depth: 2, text: "風險提醒" },
    { type: "list", ordered: false, items: ["估值偏高", "匯率波動"] },
  ]);
});

test("parseReportContent splits inline section markers from TradingAgents output", () => {
  const blocks = parseReportContent(
    "估值仍需留意。 --- ## 一、基本面 支撐現金流。 --- ## 二、催化因素 新品週期可能改善。",
  );

  assert.deepEqual(blocks, [
    { type: "paragraph", text: "估值仍需留意。" },
    { type: "rule" },
    { type: "heading", depth: 2, text: "一、基本面 支撐現金流。" },
    { type: "rule" },
    { type: "heading", depth: 2, text: "二、催化因素 新品週期可能改善。" },
  ]);
});

test("parseInlineFormatting returns safe text and strong tokens", () => {
  assert.deepEqual(parseInlineFormatting("Apple **服務業務** 持續增長。"), [
    { type: "text", text: "Apple " },
    { type: "strong", text: "服務業務" },
    { type: "text", text: " 持續增長。" },
  ]);
});
