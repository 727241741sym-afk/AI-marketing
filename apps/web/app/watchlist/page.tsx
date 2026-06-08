import { AppShell } from "@/components/AppShell";
import { WatchlistManager } from "@/components/WatchlistManager";
import { requireUser } from "@/lib/auth";

export const dynamic = "force-dynamic";

export default async function WatchlistPage() {
  const user = await requireUser();

  return (
    <AppShell
      active="/watchlist"
      title="觀察清單"
      description="管理個人研究標的，快速建立下一份報告。"
      userEmail={user.email}
    >
      <WatchlistManager />
    </AppShell>
  );
}
