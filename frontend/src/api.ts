import type {
  AnalysisHistoryDetail,
  AnalysisHistoryItem,
  ChatHistoryItem,
  KnowledgeUploadResult,
  PageResult,
  ResumeAnalysisResult,
  ResumeHistoryItem,
  ResumeUploadResult,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

interface ApiErrorPayload {
  detail?: string;
  code?: string;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    let message = `请求失败（${response.status}）`;
    try {
      const payload = (await response.json()) as ApiErrorPayload;
      message = payload.detail || message;
    } catch {
      // Preserve the HTTP status fallback when the server did not return JSON.
    }
    throw new Error(message);
  }
  return (await response.json()) as T;
}

export async function registerUser(payload: {
  username: string;
  email: string;
  password: string;
}) {
  return request<{ id: number; username: string; email: string }>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function loginUser(payload: { username: string; password: string }) {
  return request<{ token: string; user_id: number }>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getCurrentUser(token: string) {
  return request<{ id: number; username: string; email: string }>(
    "/auth/me",
    { method: "GET" },
    token,
  );
}

export async function uploadResume(file: File, token?: string) {
  const body = new FormData();
  body.append("file", file);
  return request<ResumeUploadResult>("/resume/upload", { method: "POST", body }, token);
}

export async function analyzeResume(
  payload: { resume_text: string; job_description: string; resume_id?: number },
  token?: string,
) {
  return request<ResumeAnalysisResult>(
    "/resume/analyze",
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
}

export async function chat(message: string, token?: string) {
  return request<{ answer: string }>(
    "/chat",
    { method: "POST", body: JSON.stringify({ message }) },
    token,
  );
}

export async function uploadKnowledge(file: File, token?: string) {
  const body = new FormData();
  body.append("file", file);
  return request<KnowledgeUploadResult>(
    "/knowledge/upload",
    { method: "POST", body },
    token,
  );
}

export async function knowledgeChat(question: string, token?: string) {
  return request<{ answer: string; sources: string[] }>(
    "/knowledge/chat",
    { method: "POST", body: JSON.stringify({ question }) },
    token,
  );
}

export async function listKnowledgeDocuments(
  token: string,
  page = 1,
  pageSize = 100,
) {
  return request<PageResult<KnowledgeUploadResult>>(
    `/knowledge/documents?page=${page}&page_size=${pageSize}`,
    { method: "GET" },
    token,
  );
}

export async function warmupKnowledge(token: string) {
  return request<{ status: string; model: string }>(
    "/knowledge/warmup",
    { method: "POST" },
    token,
  );
}

export async function deleteKnowledgeDocument(documentId: string, token: string) {
  return request<{ document_id: string; deleted: boolean }>(
    `/knowledge/documents/${encodeURIComponent(documentId)}`,
    { method: "DELETE" },
    token,
  );
}

export async function listResumeHistory(token: string, page: number, pageSize = 10) {
  return request<PageResult<ResumeHistoryItem>>(
    `/history/resumes?page=${page}&page_size=${pageSize}`,
    { method: "GET" },
    token,
  );
}

export async function listAnalysisHistory(token: string, page: number, pageSize = 10) {
  return request<PageResult<AnalysisHistoryItem>>(
    `/history/analyses?page=${page}&page_size=${pageSize}`,
    { method: "GET" },
    token,
  );
}

export async function getAnalysisHistoryDetail(analysisId: number, token: string) {
  return request<AnalysisHistoryDetail>(
    `/history/analyses/${analysisId}`,
    { method: "GET" },
    token,
  );
}

export async function listChatHistory(token: string, page: number, pageSize = 10) {
  return request<PageResult<ChatHistoryItem>>(
    `/history/chats?page=${page}&page_size=${pageSize}`,
    { method: "GET" },
    token,
  );
}

export async function listRagHistory(token: string, page: number, pageSize = 10) {
  return request<PageResult<ChatHistoryItem>>(
    `/history/rag-chats?page=${page}&page_size=${pageSize}`,
    { method: "GET" },
    token,
  );
}
