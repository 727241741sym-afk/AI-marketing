"use client";

import { useEffect, useState } from "react";
import { apiRequest, type WatchlistItem } from "@/lib/api";
import { normalizeTicker } from "@/lib/usage.mjs";
import { PlusIcon } from "./Icons";

export function WatchlistManager() {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [ticker, setTicker] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function refresh() {
    setItems(await apiRequest<WatchlistItem[]>("/api/watchlist"));
  }

  useEffect(() => {
    refresh()
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  async function addItem() {
    const normalizedTicker = normalizeTicker(ticker);
    if (!normalizedTicker || !companyName.trim() || adding) {
      return;
    }

    setAdding(true);
    setError("");
    try {
      await apiRequest<WatchlistItem>("/api/watchlist", {
        method: "POST",
        body: JSON.stringify({ ticker: normalizedTicker, companyName: companyName.trim() }),
      });
      setTicker("");
      setCompanyName("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "新增觀察標的失敗");
    } finally {
      setAdding(false);
    }
  }

  async function deleteItem(id: string) {
    if (deletingId) {
      return;
    }
    setDeletingId(id);
    setError("");
    try {
      await apiRequest<void>(`/api/watchlist/${id}`, { method: "DELETE" });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "刪除觀察標的失敗");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <section className="panel page-panel">
      <div className="panel-heading">
        <div>
          <h2>追蹤標的</h2>
          <p>觀察清單只用於研究排程，不會觸發任何交易行為。</p>
        </div>
      </div>
      <div className="watchlist-form">
        <input
          aria-label="股票代號"
          onChange={(event) => setTicker(event.target.value)}
          placeholder="Ticker"
          value={ticker}
        />
        <input
          aria-label="公司名稱"
          onChange={(event) => setCompanyName(event.target.value)}
          placeholder="公司名稱"
          value={companyName}
        />
        <button
          className="primary-action compact-action"
          disabled={adding}
          onClick={addItem}
          type="button"
        >
          <PlusIcon size={17} />
          {adding ? "新增中" : "新增標的"}
        </button>
      </div>
      {error ? <p className="form-message padded">{error}</p> : null}
      <div className="table-list">
        {loading ? <p className="empty-state">載入觀察清單中...</p> : null}
        {!loading && items.length === 0 ? <p className="empty-state">尚未加入標的。</p> : null}
        {items.map((item) => (
          <div className="table-row watchlist-row" key={item.id}>
            <strong>{item.ticker}</strong>
            <span>{item.companyName}</span>
            <span>下次研究：未排程</span>
            <button
              className="secondary-action"
              disabled={Boolean(deletingId)}
              onClick={() => deleteItem(item.id)}
              type="button"
            >
              {deletingId === item.id ? "移除中" : "移除"}
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}
