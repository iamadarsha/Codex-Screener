export function Topbar() {
  return (
    <header className="flex h-16 items-center justify-between border-b border-[#191a22] bg-[rgba(14,15,20,0.72)] px-6 backdrop-blur">
      <div>
        <div className="text-xs uppercase tracking-[0.2em] text-[#5C5D6E]">
          BreakoutScan
        </div>
        <div className="text-sm font-semibold text-white">
          Real-time NSE &amp; BSE breakout terminal
        </div>
      </div>

      <div className="flex items-center gap-3 rounded-full border border-[#1E1F28] bg-[#13141A] px-3 py-2">
        <span className="relative flex h-2.5 w-2.5">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#00C896] opacity-75" />
          <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-[#00C896]" />
        </span>
        <span className="text-xs font-semibold uppercase tracking-[0.24em] text-[#00C896]">
          Live
        </span>
      </div>
    </header>
  );
}

