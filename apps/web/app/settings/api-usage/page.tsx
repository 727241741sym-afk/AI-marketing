import { AppShell } from "@/components/AppShell";
import { ApiUsagePanel } from "@/components/ApiUsagePanel";
import { requireUser } from "@/lib/auth";

export const dynamic = "force-dynamic";

export default async function ApiUsagePage() {
  const user = await requireUser();

  return (
    <AppShell
      active="/settings/api-usage"
      title="API 用量"
      description="追蹤平台吸收的 LLM 與市場資料成本。"
      userEmail={user.email}
    >
      <ApiUsagePanel />
    </AppShell>
  );
}
