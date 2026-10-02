export function Mark({ className = "h-7 w-7" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <rect width="32" height="32" rx="8" fill="currentColor" />
      <path d="M9 10l7 13 7-13" fill="none" stroke="#F5F3EE" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function Wordmark({ light = false }: { light?: boolean }) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <Mark className={`h-7 w-7 ${light ? "text-white/15" : "text-brand"}`} />
      <span className={`font-display text-[22px] font-medium tracking-tight ${light ? "text-white" : "text-ink"}`}>Verilab</span>
    </span>
  );
}
