import type { View } from "../types";
import { Icon, type IconName } from "../components/Icon";

interface DashboardPageProps {
  username?: string;
  onNavigate: (view: View) => void;
}

const capabilities: Array<{
  icon: IconName;
  title: string;
  description: string;
  view: View;
  color: string;
  badge: string;
}> = [
  { icon: "resume", title: "简历智能分析", description: "对照岗位 JD 识别优势、技能差距与改进方向。", view: "resume", color: "violet", badge: "DeepSeek" },
  { icon: "chat", title: "AI 求职助手", description: "随时咨询岗位、面试、职业规划与表达策略。", view: "assistant", color: "blue", badge: "实时对话" },
  { icon: "knowledge", title: "求职知识库", description: "上传 JD 和面试资料，获得有来源的准确回答。", view: "knowledge", color: "mint", badge: "RAG" },
];

export function DashboardPage({ username, onNavigate }: DashboardPageProps) {
  const today = new Intl.DateTimeFormat("zh-CN", { month: "long", day: "numeric", weekday: "long" }).format(new Date());

  return (
    <div className="dashboard-page page-stack">
      <section className="welcome-row">
        <div>
          <p className="eyebrow">{today}</p>
          <h1>{username ? `你好，${username}` : "开始准备下一次机会"} <span className="wave">👋</span></h1>
          <p className="page-subtitle">把繁琐的求职准备交给 AI，专注展示你真正的价值。</p>
        </div>
        <button className="primary-button" onClick={() => onNavigate("resume")}><Icon name="sparkles" size={18} />开始一次简历分析</button>
      </section>

      <section className="hero-card">
        <div className="hero-copy">
          <span className="pill light"><Icon name="sparkles" size={14} /> AI CAREER COPILOT</span>
          <h2>从一份简历，到更好的职业选择。</h2>
          <p>上传简历与目标岗位，我们会拆解匹配度、发现关键差距，并为下一场面试生成专属问题。</p>
          <div className="hero-actions">
            <button className="hero-primary" onClick={() => onNavigate("resume")}>上传简历 <Icon name="arrow" size={17} /></button>
            <button className="hero-secondary" onClick={() => onNavigate("assistant")}>先问问 AI</button>
          </div>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="orbit orbit-one" />
          <div className="orbit orbit-two" />
          <div className="hero-document">
            <div className="doc-top"><span /><span /></div>
            <div className="doc-profile"><div className="doc-avatar" /><div><i /><i /></div></div>
            <div className="doc-line wide" /><div className="doc-line" /><div className="doc-line medium" />
            <div className="score-float"><span>匹配度</span><strong>88%</strong><small>↑ 12%</small></div>
            <div className="ai-float"><Icon name="sparkles" size={16} /> 5 条优化建议</div>
          </div>
        </div>
      </section>

      <section className="metric-grid">
        <article className="metric-card"><span className="metric-icon violet"><Icon name="briefcase" /></span><div><small>可用核心能力</small><strong>5</strong><em>全部服务正常</em></div><span className="trend positive">100%</span></article>
        <article className="metric-card"><span className="metric-icon blue"><Icon name="target" /></span><div><small>分析维度</small><strong>5</strong><em>技能、建议与面试</em></div><span className="trend">结构化</span></article>
        <article className="metric-card"><span className="metric-icon mint"><Icon name="database" /></span><div><small>知识来源</small><strong>PDF</strong><em>Chroma 向量检索</em></div><span className="trend positive">RAG</span></article>
        <article className="metric-card"><span className="metric-icon amber"><Icon name="shield" /></span><div><small>账户安全</small><strong>JWT</strong><em>bcrypt 密码加密</em></div><span className="trend">已保护</span></article>
      </section>

      <section>
        <div className="section-heading"><div><p className="eyebrow">SMART WORKSPACE</p><h2>你今天想完成什么？</h2></div><span className="muted">选择一个 AI 工作流开始</span></div>
        <div className="capability-grid">
          {capabilities.map((item) => (
            <button className="capability-card" key={item.title} onClick={() => onNavigate(item.view)}>
              <div className="capability-top"><span className={`feature-icon ${item.color}`}><Icon name={item.icon} /></span><span className="pill">{item.badge}</span></div>
              <h3>{item.title}</h3><p>{item.description}</p>
              <span className="card-link">打开工作台 <Icon name="arrow" size={16} /></span>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
