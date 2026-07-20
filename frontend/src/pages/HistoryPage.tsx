import { useEffect, useState } from "react";

import {
  getAnalysisHistoryDetail,
  listAnalysisHistory,
  listChatHistory,
  listRagHistory,
  listResumeHistory,
} from "../api";
import { Icon } from "../components/Icon";
import type {
  AnalysisHistoryDetail,
  AnalysisHistoryItem,
  ChatHistoryItem,
  ResumeHistoryItem,
  ToastState,
  UserSession,
} from "../types";

type HistoryTab = "resumes" | "analyses" | "chats" | "rag";
type HistoryItem = ResumeHistoryItem | AnalysisHistoryItem | ChatHistoryItem;

const tabs: Array<{ id: HistoryTab; label: string }> = [
  { id: "resumes", label: "简历列表" },
  { id: "analyses", label: "分析记录" },
  { id: "chats", label: "普通对话" },
  { id: "rag", label: "RAG 问答" },
];

interface HistoryPageProps {
  session: UserSession | null;
  notify: (toast: ToastState) => void;
  onRequireAuth: () => void;
}

export function HistoryPage({ session, notify, onRequireAuth }: HistoryPageProps) {
  const [activeTab, setActiveTab] = useState<HistoryTab>("resumes");
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [page, setPage] = useState(1);
  const [pageCount, setPageCount] = useState(0);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [detail, setDetail] = useState<AnalysisHistoryDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    if (!session) {
      setItems([]);
      setPageCount(0);
      setTotal(0);
      return;
    }
    let cancelled = false;
    setLoading(true);
    const request =
      activeTab === "resumes"
        ? listResumeHistory(session.token, page)
        : activeTab === "analyses"
          ? listAnalysisHistory(session.token, page)
          : activeTab === "chats"
            ? listChatHistory(session.token, page)
            : listRagHistory(session.token, page);
    void request
      .then((result) => {
        if (cancelled) return;
        setItems(result.items);
        setPageCount(result.pages);
        setTotal(result.total);
      })
      .catch((error) => {
        if (!cancelled) {
          notify({ type: "error", message: error instanceof Error ? error.message : "历史记录加载失败" });
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [activeTab, notify, page, session]);

  function changeTab(tab: HistoryTab) {
    setActiveTab(tab);
    setPage(1);
    setDetail(null);
  }

  async function openAnalysis(analysisId: number) {
    if (!session || detailLoading) return;
    setDetailLoading(true);
    try {
      setDetail(await getAnalysisHistoryDetail(analysisId, session.token));
    } catch (error) {
      notify({ type: "error", message: error instanceof Error ? error.message : "分析详情加载失败" });
    } finally {
      setDetailLoading(false);
    }
  }

  if (!session) {
    return (
      <div className="history-page page-stack">
        <section className="page-heading-row"><div><p className="eyebrow">YOUR ACTIVITY</p><h1>历史记录</h1><p className="page-subtitle">集中查看已保存的简历、分析和求职对话。</p></div></section>
        <article className="panel-card auth-required-card"><span className="feature-icon violet"><Icon name="shield" /></span><h2>登录后查看个人历史</h2><p>所有记录均通过 JWT 按用户隔离。</p><button className="primary-button" onClick={onRequireAuth}>登录 / 注册</button></article>
      </div>
    );
  }

  return (
    <div className="history-page page-stack">
      <section className="page-heading-row"><div><p className="eyebrow">YOUR ACTIVITY</p><h1>历史记录</h1><p className="page-subtitle">当前共找到 {total} 条{tabs.find((tab) => tab.id === activeTab)?.label}。</p></div></section>
      <section className="history-shell panel-card">
        <div className="history-tabs" role="tablist" aria-label="历史记录分类">
          {tabs.map((tab) => <button key={tab.id} role="tab" aria-selected={activeTab === tab.id} className={activeTab === tab.id ? "active" : ""} onClick={() => changeTab(tab.id)}>{tab.label}</button>)}
        </div>
        <div className="history-list">
          {loading ? <div className="history-loading"><span className="spinner large"/><p>正在读取历史数据…</p></div> : !items.length ? <div className="history-empty"><Icon name="clock" size={34}/><h3>暂无记录</h3><p>完成对应业务流程后，记录会自动保存在这里。</p></div> : items.map((item) => {
            if ("analysis_count" in item) {
              return <article className="history-item" key={`resume-${item.id}`}><span className="feature-icon violet"><Icon name="resume"/></span><div><h3>{item.filename}</h3><p>简历记录 #{item.id} · {item.analysis_count} 次分析</p></div><time>{formatTime(item.created_at)}</time></article>;
            }
            if ("score" in item) {
              return <button className="history-item history-analysis" key={`analysis-${item.id}`} onClick={() => void openAnalysis(item.id)} disabled={detailLoading}><span className="history-score">{item.score}</span><div><h3>{item.job_title}</h3><p>{item.resume_filename} · {item.job_description_preview}</p></div><time>{formatTime(item.created_at)}</time><Icon name="arrow" size={16}/></button>;
            }
            return <article className="history-item history-chat" key={`chat-${item.id}`}><span className="feature-icon mint"><Icon name={activeTab === "rag" ? "knowledge" : "chat"}/></span><div><h3>{item.question}</h3><p>{item.answer}</p>{item.sources.length > 0 && <div className="source-list">{item.sources.map((source) => <em key={source}><Icon name="file" size={12}/>{source}</em>)}</div>}</div><time>{formatTime(item.created_at)}</time></article>;
          })}
        </div>
        <div className="history-pagination"><button className="secondary-button" disabled={page <= 1 || loading} onClick={() => setPage((value) => value - 1)}>上一页</button><span>第 {page} 页 / 共 {Math.max(pageCount, 1)} 页</span><button className="secondary-button" disabled={pageCount === 0 || page >= pageCount || loading} onClick={() => setPage((value) => value + 1)}>下一页</button></div>
      </section>
      {detail && <AnalysisDetailModal detail={detail} onClose={() => setDetail(null)} />}
    </div>
  );
}

function AnalysisDetailModal({ detail, onClose }: { detail: AnalysisHistoryDetail; onClose: () => void }) {
  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="analysis-detail-modal" role="dialog" aria-modal="true" aria-labelledby="analysis-detail-title">
        <button className="icon-button modal-close" onClick={onClose} aria-label="关闭分析详情"><Icon name="close"/></button>
        <p className="eyebrow">ANALYSIS #{detail.id}</p><h2 id="analysis-detail-title">{detail.job_title}</h2><p className="muted">{detail.resume_filename} · {formatTime(detail.created_at)}</p>
        <div className="detail-score"><strong>{detail.score}</strong><span>/ 100 岗位匹配度</span></div>
        <section><h3>岗位信息</h3><p className="detail-job-description">{detail.job_description || detail.job_description_preview}</p></section>
        <DetailSkills title="匹配技能" items={detail.result.matching_skills} className="matched" />
        <DetailSkills title="待补充技能" items={detail.result.missing_skills} className="missing" />
        <DetailList title="简历修改建议" items={detail.result.resume_advices}/>
        <DetailList title="模拟面试问题" items={detail.result.interview_questions}/>
      </section>
    </div>
  );
}

function DetailSkills({ title, items, className }: { title: string; items: string[]; className: string }) {
  return <section><h3>{title}</h3><div className="skill-cloud">{items.map((item) => <span className={`skill-chip ${className}`} key={item}>{item}</span>)}</div></section>;
}

function DetailList({ title, items }: { title: string; items: string[] }) {
  return <section><h3>{title}</h3><ol className="detail-list">{items.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}</ol></section>;
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat("zh-CN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}
