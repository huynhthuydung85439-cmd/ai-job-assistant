import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react";

import { knowledgeChat, listKnowledgeDocuments, uploadKnowledge, warmupKnowledge } from "../api";
import { Icon } from "../components/Icon";
import type { KnowledgeUploadResult, Message, ToastState, UserSession } from "../types";

interface KnowledgePageProps {
  session: UserSession | null;
  notify: (toast: ToastState) => void;
  onRequireAuth: () => void;
}

export function KnowledgePage({ session, notify, onRequireAuth }: KnowledgePageProps) {
  const fileInput = useRef<HTMLInputElement>(null);
  const warmupToken = useRef<string | null>(null);
  const [documents, setDocuments] = useState<KnowledgeUploadResult[]>([]);
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const [warmupState, setWarmupState] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const [uploading, setUploading] = useState(false);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);

  useEffect(() => {
    if (!session) {
      setDocuments([]);
      setWarmupState("idle");
      warmupToken.current = null;
      return;
    }
    let cancelled = false;
    setLoadingDocuments(true);
    void listKnowledgeDocuments(session.token)
      .then((result) => {
        if (!cancelled) setDocuments(result.items);
      })
      .catch((error) => {
        if (!cancelled) notify({ type: "error", message: error instanceof Error ? error.message : "资料列表加载失败" });
      })
      .finally(() => {
        if (!cancelled) setLoadingDocuments(false);
      });

    if (warmupToken.current !== session.token) {
      warmupToken.current = session.token;
      setWarmupState("loading");
      void warmupKnowledge(session.token)
        .then(() => setWarmupState("ready"))
        .catch((error) => {
          setWarmupState("error");
          notify({ type: "error", message: error instanceof Error ? error.message : "Embedding 模型预热失败" });
        });
    }
    return () => {
      cancelled = true;
    };
  }, [notify, session]);

  async function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setUploading(true);
    try {
      const result = await uploadKnowledge(file, session?.token);
      setDocuments((current) => [result, ...current.filter((item) => item.document_id !== result.document_id)]);
      notify({ type: "success", message: `${result.filename} 已加入知识库` });
    } catch (error) {
      notify({ type: "error", message: error instanceof Error ? error.message : "资料上传失败" });
    } finally {
      setUploading(false);
    }
  }

  async function handleAsk(event: FormEvent) {
    event.preventDefault();
    const content = question.trim();
    if (!content || busy) return;
    setQuestion("");
    setMessages((current) => [...current, { id: crypto.randomUUID(), role: "user", content }]);
    setBusy(true);
    try {
      const result = await knowledgeChat(content, session?.token);
      setMessages((current) => [...current, { id: crypto.randomUUID(), role: "assistant", content: result.answer, sources: result.sources }]);
    } catch (error) {
      notify({ type: "error", message: error instanceof Error ? error.message : "知识库问答失败" });
    } finally {
      setBusy(false);
    }
  }

  if (!session) {
    return (
      <div className="knowledge-page page-stack">
        <section className="page-heading-row"><div><p className="eyebrow">KNOWLEDGE HUB</p><h1>求职知识库</h1><p className="page-subtitle">上传岗位 JD 与面试资料，让回答有据可查。</p></div></section>
        <article className="panel-card auth-required-card"><span className="feature-icon violet"><Icon name="shield" /></span><h2>登录后使用个人知识库</h2><p>文档和向量检索均按 JWT 用户隔离。</p><button className="primary-button" onClick={onRequireAuth}>登录 / 注册</button></article>
      </div>
    );
  }

  return (
    <div className="knowledge-page page-stack">
      <section className="page-heading-row"><div><p className="eyebrow">KNOWLEDGE HUB</p><h1>求职知识库</h1><p className="page-subtitle">上传岗位 JD 与面试资料，让回答有据可查。</p></div><button className="primary-button" onClick={() => fileInput.current?.click()} disabled={uploading || warmupState === "loading"}>{uploading || warmupState === "loading" ? <span className="spinner"/> : <Icon name="upload" size={18}/>}上传 PDF 资料</button><input ref={fileInput} hidden type="file" accept="application/pdf,.pdf" onChange={handleFile}/></section>

      {warmupState === "loading" && <div className="embedding-notice"><span className="spinner"/><div><strong>首次加载 Embedding 模型</strong><p>正在准备本地多语言检索模型，首次启动可能需要 1–2 分钟；完成后本次服务进程会复用同一模型。</p></div></div>}
      {warmupState === "error" && <div className="embedding-notice error"><Icon name="shield"/><div><strong>Embedding 模型尚未就绪</strong><p>请检查模型缓存或网络后重试进入知识库。</p></div></div>}

      <section className="knowledge-grid">
        <article className="library-panel panel-card">
          <div className="panel-heading"><span className="feature-icon violet"><Icon name="database"/></span><div><h2>资料库</h2><p>{documents.length ? `已保存 ${documents.length} 份资料` : "等待上传资料"}</p></div></div>
          {loadingDocuments ? <div className="library-empty"><span className="spinner large"/><h3>正在读取资料列表…</h3></div> : !documents.length ? <div className="library-empty"><span className="empty-folder"><Icon name="knowledge" size={30}/></span><h3>还没有资料</h3><p>上传招聘 JD、面试题库或行业资料，系统会自动切割并生成向量。</p><button className="secondary-button" onClick={() => fileInput.current?.click()} disabled={warmupState === "loading"}><Icon name="upload" size={16}/>选择 PDF</button></div> : <div className="document-list">{documents.map((document) => <div className="document-item" key={document.document_id}><span className="pdf-icon">PDF</span><div><strong>{document.filename}</strong><p>{document.pages} 页 · {document.chunks} 个知识片段 · {new Date(document.uploaded_at).toLocaleDateString("zh-CN")}</p></div><span className="status-badge success"><Icon name="check" size={13}/>就绪</span></div>)}</div>}
          <div className="library-stats"><div><strong>{documents.reduce((sum, item) => sum + item.pages, 0)}</strong><span>总页数</span></div><div><strong>{documents.reduce((sum, item) => sum + item.chunks, 0)}</strong><span>知识片段</span></div><div><strong>Chroma</strong><span>向量引擎</span></div></div>
        </article>

        <article className="knowledge-chat panel-card">
          <header><div><span className="assistant-avatar"><Icon name="sparkles"/></span><span><h2>基于资料问答</h2><p><i className="online-dot"/> RAG 检索已启用</p></span></div><span className="model-pill"><Icon name="knowledge" size={14}/>引用来源</span></header>
          <div className="knowledge-messages">
            {!messages.length && <div className="knowledge-welcome"><div className="empty-visual small"><Icon name="knowledge" size={32}/></div><h3>从你的资料中寻找答案</h3><p>例如：“这个岗位最看重哪些技能？”或“面试需要准备哪些项目案例？”</p></div>}
            {messages.map((message) => <div className={`message-row ${message.role}`} key={message.id}>{message.role === "assistant" && <span className="message-avatar"><Icon name="sparkles" size={16}/></span>}<div className="message-bubble"><p>{message.content}</p>{message.sources && message.sources.length > 0 && <div className="source-list"><span>参考来源</span>{message.sources.map((source) => <em key={source}><Icon name="file" size={13}/>{source}</em>)}</div>}</div></div>)}
            {busy && <div className="message-row assistant"><span className="message-avatar"><Icon name="sparkles" size={16}/></span><div className="message-bubble typing"><i/><i/><i/></div></div>}
          </div>
          <form className="knowledge-composer" onSubmit={handleAsk}><div className="input-with-icon"><Icon name="search" size={18}/><input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder={warmupState === "loading" ? "Embedding 模型首次加载中…" : "针对已上传资料提问…"} maxLength={10000} disabled={warmupState !== "ready"}/><button className="send-button" disabled={!question.trim() || busy || warmupState !== "ready"} aria-label="提问"><Icon name="send" size={17}/></button></div><small>AI 会优先基于检索到的资料回答，并返回来源文件。</small></form>
        </article>
      </section>
    </div>
  );
}
