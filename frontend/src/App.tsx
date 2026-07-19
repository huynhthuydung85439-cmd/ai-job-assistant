import { useEffect, useState } from "react";

import { getCurrentUser } from "./api";
import { AuthModal } from "./components/AuthModal";
import { Layout } from "./components/Layout";
import { Toast } from "./components/Toast";
import { AssistantPage } from "./pages/AssistantPage";
import { DashboardPage } from "./pages/DashboardPage";
import { HistoryPage } from "./pages/HistoryPage";
import { KnowledgePage } from "./pages/KnowledgePage";
import { ResumePage } from "./pages/ResumePage";
import type { ToastState, UserSession, View } from "./types";

const SESSION_KEY = "aicareer.session";
const routeByView: Record<View, string> = {
  dashboard: "/",
  resume: "/resume",
  assistant: "/chat",
  knowledge: "/knowledge",
  history: "/history",
};

function viewFromPath(pathname: string): View {
  const matched = Object.entries(routeByView).find(([, path]) => path === pathname);
  return (matched?.[0] as View | undefined) ?? "dashboard";
}

function readSession(): UserSession | null {
  try {
    const value = localStorage.getItem(SESSION_KEY);
    return value ? (JSON.parse(value) as UserSession) : null;
  } catch {
    return null;
  }
}

export default function App() {
  const [view, setView] = useState<View>(() => viewFromPath(window.location.pathname));
  const [session, setSession] = useState<UserSession | null>(readSession);
  const [sessionReady, setSessionReady] = useState(() => readSession() === null);
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem("aicareer.theme") === "dark");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [authOpen, setAuthOpen] = useState(false);
  const [toast, setToast] = useState<ToastState | null>(null);

  useEffect(() => {
    document.documentElement.dataset.theme = darkMode ? "dark" : "light";
    localStorage.setItem("aicareer.theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(null), 3200);
    return () => window.clearTimeout(timer);
  }, [toast]);

  useEffect(() => {
    const handlePopState = () => setView(viewFromPath(window.location.pathname));
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  useEffect(() => {
    if (!session) {
      setSessionReady(true);
      return;
    }
    let cancelled = false;
    setSessionReady(false);
    void getCurrentUser(session.token)
      .then((user) => {
        if (cancelled) return;
        const verified = { token: session.token, userId: user.id, username: user.username };
        localStorage.setItem(SESSION_KEY, JSON.stringify(verified));
        setSession(verified);
      })
      .catch(() => {
        if (cancelled) return;
        localStorage.removeItem(SESSION_KEY);
        setSession(null);
      })
      .finally(() => {
        if (!cancelled) setSessionReady(true);
      });
    return () => {
      cancelled = true;
    };
  }, [session?.token]);

  function navigate(nextView: View) {
    const path = routeByView[nextView];
    if (window.location.pathname !== path) window.history.pushState({}, "", path);
    setView(nextView);
  }

  function handleAuthenticated(nextSession: UserSession) {
    localStorage.setItem(SESSION_KEY, JSON.stringify(nextSession));
    setSession(nextSession);
    setAuthOpen(false);
    setToast({ type: "success", message: `欢迎回来，${nextSession.username}` });
  }

  function handleLogout() {
    localStorage.removeItem(SESSION_KEY);
    setSession(null);
    setToast({ type: "success", message: "已安全退出登录" });
  }

  if (!sessionReady) {
    return <div className="app-loading"><span className="spinner large"/><strong>正在恢复登录状态…</strong><p>页面位置会保持不变</p></div>;
  }

  return (
    <>
      <Layout
        currentView={view}
        onNavigate={navigate}
        darkMode={darkMode}
        onToggleTheme={() => setDarkMode((current) => !current)}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen((current) => !current)}
        session={session}
        onOpenAuth={() => setAuthOpen(true)}
        onLogout={handleLogout}
      >
        {view === "dashboard" && <DashboardPage username={session?.username} onNavigate={navigate} />}
        {view === "resume" && <ResumePage session={session} notify={setToast} onRequireAuth={() => setAuthOpen(true)} />}
        {view === "assistant" && <AssistantPage session={session} notify={setToast} />}
        {view === "knowledge" && <KnowledgePage session={session} notify={setToast} onRequireAuth={() => setAuthOpen(true)} />}
        {view === "history" && <HistoryPage session={session} notify={setToast} onRequireAuth={() => setAuthOpen(true)} />}
      </Layout>
      {authOpen && <AuthModal onClose={() => setAuthOpen(false)} onAuthenticated={handleAuthenticated} />}
      {toast && <Toast toast={toast} />}
    </>
  );
}
