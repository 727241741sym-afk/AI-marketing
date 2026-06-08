import { AppShell } from "@/components/AppShell";
import { ReportDetail } from "@/components/ReportDetail";
import { requireUser } from "@/lib/auth";

export const dynamic = "force-dynamic";

export default async function ReportDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const [{ id }, user] = await Promise.all([params, requireUser()]);

  return (
    <AppShell
      active="/reports"
      title="研究報告"
      description={`報告 ID：${id}`}
      userEmail={user.email}
    >
      <ReportDetail reportId={id} />
    </AppShell>
  );
}
