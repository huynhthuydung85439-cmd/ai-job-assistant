import { useEffect, useState } from "react";

import { AuthModal } from "./components/AuthModal";
import { Layout } from "./components/Layout";
import { Toast } from "./components/Toast";
import { AssistantPage } from "./pages/AssistantPage";
import { DashboardPage } from "./pages/DashboardPage";
import { KnowledgePage } from "./pages/KnowledgePage";
import { ResumePage } from "./pages/ResumePage";
import type { ToastState, UserSession, View } from "./types";

const SESSION_KEY = "aicareer.session";

function readSession(): UserSession | null {
  try {
    const value = localStorage.getItem(SESSION_KEY);
    return value ? (JSON.parse(value) as UserSession) : null;
  } catch {
    return null;
  }
}

export default function App() {
  const [view, setView] = useState<View>("dashboard");
  const [session, setSession] = useState<UserSession | null>(readSession);
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

  return (
    <>
      <Layout
        currentView={view}
        onNavigate={setView}
        darkMode={darkMode}
        onToggleTheme={() => setDarkMode((current) => !current)}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen((current) => !current)}
        session={session}
        onOpenAuth={() => setAuthOpen(true)}
        onLogout={handleLogout}
      >
        {view === "dashboard" && <DashboardPage username={session?.username} onNavigate={setView} />}
        {view === "resume" && <ResumePage session={session} notify={setToast} onRequireAuth={() => setAuthOpen(true)} />}
        {view === "assistant" && <AssistantPage session={session} notify={setToast} />}
        {view === "knowledge" && <KnowledgePage session={session} notify={setToast} />}
      </Layout>
      {authOpen && <AuthModal onClose={() => setAuthOpen(false)} onAuthenticated={handleAuthenticated} />}
      {toast && <Toast toast={toast} />}
    </>
  );
}
