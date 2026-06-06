export type ResearchStatus = "queued" | "running" | "completed" | "failed";

export type ResearchRun = {
  id: string;
  ticker: string;
  company: string;
  reportDate: string;
  depth: "快速" | "標準" | "深度";
  analysts: string[];
  status: ResearchStatus;
  progress: number;
  createdAt: string;
};

export type ReportSection = {
  title: string;
  content: string;
};

export type Report = {
  id: string;
  ticker: string;
  company: string;
  reportDate: string;
  status: ResearchStatus;
  costCents: number;
  sections: ReportSection[];
  sources: string[];
};

export const quota = {
  plan: "Pro 方案",
  used: 38,
  limit: 50,
};

export const researchRuns: ResearchRun[] = [
  {
    id: "run_aapl_0606",
    ticker: "AAPL",
    company: "Apple Inc.",
    reportDate: "2026-06-06",
    depth: "標準",
    analysts: ["市場", "新聞", "基本面", "風險"],
    status: "running",
    progress: 64,
    createdAt: "09:42",
  },
  {
    id: "run_msft_0605",
    ticker: "MSFT",
    company: "Microsoft",
    reportDate: "2026-06-05",
    depth: "深度",
    analysts: ["市場", "基本面", "社群"],
    status: "completed",
    progress: 100,
    createdAt: "昨天",
  },
  {
    id: "run_nvda_0605",
    ticker: "NVDA",
    company: "NVIDIA",
    reportDate: "2026-06-05",
    depth: "快速",
    analysts: ["市場", "新聞"],
    status: "completed",
    progress: 100,
    createdAt: "昨天",
  },
];

export const latestReport: Report = {
  id: "report_aapl_0606",
  ticker: "AAPL",
  company: "Apple Inc.",
  reportDate: "2026-06-06",
  status: "running",
  costCents: 84,
  sections: [
    {
      title: "多頭觀點",
      content:
        "服務收入與生態黏性仍是核心支撐。若硬體換機週期回升，營收品質與自由現金流可維持韌性。",
    },
    {
      title: "空頭觀點",
      content:
        "估值已反映大量樂觀預期，若成長放緩或監管成本升高，市場可能先壓縮本益比。",
    },
    {
      title: "風險辯論",
      content:
        "主要風險集中在供應鏈、監管與大型科技支出週期；防守面來自現金流、回購能力與產品生態。",
    },
    {
      title: "最終綜合",
      content:
        "目前較適合作為觀察清單核心標的，等待更清楚的安全邊際。本報告僅供研究用途。",
    },
  ],
  sources: ["TradingAgents", "Yahoo Finance", "Finnhub", "Reddit"],
};

export const watchlist = [
  { ticker: "AAPL", name: "Apple Inc.", change: "+0.8%", tone: "positive" },
  { ticker: "MSFT", name: "Microsoft", change: "-0.3%", tone: "negative" },
  { ticker: "NVDA", name: "NVIDIA", change: "+1.6%", tone: "positive" },
  { ticker: "TSM", name: "台積電 ADR", change: "+0.4%", tone: "positive" },
];
