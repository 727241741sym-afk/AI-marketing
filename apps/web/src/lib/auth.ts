import { redirect } from "next/navigation";
import { hasSupabaseConfig } from "@/lib/supabase/config";
import { createClient } from "@/lib/supabase/server";

export type AppUser = {
  id: string;
  email: string;
};

export async function requireUser(): Promise<AppUser> {
  if (!hasSupabaseConfig()) {
    redirect("/login?config=missing");
  }

  const supabase = await createClient();
  const { data, error } = await supabase.auth.getClaims();
  const claims = data?.claims as { sub?: string; email?: string } | undefined;

  if (error || !claims?.sub) {
    redirect("/login");
  }

  return {
    id: claims.sub,
    email: claims.email ?? "已登入使用者",
  };
}
