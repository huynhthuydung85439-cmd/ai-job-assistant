import type { ReactNode } from "react";

import type { UserSession, View } from "../types";
import { Icon, type IconName } from "./Icon";

const navigation: Array<{ id: View; label: string; description: string; icon: IconName }> = [
  { id: "dashboard", label: "工作台", description: "求职进度概览", icon: "home" },
  { id: "resume", label: "简历分析", description: "上传与岗位匹配", icon: "resume" },
  { id: "assistant", label: "AI 助手", description: "求职问题咨询", icon: "chat" },
  { id: "knowledge", label: "知识库", description: "资料检索问答", icon: "knowledge" },
  { id: "history", label: "历史记录", description: "简历与对话回顾", icon: "clock" },
];

interface LayoutProps {
  children: ReactNode;
  currentView: View;
  onNavigate: (view: View) => void;
  darkMode: boolean;
  onToggleTheme: () => void;
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
  session: UserSession | null;
  onOpenAuth: () => void;
  onLogout: () => void;
}

export function Layout({
  children,
  currentView,
  onNavigate,
  darkMode,
  onToggleTheme,
  sidebarOpen,
  onToggleSidebar,
  session,
  onOpenAuth,
  onLogout,
}: LayoutProps) {
  const active = navigation.find((item) => item.id === currentView) ?? navigation[0];

  return (
    <div className={`app-shell ${sidebarOpen ? "sidebar-open" : ""}`}>
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark"><Icon name="sparkles" size={21} /></span>
          <span><strong>AiCareer</strong><small>智能求职工作台</small></span>
        </div>

        <div className="sidebar-section-label">工作空间</div>
        <nav className="nav-list" aria-label="主导航">
          {navigation.map((item) => (
            <button
              className={`nav-item ${currentView === item.id ? "active" : ""}`}
              key={item.id}
              onClick={() => {
                onNavigate(item.id);
                if (window.innerWidth < 960) onToggleSidebar();
              }}
            >
              <span className="nav-icon"><Icon name={item.icon} /></span>
              <span><strong>{item.label}</strong><small>{item.description}</small></span>
            </button>
          ))}
        </nav>

        <div className="sidebar-spacer" />
        <div className="upgrade-card">
          <span className="upgrade-icon"><Icon name="sparkles" /></span>
          <strong>让 AI 理解你的优势</strong>
          <p>上传简历和岗位 JD，获得更精准的求职建议。</p>
          <button onClick={() => onNavigate("resume")}>立即分析 <Icon name="arrow" size={15} /></button>
        </div>

        <div className="sidebar-profile">
          <span className="avatar">{session?.username.slice(0, 1).toUpperCase() || "访"}</span>
          <span><strong>{session?.username || "访客模式"}</strong><small>{session ? `用户 #${session.userId}` : "登录后保存记录"}</small></span>
          {session ? (
            <button className="icon-button" onClick={onLogout} title="退出登录"><Icon name="logout" size={18} /></button>
          ) : (
            <button className="text-button" onClick={onOpenAuth}>登录</button>
          )}
        </div>
      </aside>

      <div className="sidebar-backdrop" onClick={onToggleSidebar} />
      <section className="main-column">
        <header className="topbar">
          <div className="topbar-title">
            <button className="icon-button mobile-menu" onClick={onToggleSidebar}><Icon name="menu" /></button>
            <span><small>AiCareer /</small><strong>{active.label}</strong></span>
          </div>
          <div className="topbar-actions">
            <label className="global-search">
              <Icon name="search" size={18} />
              <input placeholder="搜索功能或输入快捷指令" aria-label="搜索" />
              <kbd>⌘ K</kbd>
            </label>
            <button className="icon-button" aria-label="通知"><Icon name="bell" /></button>
            <button className="icon-button" onClick={onToggleTheme} aria-label="切换主题">
              <Icon name={darkMode ? "sun" : "moon"} />
            </button>
            {!session && <button className="primary-button compact" onClick={onOpenAuth}>登录 / 注册</button>}
          </div>
        </header>
        <main className="page-content">{children}</main>
      </section>
    </div>
  );
}
