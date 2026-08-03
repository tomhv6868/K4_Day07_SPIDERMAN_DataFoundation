"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchDocument, fetchDocuments } from "@/lib/api";
import {
  ROLE_LABELS,
  STRATEGY_LABELS,
  type DocumentDetail,
  type DocumentStats,
  type DocumentSummary,
  type Strategy,
} from "@/lib/types";
import { CloseIcon, LinkIcon, SearchIcon } from "./Icons";

function RolePill({ role }: { role: string }) {
  const tone =
    role === "seller"
      ? "bg-accent-50 text-accent-700 ring-accent-200"
      : role === "buyer"
        ? "bg-brand-50 text-brand-700 ring-brand-200"
        : "bg-canvas text-ink-700 ring-line";
  return (
    <span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset ${tone}`}>
      {ROLE_LABELS[role] ?? role}
    </span>
  );
}

function StatCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-xl border border-line bg-surface p-4">
      <div className="text-[11px] font-medium tracking-wide text-ink-500 uppercase">{label}</div>
      <div className="mt-1 text-2xl font-semibold tracking-tight text-ink-900">{value}</div>
      {hint ? <div className="mt-0.5 text-[11px] text-ink-500">{hint}</div> : null}
    </div>
  );
}

export function DocumentsView() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [stats, setStats] = useState<DocumentStats | null>(null);
  const [strategy, setStrategy] = useState<Strategy>("fixed_size");
  const [query, setQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [selected, setSelected] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    fetchDocuments(strategy)
      .then((data) => {
        if (cancelled) return;
        setDocuments(data.documents);
        setStats(data.stats);
      })
      .catch((cause: unknown) => {
        if (!cancelled) setError(cause instanceof Error ? cause.message : "Lỗi không xác định.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [strategy]);

  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return documents.filter((doc) => {
      if (roleFilter && doc.customer_role !== roleFilter) return false;
      if (!needle) return true;
      return (
        doc.title.toLowerCase().includes(needle) ||
        doc.doc_id.toLowerCase().includes(needle) ||
        doc.category.toLowerCase().includes(needle)
      );
    });
  }, [documents, query, roleFilter]);

  const roles = Object.entries(stats?.roles ?? {}).sort((a, b) => b[1] - a[1]);

  return (
    <div className="min-h-0 flex-1 overflow-y-auto">
      <div className="mx-auto w-full max-w-5xl px-4 py-8">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold tracking-tight text-ink-900">Kho tài liệu</h1>
          <p className="mt-1 text-sm text-ink-500">
            Corpus <code className="font-mono text-ink-700">data/k4_ecommerce</code> — nguồn công
            khai, đã kiểm <code className="font-mono text-ink-700">robots.txt</code> và làm sạch.
          </p>
        </header>

        {error ? (
          <div className="mb-6 rounded-xl border border-accent-200 bg-accent-50 px-4 py-3 text-[13px] text-accent-700">
            {error} — chạy backend bằng{" "}
            <code className="font-mono">uvicorn api.server:app --port 8000</code>.
          </div>
        ) : null}

        {stats ? (
          <div className="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Tài liệu" value={String(stats.total_documents)} hint="cần 5–10" />
            <StatCard
              label="Chunk"
              value={String(stats.total_chunks)}
              hint={STRATEGY_LABELS[stats.strategy as Strategy] ?? stats.strategy}
            />
            <StatCard
              label="Ký tự"
              value={stats.total_chars.toLocaleString("vi-VN")}
              hint="sau khi làm sạch"
            />
            <div className="rounded-xl border border-line bg-surface p-4">
              <div className="text-[11px] font-medium tracking-wide text-ink-500 uppercase">
                Phân vai customer_role
              </div>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {roles.map(([role, count]) => (
                  <span key={role} className="flex items-center gap-1">
                    <RolePill role={role} />
                    <span className="font-mono text-[11px] text-ink-500">{count}</span>
                  </span>
                ))}
              </div>
            </div>
          </div>
        ) : null}

        <div className="mb-4 flex flex-wrap items-center gap-2">
          <div className="relative min-w-[220px] flex-1">
            <SearchIcon className="absolute top-1/2 left-3 -translate-y-1/2 text-ink-300" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Tìm theo tiêu đề, doc_id, category…"
              className="w-full rounded-lg border border-line bg-surface py-2 pr-3 pl-9 text-[13px] text-ink-900 outline-none focus:border-brand-400"
            />
          </div>

          <select
            value={roleFilter}
            onChange={(event) => setRoleFilter(event.target.value)}
            className="rounded-lg border border-line bg-surface px-3 py-2 text-[13px] text-ink-900 outline-none focus:border-brand-400"
          >
            <option value="">Tất cả vai trò</option>
            {roles.map(([role]) => (
              <option key={role} value={role}>
                {ROLE_LABELS[role] ?? role}
              </option>
            ))}
          </select>

          <select
            value={strategy}
            onChange={(event) => setStrategy(event.target.value as Strategy)}
            className="rounded-lg border border-line bg-surface px-3 py-2 text-[13px] text-ink-900 outline-none focus:border-brand-400"
          >
            {Object.entries(STRATEGY_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>

        <div className="overflow-hidden rounded-xl border border-line bg-surface">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-[13px]">
              <thead className="border-b border-line bg-canvas text-[11px] tracking-wide text-ink-500 uppercase">
                <tr>
                  <th className="px-4 py-2.5 font-medium">Tài liệu</th>
                  <th className="px-4 py-2.5 font-medium">Vai trò</th>
                  <th className="px-4 py-2.5 font-medium">Category</th>
                  <th className="px-4 py-2.5 text-right font-medium">Chunk</th>
                  <th className="px-4 py-2.5 text-right font-medium">Ký tự</th>
                  <th className="px-4 py-2.5 font-medium">Phiên bản</th>
                  <th className="px-4 py-2.5" />
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-10 text-center text-ink-500">
                      Đang tải…
                    </td>
                  </tr>
                ) : visible.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-10 text-center text-ink-500">
                      Không có tài liệu nào khớp bộ lọc.
                    </td>
                  </tr>
                ) : (
                  visible.map((doc) => (
                    <tr key={doc.doc_id} className="border-b border-line last:border-0 hover:bg-canvas">
                      <td className="px-4 py-3">
                        <button
                          type="button"
                          onClick={() =>
                            fetchDocument(doc.doc_id)
                              .then(setSelected)
                              .catch((cause: unknown) =>
                                setError(cause instanceof Error ? cause.message : "Lỗi tải tài liệu."),
                              )
                          }
                          className="text-left font-medium text-ink-900 hover:text-brand-700"
                        >
                          {doc.title}
                        </button>
                        <div className="mt-0.5 font-mono text-[11px] text-ink-500">{doc.doc_id}</div>
                      </td>
                      <td className="px-4 py-3">
                        <RolePill role={doc.customer_role} />
                      </td>
                      <td className="px-4 py-3 text-ink-700">{doc.category || "—"}</td>
                      <td className="px-4 py-3 text-right font-mono text-ink-700">
                        {doc.chunk_count}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-ink-700">
                        {doc.char_count.toLocaleString("vi-VN")}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={
                            doc.document_version === "not-stated"
                              ? "text-[12px] text-ink-300"
                              : "font-mono text-[12px] text-ink-700"
                          }
                        >
                          {doc.document_version}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        {doc.source_url ? (
                          <a
                            href={doc.source_url}
                            target="_blank"
                            rel="noreferrer noopener"
                            aria-label={`Mở nguồn gốc của ${doc.doc_id}`}
                            className="inline-flex text-ink-300 hover:text-brand-600"
                          >
                            <LinkIcon />
                          </a>
                        ) : null}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <p className="mt-3 text-[11px] text-ink-500">
          Hiện {visible.length}/{documents.length} tài liệu. Số chunk đổi theo chiến lược chia nhỏ
          đang chọn.
        </p>
      </div>

      {selected ? (
        <div className="fixed inset-0 z-50 flex justify-end bg-ink-900/25" role="dialog" aria-modal="true">
          <button
            type="button"
            aria-label="Đóng"
            className="flex-1 cursor-default"
            onClick={() => setSelected(null)}
          />
          <div className="animate-rise flex w-full max-w-2xl flex-col bg-surface shadow-xl">
            <div className="flex items-start justify-between gap-4 border-b border-line px-5 py-4">
              <div className="min-w-0">
                <h2 className="truncate text-[15px] font-semibold text-ink-900">{selected.title}</h2>
                <div className="mt-1 flex flex-wrap items-center gap-2">
                  <RolePill role={selected.customer_role} />
                  <span className="font-mono text-[11px] text-ink-500">{selected.doc_id}</span>
                  <span className="text-[11px] text-ink-500">
                    lấy ngày {selected.retrieved_at} · phiên bản {selected.document_version}
                  </span>
                </div>
                {selected.source_url ? (
                  <a
                    href={selected.source_url}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="mt-1.5 inline-flex items-center gap-1 text-[11px] break-all text-brand-600 hover:underline"
                  >
                    <LinkIcon className="h-3 w-3 shrink-0" />
                    {selected.source_url}
                  </a>
                ) : null}
              </div>
              <button
                type="button"
                onClick={() => setSelected(null)}
                aria-label="Đóng"
                className="shrink-0 rounded-lg p-1.5 text-ink-500 hover:bg-canvas hover:text-ink-900"
              >
                <CloseIcon />
              </button>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
              <pre className="font-sans text-[13px] leading-[1.75] whitespace-pre-wrap text-ink-700">
                {selected.content}
              </pre>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
