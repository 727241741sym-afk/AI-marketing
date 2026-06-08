import { AppShell } from "@/components/AppShell";
import { BillingPanel } from "@/components/BillingPanel";
import { requireUser } from "@/lib/auth";

export const dynamic = "force-dynamic";

export default async function BillingPage() {
  const user = await requireUser();

  return (
    <AppShell
      active="/billing"
      title="帳單"
      description="管理月費訂閱、付款方式與報告配額。"
      userEmail={user.email}
    >
      <BillingPanel />
    </AppShell>
  );
}
