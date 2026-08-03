/** Logo VinUni — dựng lại đúng hình học từ vinuni_logo.svg. */
export function Logo({ size = 32, className = "" }: { size?: number; className?: string }) {
  return (
    <svg
      viewBox="0 0 613 613"
      width={size}
      height={size}
      className={className}
      role="img"
      aria-label="VinUni"
    >
      <polygon fill="#c72127" points="126,115 213.5,202.5 126,290" />
      <polygon
        fill="#134d8b"
        points="486,113 486,296 306,476 133.5,303.5 225,212 306,293 387,212"
      />
    </svg>
  );
}

export function LogoLockup({ subtitle }: { subtitle?: string }) {
  return (
    <div className="flex items-center gap-3">
      <Logo size={34} />
      <div className="leading-tight">
        <div className="text-[15px] font-semibold tracking-tight text-ink-900">
          VinUni <span className="text-brand-600">Knowledge Base</span>
        </div>
        {subtitle ? <div className="text-[11px] text-ink-500">{subtitle}</div> : null}
      </div>
    </div>
  );
}
