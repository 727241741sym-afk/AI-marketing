import { AppShell } from "@/components/AppShell";
import { ResearchConsole } from "@/components/ResearchConsole";
import { requireUser } from "@/lib/auth";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const user = await requireUser();

  return (
    <AppShell
      active="/dashboard"
      title="儀表板"
      description="建立 AI 股票研究任務，追蹤執行狀態與月度報告配額。"
      userEmail={user.email}
    >
      <ResearchConsole />
    </AppShell>
  );
}
