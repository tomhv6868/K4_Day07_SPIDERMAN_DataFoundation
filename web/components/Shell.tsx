"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChatIcon, DocsIcon } from "./Icons";
import { LogoLockup } from "./Logo";

const NAV = [
  { href: "/", label: "Trò chuyện", icon: ChatIcon },
  { href: "/documents", label: "Kho tài liệu", icon: DocsIcon },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex h-dvh overflow-hidden bg-canvas">
      <aside className="hidden w-64 shrink-0 flex-col border-r border-line bg-surface md:flex">
        <div className="border-b border-line px-5 py-4">
          <LogoLockup subtitle="K4 · Nhóm SPIDERMAN" />
        </div>

        <nav className="flex-1 space-y-1 p-3">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors ${
                  active
                    ? "bg-brand-50 font-medium text-brand-700"
                    : "text-ink-700 hover:bg-canvas hover:text-ink-900"
                }`}
              >
                <Icon className={active ? "text-brand-600" : "text-ink-500"} />
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-line px-5 py-4 text-[11px] leading-relaxed text-ink-500">
          <div className="mb-1 font-medium text-ink-700">Chính sách TMĐT Việt Nam</div>
          Đổi trả · hoàn tiền · khiếu nại, nhìn từ phía người mua và người bán.
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-line bg-surface px-4 py-3 md:hidden">
          <LogoLockup />
          <nav className="flex gap-1">
            {NAV.map(({ href, label, icon: Icon }) => {
              const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
              return (
                <Link
                  key={href}
                  href={href}
                  aria-label={label}
                  className={`rounded-lg p-2 ${
                    active ? "bg-brand-50 text-brand-700" : "text-ink-500"
                  }`}
                >
                  <Icon />
                </Link>
              );
            })}
          </nav>
        </header>
        {children}
      </div>
    </div>
  );
}
