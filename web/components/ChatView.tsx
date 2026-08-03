"use client";

import { useEffect, useRef, useState } from "react";
import { streamChat } from "@/lib/api";
import {
  ROLE_LABELS,
  STRATEGY_LABELS,
  type ChatMessage,
  type Strategy,
} from "@/lib/types";
import { LinkIcon, SendIcon } from "./Icons";
import { Logo } from "./Logo";
import { StepTrace } from "./StepTrace";

/** 5 benchmark query của nhóm (REPORT_NHOM.md) — bấm là chạy luôn. */
const SUGGESTIONS: { text: string; role: string | null }[] = [
  {
    text: "Nhà Bán có bao nhiêu thời gian để xác nhận phương án xử lý yêu cầu đổi trả bảo hành của khách hàng?",
    role: "seller",
  },
  { text: "Thời gian bảo hành mà Nhà Bán được cam kết tối đa là bao lâu, tính từ lúc nào?", role: null },
  { text: "Những loại hàng hóa nào Nhà Bán không được đăng bán trên sàn Tiki?", role: "seller" },
  { text: "Người tiêu dùng nên làm gì để phòng tránh rủi ro khi mua sắm trực tuyến?", role: "buyer" },
];

const ROLE_OPTIONS = ["", "buyer", "seller", "both"];

let counter = 0;
const nextId = () => `m${++counter}`;

export function ChatView() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [strategy, setStrategy] = useState<Strategy>("fixed_size");
  const [topK, setTopK] = useState(3);
  const [role, setRole] = useState("");
  const [busy, setBusy] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  function patch(id: string, update: (message: ChatMessage) => ChatMessage) {
    setMessages((list) => list.map((message) => (message.id === id ? update(message) : message)));
  }

  async function send(question: string, overrideRole?: string | null) {
    const trimmed = question.trim();
    if (!trimmed || busy) return;

    const effectiveRole = overrideRole === undefined ? role : (overrideRole ?? "");
    if (overrideRole !== undefined) setRole(effectiveRole);

    setBusy(true);
    setInput("");
    const replyId = nextId();
    setMessages((list) => [
      ...list,
      { id: nextId(), role: "user", content: trimmed, steps: [], sources: [], running: false },
      { id: replyId, role: "assistant", content: "", steps: [], sources: [], running: true },
    ]);

    try {
      await streamChat({
        question: trimmed,
        topK,
        strategy,
        customerRole: effectiveRole || null,
        onStep: (step) =>
          patch(replyId, (message) => ({ ...message, steps: [...message.steps, step] })),
        onToken: (text) =>
          patch(replyId, (message) => ({ ...message, content: message.content + text })),
        onAnswer: ({ sources, totalMs }) =>
          patch(replyId, (message) => ({ ...message, sources, totalMs, running: false })),
      });
    } catch (error) {
      patch(replyId, (message) => ({
        ...message,
        running: false,
        error: error instanceof Error ? error.message : "Lỗi không xác định.",
      }));
    } finally {
      setBusy(false);
      textareaRef.current?.focus();
    }
  }

  const empty = messages.length === 0;

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-3xl px-4 py-8">
          {empty ? (
            <div className="animate-rise pt-10 pb-6 text-center">
              <Logo size={56} className="mx-auto" />
              <h1 className="mt-5 text-2xl font-semibold tracking-tight text-ink-900">
                Hỏi về chính sách thương mại điện tử
              </h1>
              <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-ink-500">
                Câu trả lời chỉ lấy từ 10 tài liệu công khai trong kho. Mở phần tiến trình để xem
                đúng những chunk nào được truy xuất và điểm tương đồng bao nhiêu.
              </p>

              <div className="mt-8 grid gap-2 text-left sm:grid-cols-2">
                {SUGGESTIONS.map((item) => (
                  <button
                    key={item.text}
                    type="button"
                    onClick={() => send(item.text, item.role)}
                    className="group rounded-xl border border-line bg-surface p-3.5 text-left transition-all hover:border-brand-300 hover:shadow-sm"
                  >
                    <span className="block text-[13px] leading-relaxed text-ink-700 group-hover:text-ink-900">
                      {item.text}
                    </span>
                    {item.role ? (
                      <span className="mt-2 inline-block rounded bg-brand-50 px-1.5 py-0.5 text-[10px] font-medium text-brand-700">
                        lọc: {ROLE_LABELS[item.role]}
                      </span>
                    ) : null}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-7">
              {messages.map((message) =>
                message.role === "user" ? (
                  <div key={message.id} className="animate-rise flex justify-end">
                    <div className="max-w-[85%] rounded-2xl rounded-br-md bg-brand-600 px-4 py-2.5 text-[14px] leading-relaxed text-white">
                      {message.content}
                    </div>
                  </div>
                ) : (
                  <div key={message.id} className="animate-rise flex gap-3">
                    <Logo size={26} className="mt-0.5 shrink-0" />
                    <div className="min-w-0 flex-1">
                      {message.steps.length || message.running ? (
                        <StepTrace steps={message.steps} running={message.running} />
                      ) : null}

                      {message.error ? (
                        <div className="rounded-xl border border-accent-200 bg-accent-50 px-3.5 py-3 text-[13px] leading-relaxed text-accent-700">
                          {message.error}
                        </div>
                      ) : null}

                      {message.content ? (
                        <div className="text-[14px] leading-[1.75] whitespace-pre-wrap text-ink-900">
                          {message.content}
                          {message.running ? (
                            <span
                              className="animate-dot ml-0.5 inline-block h-[15px] w-[2px] translate-y-[2px] bg-brand-600"
                              aria-hidden="true"
                            />
                          ) : null}
                        </div>
                      ) : null}

                      {message.sources.length ? (
                        <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-line pt-3">
                          <span className="text-[11px] font-medium text-ink-500">Nguồn:</span>
                          {message.sources.map((source, index) => (
                            <a
                              key={`${source.doc_id}-${index}`}
                              href={source.source_url || undefined}
                              target="_blank"
                              rel="noreferrer noopener"
                              className="inline-flex items-center gap-1 rounded-full border border-line bg-surface px-2 py-0.5 font-mono text-[11px] text-ink-700 transition-colors hover:border-brand-300 hover:text-brand-700"
                            >
                              <LinkIcon className="h-3 w-3" />
                              {source.doc_id}
                            </a>
                          ))}
                          {message.totalMs ? (
                            <span className="ml-auto font-mono text-[11px] text-ink-300">
                              {message.totalMs.toFixed(0)} ms
                            </span>
                          ) : null}
                        </div>
                      ) : null}
                    </div>
                  </div>
                ),
              )}
            </div>
          )}
        </div>
      </div>

      <div className="border-t border-line bg-surface">
        <div className="mx-auto w-full max-w-3xl px-4 py-3.5">
          <div className="mb-2.5 flex flex-wrap items-center gap-2 text-[11px]">
            <label className="flex items-center gap-1.5 text-ink-500">
              Chiến lược
              <select
                value={strategy}
                onChange={(event) => setStrategy(event.target.value as Strategy)}
                className="rounded-md border border-line bg-surface px-2 py-1 text-[11px] text-ink-900 outline-none focus:border-brand-400"
              >
                {Object.entries(STRATEGY_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex items-center gap-1.5 text-ink-500">
              Lọc vai trò
              <select
                value={role}
                onChange={(event) => setRole(event.target.value)}
                className="rounded-md border border-line bg-surface px-2 py-1 text-[11px] text-ink-900 outline-none focus:border-brand-400"
              >
                {ROLE_OPTIONS.map((value) => (
                  <option key={value || "none"} value={value}>
                    {value ? ROLE_LABELS[value] : "Không lọc"}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex items-center gap-1.5 text-ink-500">
              top-k
              <input
                type="number"
                min={1}
                max={10}
                value={topK}
                onChange={(event) => setTopK(Math.min(10, Math.max(1, Number(event.target.value) || 1)))}
                className="w-14 rounded-md border border-line bg-surface px-2 py-1 text-[11px] text-ink-900 outline-none focus:border-brand-400"
              />
            </label>
          </div>

          <form
            onSubmit={(event) => {
              event.preventDefault();
              send(input);
            }}
            className="flex items-end gap-2 rounded-2xl border border-line bg-surface p-2 transition-colors focus-within:border-brand-400"
          >
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  send(input);
                }
              }}
              placeholder="Hỏi về đổi trả, hoàn tiền, quy định người bán…"
              className="max-h-40 min-h-[38px] flex-1 resize-none bg-transparent px-2 py-2 text-[14px] leading-relaxed text-ink-900 outline-none placeholder:text-ink-300"
            />
            <button
              type="submit"
              disabled={busy || !input.trim()}
              aria-label="Gửi câu hỏi"
              className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white transition-colors hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-ink-300"
            >
              <SendIcon />
            </button>
          </form>

          <p className="mt-2 text-center text-[11px] text-ink-300">
            Câu trả lời sinh bởi OpenAI, chỉ dựa trên ngữ cảnh truy xuất từ corpus. Mở phần tiến
            trình để đối chiếu với chunk gốc.
          </p>
        </div>
      </div>
    </div>
  );
}
