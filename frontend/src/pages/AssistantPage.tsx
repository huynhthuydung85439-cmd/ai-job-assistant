import { useState, type FormEvent } from "react";

import { chat } from "../api";
import { Icon } from "../components/Icon";
import type { Message, ToastState, UserSession } from "../types";

const suggestions = ["帮我分析一个 Python 后端岗位", "如何回答职业规划问题？", "给我一份面试自我介绍框架"];

interface AssistantPageProps {
  session: UserSession | null;
  notify: (toast: ToastState) => void;
}

export function AssistantPage({ session, notify }: AssistantPageProps) {
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { id: "welcome", role: "assistant", content: "你好，我是你的 AI 求职助手。可以把岗位描述、面试问题或职业困惑交给我，我们一起把问题拆清楚。" },
  ]);

  async function submitMessage(event?: FormEvent, preset?: string) {
    event?.preventDefault();
    const content = (preset ?? input).trim();
    if (!content || busy) return;
    setInput("");
    setMessages((current) => [...current, { id: crypto.randomUUID(), role: "user", content }]);
    setBusy(true);
    try {
      const response = await chat(content, session?.token);
      setMessages((current) => [...current, { id: crypto.randomUUID(), role: "assistant", content: response.answer }]);
    } catch (error) {
      notify({ type: "error", message: error instanceof Error ? error.message : "AI 暂时无法回答" });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="assistant-page">
      <section className="chat-shell">
        <header className="chat-header"><div><span className="assistant-avatar"><Icon name="sparkles" /></span><span><h1>AI 求职助手</h1><p><i className="online-dot" /> DeepSeek 在线 · {session ? "对话会自动保存" : "访客对话"}</p></span></div><span className="model-pill"><Icon name="sparkles" size={14}/> DeepSeek Chat</span></header>
        <div className="message-list">
          {messages.map((message) => (
            <div className={`message-row ${message.role}`} key={message.id}>
              {message.role === "assistant" && <span className="message-avatar"><Icon name="sparkles" size={17} /></span>}
              <div className="message-bubble"><p>{message.content}</p>{message.role === "assistant" && <small>AI 生成内容仅供求职准备参考</small>}</div>
              {message.role === "user" && <span className="message-avatar user"><Icon name="user" size={17} /></span>}
            </div>
          ))}
          {busy && <div className="message-row assistant"><span className="message-avatar"><Icon name="sparkles" size={17} /></span><div className="message-bubble typing"><i/><i/><i/></div></div>}
        </div>
        {messages.length === 1 && <div className="suggestion-row">{suggestions.map((item) => <button key={item} onClick={() => void submitMessage(undefined, item)}><Icon name="sparkles" size={14}/>{item}</button>)}</div>}
        <form className="chat-composer" onSubmit={submitMessage}><textarea value={input} onChange={(event) => setInput(event.target.value)} placeholder="输入你的求职问题…" rows={1} maxLength={10000} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void submitMessage(); } }}/><div className="composer-bottom"><span><kbd>Enter</kbd> 发送 · <kbd>Shift Enter</kbd> 换行</span><button className="send-button" disabled={!input.trim() || busy} aria-label="发送"><Icon name="send" size={18}/></button></div></form>
      </section>
      <aside className="chat-context">
        <div><p className="eyebrow">AI PLAYBOOK</p><h2>让提问更有效</h2><p className="muted">提供具体岗位、个人经历和目标，AI 才能给出更有针对性的回答。</p></div>
        <div className="prompt-tip"><span>01</span><div><strong>补充上下文</strong><p>岗位名称、行业和工作年限</p></div></div>
        <div className="prompt-tip"><span>02</span><div><strong>说明输出目标</strong><p>例如分析、改写或模拟追问</p></div></div>
        <div className="prompt-tip"><span>03</span><div><strong>持续迭代</strong><p>让 AI 基于上一轮继续优化</p></div></div>
        <div className="context-note"><Icon name="shield" size={18}/><div><strong>隐私提醒</strong><p>请避免在对话中发送身份证号、住址等敏感个人信息。</p></div></div>
      </aside>
    </div>
  );
}
