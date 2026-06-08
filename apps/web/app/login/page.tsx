"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { hasSupabaseConfig } from "@/lib/supabase/config";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const supabaseConfigured = hasSupabaseConfig();

  async function authenticate(mode: "login" | "signup") {
    setLoading(true);
    setMessage("");

    if (!supabaseConfigured) {
      setMessage("尚未設定 Supabase URL 與 publishable key。");
      setLoading(false);
      return;
    }

    const supabase = createClient();
    const result =
      mode === "login"
        ? await supabase.auth.signInWithPassword({ email, password })
        : await supabase.auth.signUp({
            email,
            password,
            options: { emailRedirectTo: `${window.location.origin}/auth/callback` },
          });

    setLoading(false);

    if (result.error) {
      setMessage(result.error.message);
      return;
    }

    if (mode === "signup" && !result.data.session) {
      setMessage("帳戶已建立，請先到信箱完成驗證。");
      return;
    }

    router.replace("/dashboard");
    router.refresh();
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await authenticate("login");
  }

  return (
    <main className="login-screen">
      <section className="login-panel">
        <div>
          <span className="brand-mark">AR</span>
          <h1>Atlas Research</h1>
          <p>登入後建立 AI 股票研究任務，所有報告與用量只屬於你的帳戶。</p>
        </div>
        <form className="login-form" onSubmit={submit}>
          <label>
            <span>Email</span>
            <input
              autoComplete="email"
              onChange={(event) => setEmail(event.target.value)}
              required
              type="email"
              value={email}
            />
          </label>
          <label>
            <span>密碼</span>
            <input
              autoComplete="current-password"
              minLength={8}
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
            />
          </label>
          {!supabaseConfigured ? (
            <p className="form-message">尚未設定 Supabase URL 與 publishable key。</p>
          ) : null}
          {message ? <p className="form-message">{message}</p> : null}
          <div className="login-actions">
            <button className="primary-action" disabled={loading || !supabaseConfigured} type="submit">
              {loading ? "處理中" : "登入"}
            </button>
            <button
              className="secondary-action"
              disabled={loading || !supabaseConfigured}
              onClick={() => authenticate("signup")}
              type="button"
            >
              建立帳戶
            </button>
          </div>
        </form>
        <p className="disclaimer">本服務僅供研究用途，不構成投資建議或交易建議。</p>
      </section>
    </main>
  );
}
