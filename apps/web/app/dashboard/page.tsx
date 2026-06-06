import { AppShell } from "@/components/AppShell";
import { ResearchConsole } from "@/components/ResearchConsole";

export default function DashboardPage() {
  return (
    <AppShell
      active="/dashboard"
      title="儀表板"
      description="建立 AI 股票研究任務，追蹤執行狀態與月度報告配額。"
    >
      <ResearchConsole />
    </AppShell>
  );
}
