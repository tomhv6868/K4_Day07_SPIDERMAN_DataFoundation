export type CustomerRole = "buyer" | "seller" | "both" | string;

export type Strategy = "fixed_size" | "by_sentences" | "recursive";

export const STRATEGY_LABELS: Record<Strategy, string> = {
  fixed_size: "FixedSize (500/50)",
  by_sentences: "Sentence (3 câu)",
  recursive: "Recursive (500)",
};

export const ROLE_LABELS: Record<string, string> = {
  buyer: "Người mua",
  seller: "Người bán",
  both: "Cả hai",
};

export interface RetrievedChunk {
  id: string;
  score: number;
  doc_id: string;
  customer_role: string;
  source_url: string;
  preview: string;
}

export interface TraceStep {
  id: string;
  label: string;
  detail: string;
  ms: number;
  results?: RetrievedChunk[];
}

export interface AnswerSource {
  doc_id: string;
  source_url: string;
  score: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  steps: TraceStep[];
  sources: AnswerSource[];
  totalMs?: number;
  running: boolean;
  error?: string;
}

export interface DocumentSummary {
  doc_id: string;
  title: string;
  customer_role: CustomerRole;
  category: string;
  language: string;
  source_url: string;
  retrieved_at: string;
  document_version: string;
  file_name: string;
  char_count: number;
  chunk_count: number;
}

export interface DocumentDetail extends Omit<DocumentSummary, "chunk_count"> {
  content: string;
}

export interface DocumentStats {
  total_documents: number;
  total_chunks: number;
  total_chars: number;
  roles: Record<string, number>;
  strategy: string;
}
