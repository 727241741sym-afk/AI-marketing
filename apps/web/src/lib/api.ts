import { createClient } from "@/lib/supabase/client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type ApiDepth = "quick" | "standard" | "deep";
export type ApiStatus = "queued" | "running" | "completed" | "failed";

export type Subscription = {
  plan: string;
  status: string;
  monthlyReports: number;
  periodReportsUsed: number;
  remainingReports: number;
  stripeCustomerId?: string | null;
};

export type ResearchRun = {
  id: string;
  ticker: string;
  reportDate: string;
  depth: ApiDepth;
  analysts: string[];
  status: ApiStatus;
  createdAt: string;
  completedAt?: string | null;
  reportId?: string | null;
  errorMessage?: string | null;
};

export type ReportSection = {
  title: string;
  content: string;
};

export type ResearchReport = {
  ticker: string;
  reportDate: string;
  sections: {
    bullCase: ReportSection;
    bearCase: ReportSection;
    riskDebate: ReportSection;
    finalSynthesis: ReportSection;
  };
  sources: string[];
  costCents: number;
  disclaimer: string;
};

export type WatchlistItem = {
  id: string;
  ticker: string;
  companyName: string;
  createdAt: string;
};

type RequestOptions = Omit<RequestInit, "headers"> & {
  headers?: Record<string, string>;
};

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const supabase = createClient();
  const { data, error } = await supabase.auth.getSession();

  if (error || !data.session?.access_token) {
    window.location.href = "/login";
    throw new Error("請先登入");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${data.session.access_token}`,
      ...options.headers,
    },
  });

  if (response.status === 401) {
    await supabase.auth.signOut();
    window.location.href = "/login";
    throw new Error("登入已過期，請重新登入");
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const message =
      typeof payload?.detail === "string"
        ? payload.detail
        : payload?.detail?.message ?? "請求失敗，請稍後再試";
    throw new Error(message);
  }

  return payload as T;
}

export function depthLabel(depth: ApiDepth): "快速" | "標準" | "深度" {
  switch (depth) {
    case "quick":
      return "快速";
    case "deep":
      return "深度";
    case "standard":
    default:
      return "標準";
  }
}

export function analystLabel(analyst: string): string {
  return (
    {
      market: "市場",
      news: "新聞",
      fundamentals: "基本面",
      social: "社群",
      risk: "風險",
    }[analyst] ?? analyst
  );
}

export function statusProgress(status: ApiStatus): number {
  return {
    queued: 12,
    running: 62,
    completed: 100,
    failed: 100,
  }[status];
}
