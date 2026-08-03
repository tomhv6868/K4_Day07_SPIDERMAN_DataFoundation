"use client";

import { useState } from "react";
import { CheckIcon, ChevronDown, LinkIcon } from "./Icons";
import { ROLE_LABELS, type TraceStep } from "@/lib/types";

function RoleBadge({ role }: { role: string }) {
  if (!role) return null;
  const tone =
    role === "seller"
      ? "bg-accent-50 text-accent-700"
      : role === "buyer"
        ? "bg-brand-50 text-brand-700"
        : "bg-canvas text-ink-700";
  return (
    <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${tone}`}>
      {ROLE_LABELS[role] ?? role}
    </span>
  );
}

/**
 * Bảng tiến trình thu gọn — mũi tên bấm để mở, xem rõ từng bước pipeline RAG
 * đang chạy, mất bao lâu, và chunk nào được lấy về với điểm bao nhiêu.
 */
export function StepTrace({ steps, running }: { steps: TraceStep[]; running: boolean }) {
  const [open, setOpen] = useState(false);
  const current = steps.at(-1);
  const totalMs = steps.reduce((sum, step) => sum + step.ms, 0);

  const summary = running
    ? (current?.label ?? "Đang khởi động…")
    : `Đã chạy ${steps.length} bước · ${totalMs.toFixed(0)} ms`;

  return (
    <div className="mb-3 overflow-hidden rounded-xl border border-line bg-surface">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="flex w-full items-center gap-2.5 px-3.5 py-2.5 text-left transition-colors hover:bg-canvas"
      >
        {running ? (
          <span className="flex gap-0.5" aria-hidden="true">
            {[0, 1, 2].map((index) => (
              <span
                key={index}
                className="animate-dot h-1.5 w-1.5 rounded-full bg-brand-500"
                style={{ animationDelay: `${index * 0.16}s` }}
              />
            ))}
          </span>
        ) : (
          <CheckIcon className="h-3.5 w-3.5 text-brand-600" />
        )}

        <span className="min-w-0 flex-1 truncate text-[13px] font-medium text-ink-700">
          {summary}
        </span>

        <span className="text-[11px] text-ink-500">{open ? "Ẩn chi tiết" : "Xem chi tiết"}</span>
        <ChevronDown
          className={`text-ink-500 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open ? (
        <ol className="border-t border-line px-3.5 py-3">
          {steps.map((step, index) => (
            <li key={step.id} className="animate-rise relative pb-4 pl-6 last:pb-0">
              {index < steps.length - 1 ? (
                <span className="absolute top-4 bottom-0 left-[5px] w-px bg-line" aria-hidden="true" />
              ) : null}
              <span
                className="absolute top-1.5 left-0 h-2.5 w-2.5 rounded-full border-2 border-brand-500 bg-surface"
                aria-hidden="true"
              />

              <div className="flex items-baseline justify-between gap-3">
                <span className="text-[13px] font-medium text-ink-900">{step.label}</span>
                <span className="shrink-0 font-mono text-[11px] text-ink-500">
                  {step.ms.toFixed(1)} ms
                </span>
              </div>
              <p className="mt-0.5 text-[12px] leading-relaxed text-ink-700">{step.detail}</p>

              {step.results?.length ? (
                <ul className="mt-2 space-y-1.5">
                  {step.results.map((chunk, rank) => (
                    <li key={chunk.id} className="rounded-lg border border-line bg-canvas p-2.5">
                      <div className="mb-1 flex flex-wrap items-center gap-1.5">
                        <span className="rounded bg-brand-600 px-1.5 py-0.5 text-[10px] font-semibold text-white">
                          #{rank + 1}
                        </span>
                        <span className="font-mono text-[11px] text-ink-700">{chunk.doc_id}</span>
                        <RoleBadge role={chunk.customer_role} />
                        <span className="ml-auto font-mono text-[11px] font-medium text-brand-700">
                          {chunk.score.toFixed(4)}
                        </span>
                      </div>
                      <p className="line-clamp-3 text-[12px] leading-relaxed text-ink-700">
                        {chunk.preview}
                      </p>
                      {chunk.source_url ? (
                        <a
                          href={chunk.source_url}
                          target="_blank"
                          rel="noreferrer noopener"
                          className="mt-1.5 inline-flex items-center gap-1 text-[11px] text-brand-600 hover:underline"
                        >
                          <LinkIcon className="h-3 w-3" />
                          Nguồn gốc
                        </a>
                      ) : null}
                    </li>
                  ))}
                </ul>
              ) : null}
            </li>
          ))}
        </ol>
      ) : null}
    </div>
  );
}
