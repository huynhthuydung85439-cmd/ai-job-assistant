import { useState, type FormEvent } from "react";

import { loginUser, registerUser } from "../api";
import type { UserSession } from "../types";
import { Icon } from "./Icon";

interface AuthModalProps {
  onClose: () => void;
  onAuthenticated: (session: UserSession) => void;
}

export function AuthModal({ onClose, onAuthenticated }: AuthModalProps) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "register") {
        await registerUser({ username, email, password });
      }
      const result = await loginUser({ username, password });
      onAuthenticated({ token: result.token, userId: result.user_id, username });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "认证失败，请稍后重试");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="auth-modal" role="dialog" aria-modal="true" aria-labelledby="auth-title">
        <button className="icon-button modal-close" onClick={onClose} aria-label="关闭"><Icon name="close" /></button>
        <div className="auth-brand"><span className="brand-mark"><Icon name="sparkles" /></span></div>
        <p className="eyebrow">WELCOME TO AICAREER</p>
        <h2 id="auth-title">{mode === "login" ? "欢迎回来" : "创建你的求职空间"}</h2>
        <p className="muted">登录后自动保存简历、分析结果和 AI 对话历史。</p>

        <div className="auth-tabs">
          <button className={mode === "login" ? "active" : ""} onClick={() => { setMode("login"); setError(""); }}>登录</button>
          <button className={mode === "register" ? "active" : ""} onClick={() => { setMode("register"); setError(""); }}>注册</button>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <label><span>用户名</span><div className="input-with-icon"><Icon name="user" size={18} /><input value={username} onChange={(event) => setUsername(event.target.value)} minLength={3} required placeholder="例如：aicareer_user" /></div></label>
          {mode === "register" && <label><span>邮箱</span><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required placeholder="name@example.com" /></label>}
          <label><span>密码</span><input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={8} required placeholder="至少 8 位字符" /></label>
          {error && <div className="form-error">{error}</div>}
          <button className="primary-button auth-submit" disabled={busy}>
            {busy ? <span className="spinner" /> : <Icon name="shield" size={18} />}
            {busy ? "处理中…" : mode === "login" ? "安全登录" : "注册并登录"}
          </button>
        </form>
        <p className="auth-note"><Icon name="shield" size={14} /> 密码使用 bcrypt 加密，访问令牌通过 JWT 保护。</p>
      </section>
    </div>
  );
}
