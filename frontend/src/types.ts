export type View = "dashboard" | "resume" | "assistant" | "knowledge" | "history";

export interface UserSession {
  token: string;
  userId: number;
  username: string;
}

export interface ResumeUploadResult {
  filename: string;
  text: string;
  pages: number;
  resume_id?: number;
}

export interface ResumeAnalysisResult {
  score: number;
  matching_skills: string[];
  missing_skills: string[];
  resume_advices: string[];
  interview_questions: string[];
}

export interface KnowledgeUploadResult {
  document_id: string;
  filename: string;
  pages: number;
  chunks: number;
  collection_name: string;
  uploaded_at: string;
}

export interface PageResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ResumeHistoryItem {
  id: number;
  filename: string;
  analysis_count: number;
  created_at: string;
}

export interface AnalysisHistoryItem {
  id: number;
  resume_id: number;
  resume_filename: string;
  score: number;
  job_title: string;
  job_description_preview: string;
  created_at: string;
}

export interface AnalysisHistoryDetail extends AnalysisHistoryItem {
  job_description: string | null;
  result: ResumeAnalysisResult;
}

export interface ChatHistoryItem {
  id: number;
  question: string;
  answer: string;
  sources: string[];
  created_at: string;
}

export interface Message {
  id: string;
  role: "assistant" | "user";
  content: string;
  sources?: string[];
}

export interface ToastState {
  type: "success" | "error";
  message: string;
}
