import { AppShell } from "@/components/AppShell";
import { ReportsList } from "@/components/ReportsList";
import { requireUser } from "@/lib/auth";

export const dynamic = "force-dynamic";

export default async function ReportsPage() {
  const user = await requireUser();

  return (
    <AppShell
      active="/reports"
      title="研究報告"
      description="查看所有已完成與執行中的 AI 研究報告。"
      userEmail={user.email}
    >
      <ReportsList />
    </AppShell>
  );
}
