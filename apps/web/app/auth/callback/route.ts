import { NextResponse } from "next/server";
import { safeRedirectPath } from "@/lib/navigation.mjs";
import { createClient } from "@/lib/supabase/server";

export async function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get("code");
  const next = safeRedirectPath(requestUrl.searchParams.get("next"));

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (error) {
      return NextResponse.redirect(new URL("/login?error=callback", request.url));
    }
  }

  return NextResponse.redirect(new URL(next, request.url));
}
