export type View = "dashboard" | "resume" | "assistant" | "knowledge";

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
