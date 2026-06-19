const NETWORK_AUTH_ERROR =
  "無法連線到登入服務，請稍後再試；如果問題持續，請確認 Supabase 專案已啟用。";

export function authErrorMessage(error) {
  const message = typeof error?.message === "string" ? error.message.trim() : "";

  if (!message) {
    return "登入失敗，請稍後再試。";
  }

  if (/failed to fetch|fetch failed|networkerror|load failed/i.test(message)) {
    return NETWORK_AUTH_ERROR;
  }

  return message;
}
