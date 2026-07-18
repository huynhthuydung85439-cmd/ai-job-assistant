import { useRef, useState, type ChangeEvent, type DragEvent } from "react";

import { analyzeResume, uploadResume } from "../api";
import { Icon } from "../components/Icon";
import type { ResumeAnalysisResult, ResumeUploadResult, ToastState, UserSession } from "../types";

interface ResumePageProps {
  session: UserSession | null;
  notify: (toast: ToastState) => void;
  onRequireAuth: () => void;
}

export function ResumePage({ session, notify, onRequireAuth }: ResumePageProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [upload, setUpload] = useState<ResumeUploadResult | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<ResumeAnalysisResult | null>(null);

  async function handleFile(file?: File) {
    if (!file) return;
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      notify({ type: "error", message: "请上传 PDF 格式的简历" });
      return;
    }
    setUploading(true);
    setResult(null);
    try {
      const data = await uploadResume(file, session?.token);
      setUpload(data);
      notify({ type: "success", message: session ? "简历已解析并保存" : "简历已解析（登录后可保存）" });
    } catch (error) {
      notify({ type: "error", message: error instanceof Error ? error.message : "简历上传失败" });
    } finally {
      setUploading(false);
    }
  }

  function handleInput(event: ChangeEvent<HTMLInputElement>) {
    void handleFile(event.target.files?.[0]);
    event.target.value = "";
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    void handleFile(event.dataTransfer.files[0]);
  }

  async function handleAnalyze() {
    if (!upload || !jobDescription.trim()) {
      notify({ type: "error", message: "请先上传简历并填写目标岗位 JD" });
      return;
    }
    setAnalyzing(true);
    try {
      const data = await analyzeResume(
        {
          resume_text: upload.text,
          job_description: jobDescription.trim(),
          ...(upload.resume_id ? { resume_id: upload.resume_id } : {}),
        },
        session?.token,
      );
      setResult(data);
      notify({ type: "success", message: "AI 简历分析已完成" });
    } catch (error) {
      notify({ type: "error", message: error instanceof Error ? error.message : "分析失败" });
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <div className="resume-page page-stack">
      <section className="page-heading-row">
        <div><p className="eyebrow">RESUME INTELLIGENCE</p><h1>简历智能分析</h1><p className="page-subtitle">让 AI 对照目标岗位，找到简历中最值得被看见的部分。</p></div>
        {!session && <button className="secondary-button" onClick={onRequireAuth}><Icon name="shield" size={17} />登录后保存分析记录</button>}
      </section>

      <section className="analysis-workspace">
        <div className="workspace-inputs">
          <article className="panel-card">
            <div className="panel-heading"><span className="step-number">1</span><div><h2>上传 PDF 简历</h2><p>系统会自动提取文本内容</p></div>{upload && <span className="status-badge success"><Icon name="check" size={14} />已解析</span>}</div>
            <input ref={inputRef} type="file" accept="application/pdf,.pdf" onChange={handleInput} hidden />
            <div
              className={`dropzone ${dragging ? "dragging" : ""} ${upload ? "has-file" : ""}`}
              onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              onClick={() => inputRef.current?.click()}
              role="button"
              tabIndex={0}
              onKeyDown={(event) => event.key === "Enter" && inputRef.current?.click()}
            >
              {uploading ? <><span className="spinner large" /><h3>正在解析简历…</h3><p>通常只需要几秒钟</p></> : upload ? <><span className="file-success"><Icon name="file" size={28} /></span><h3>{upload.filename}</h3><p>{upload.pages} 页 · 文本已提取{upload.resume_id ? ` · 记录 #${upload.resume_id}` : ""}</p><button className="text-button">更换文件</button></> : <><span className="upload-orb"><Icon name="upload" size={26} /></span><h3>拖放简历到这里</h3><p>或点击选择 PDF 文件，最大 10 MB</p><span className="browse-button">选择文件</span></>}
            </div>
          </article>

          <article className="panel-card">
            <div className="panel-heading"><span className="step-number">2</span><div><h2>粘贴目标岗位 JD</h2><p>信息越完整，匹配分析越准确</p></div><span className="character-count">{jobDescription.length} / 100,000</span></div>
            <textarea className="jd-editor" value={jobDescription} onChange={(event) => setJobDescription(event.target.value)} maxLength={100000} placeholder={"在这里粘贴岗位描述，例如：\n\n负责 AI 应用后端研发，熟悉 Python、FastAPI、LangChain…"} />
            <div className="editor-footer"><span><Icon name="briefcase" size={15} />支持中文和英文 JD</span><button className="text-button" onClick={() => setJobDescription("")}>清空</button></div>
          </article>

          <button className="primary-button analyze-button" onClick={handleAnalyze} disabled={analyzing || uploading}>
            {analyzing ? <span className="spinner" /> : <Icon name="sparkles" size={19} />}
            {analyzing ? "DeepSeek 正在分析…" : "开始 AI 匹配分析"}
          </button>
        </div>

        <div className="workspace-result">
          {!result ? (
            <article className="result-empty panel-card">
              <div className="empty-visual"><span className="radar-ring ring-one"/><span className="radar-ring ring-two"/><span className="radar-ring ring-three"/><Icon name="target" size={42} /></div>
              <h2>等待开始分析</h2><p>上传简历并填写岗位 JD 后，AI 将从五个维度生成结构化结果。</p>
              <ul><li><Icon name="check" size={15}/>岗位匹配评分</li><li><Icon name="check" size={15}/>技能优势与缺口</li><li><Icon name="check" size={15}/>简历优化建议</li><li><Icon name="check" size={15}/>定制面试问题</li></ul>
            </article>
          ) : (
            <div className="result-stack">
              <article className="score-card panel-card"><div className="score-ring" style={{ "--score": `${result.score * 3.6}deg` } as React.CSSProperties}><div><strong>{result.score}</strong><span>/ 100</span></div></div><div><span className="pill success">综合匹配度</span><h2>{result.score >= 80 ? "匹配表现很不错" : result.score >= 60 ? "具备一定匹配度" : "还有明显提升空间"}</h2><p>结合岗位要求与简历证据计算，建议优先补齐缺失技能。</p></div></article>
              <article className="result-card panel-card"><div className="result-title"><span className="feature-icon mint"><Icon name="check" /></span><div><h3>匹配技能</h3><p>简历中已有充分证据</p></div></div><div className="skill-cloud">{result.matching_skills.length ? result.matching_skills.map((skill) => <span className="skill-chip matched" key={skill}>{skill}</span>) : <span className="muted">暂无明确匹配技能</span>}</div></article>
              <article className="result-card panel-card"><div className="result-title"><span className="feature-icon amber"><Icon name="target" /></span><div><h3>待补充技能</h3><p>岗位需要但简历证据不足</p></div></div><div className="skill-cloud">{result.missing_skills.length ? result.missing_skills.map((skill) => <span className="skill-chip missing" key={skill}>{skill}</span>) : <span className="muted">没有发现明显技能缺口</span>}</div></article>
              <ResultList title="简历优化建议" icon="sparkles" items={result.resume_advices} />
              <ResultList title="模拟面试问题" icon="chat" items={result.interview_questions} numbered />
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

function ResultList({ title, icon, items, numbered = false }: { title: string; icon: "sparkles" | "chat"; items: string[]; numbered?: boolean }) {
  return <article className="result-card panel-card"><div className="result-title"><span className="feature-icon violet"><Icon name={icon} /></span><div><h3>{title}</h3><p>由 DeepSeek 根据本次匹配生成</p></div></div><ol className={`advice-list ${numbered ? "numbered" : ""}`}>{items.map((item, index) => <li key={`${index}-${item}`}><span>{numbered ? index + 1 : <Icon name="arrow" size={14} />}</span><p>{item}</p></li>)}</ol></article>;
}
