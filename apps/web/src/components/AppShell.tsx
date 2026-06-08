import Link from "next/link";
import {
  BarChartIcon,
  CreditCardIcon,
  DashboardIcon,
  FileTextIcon,
  SettingsIcon,
  TelescopeIcon,
} from "./Icons";

const navItems = [
  { href: "/dashboard", label: "儀表板", icon: DashboardIcon },
  { href: "/reports", label: "研究報告", icon: FileTextIcon },
  { href: "/watchlist", label: "觀察清單", icon: TelescopeIcon },
  { href: "/billing", label: "帳單", icon: CreditCardIcon },
  { href: "/settings/api-usage", label: "API 用量", icon: BarChartIcon },
];

export function AppShell({
  active,
  title,
  description,
  userEmail,
  children,
}: {
  active: string;
  title: string;
  description: string;
  userEmail: string;
  children: React.ReactNode;
}) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand" href="/dashboard" aria-label="Atlas Research 儀表板">
          <span className="brand-mark">AR</span>
          <span>
            <strong>Atlas Research</strong>
            <small>AI 股票研究</small>
          </span>
        </Link>
        <nav aria-label="主要導覽">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                className={active === item.href ? "active" : ""}
                href={item.href}
              >
                <Icon size={18} aria-hidden="true" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="sidebar-footer">
          <SettingsIcon size={17} aria-hidden="true" />
          <span>僅供研究，不構成投資建議。</span>
        </div>
      </aside>
      <main className="workspace">
        <header className="topbar">
          <div>
            <h1>{title}</h1>
            <p>{description}</p>
          </div>
          <div className="user-chip">
            <span>已登入</span>
            <strong>{userEmail}</strong>
            <form action="/auth/signout" method="post">
              <button type="submit">登出</button>
            </form>
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
