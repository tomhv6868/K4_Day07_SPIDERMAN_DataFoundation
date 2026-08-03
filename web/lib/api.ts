import type {
  AnswerSource,
  DocumentDetail,
  DocumentStats,
  DocumentSummary,
  Strategy,
  TraceStep,
} from "./types";

export interface ChatOptions {
  question: string;
  topK: number;
  strategy: Strategy;
  customerRole: string | null;
  onStep: (step: TraceStep) => void;
  onToken: (text: string) => void;
  onAnswer: (payload: { answer: string; sources: AnswerSource[]; totalMs: number }) => void;
  signal?: AbortSignal;
}

/**
 * Gọi /api/chat và đọc luồng SSE. Mỗi bước của pipeline RAG được backend đẩy
 * ra ngay khi chạy xong, nên UI hiển thị tiến trình thật chứ không phải mô phỏng.
 */
export async function streamChat(options: ChatOptions): Promise<void> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question: options.question,
      top_k: options.topK,
      strategy: options.strategy,
      customer_role: options.customerRole,
    }),
    signal: options.signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(`Backend trả về ${response.status}. Kiểm tra server FastAPI đã chạy chưa.`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const raw = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      boundary = buffer.indexOf("\n\n");

      let event = "message";
      const dataLines: string[] = [];
      for (const line of raw.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
      }
      if (!dataLines.length) continue;

      const payload = JSON.parse(dataLines.join("\n"));
      if (event === "step") {
        options.onStep(payload as TraceStep);
      } else if (event === "token") {
        options.onToken(payload.text as string);
      } else if (event === "answer") {
        options.onAnswer({
          answer: payload.answer,
          sources: payload.sources ?? [],
          totalMs: payload.total_ms ?? 0,
        });
      }
    }
  }
}

export async function fetchDocuments(
  strategy: Strategy,
): Promise<{ documents: DocumentSummary[]; stats: DocumentStats }> {
  const response = await fetch(`/api/documents?strategy=${strategy}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Không tải được danh sách tài liệu (${response.status}).`);
  }
  return response.json();
}

export async function fetchDocument(docId: string): Promise<DocumentDetail> {
  const response = await fetch(`/api/documents/${encodeURIComponent(docId)}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Không tải được tài liệu ${docId} (${response.status}).`);
  }
  return response.json();
}
