import { useI18n } from "@/i18n/LanguageProvider";
import { BASE, MONTHLY_BURN } from "@/lib/stress-model";

const MAX = 12;
const pt = (m: number, r: number) => {
  const a = Math.PI * (1 - Math.min(m, MAX) / MAX);
  return [100 + r * Math.cos(a), 100 - r * Math.sin(a)];
};
const arc = (from: number, to: number, r = 80) => {
  const [x1, y1] = pt(from, r); const [x2, y2] = pt(to, r);
  return `M ${x1} ${y1} A ${r} ${r} 0 0 1 ${x2} ${y2}`;
};

export function RunwayGauge() {
  const { t } = useI18n();
  const m = BASE.runway;
  const [nx, ny] = pt(m, 66);
  return (
    <div className="terminal-panel flex flex-col p-5">
      <div className="label-caps">{t.gauge.title}</div>
      <svg viewBox="0 0 200 115" className="mx-auto mt-2 w-full max-w-[260px]">
        <path d={arc(0, 3)} stroke="var(--loss)" strokeWidth="12" fill="none" />
        <path d={arc(3, 6)} stroke="var(--warn)" strokeWidth="12" fill="none" />
        <path d={arc(6, 12)} stroke="var(--gain)" strokeWidth="12" fill="none" opacity="0.8" />
        <line x1="100" y1="100" x2={nx} y2={ny} stroke="var(--foreground)" strokeWidth="3" strokeLinecap="round" />
        <circle cx="100" cy="100" r="5" fill="var(--primary)" />
        <text x="16" y="112" fill="var(--muted-foreground)" fontFamily="var(--font-mono)" fontSize="8">0</text>
        <text x="178" y="112" fill="var(--muted-foreground)" fontFamily="var(--font-mono)" fontSize="8">12</text>
      </svg>
      <div className="num text-center text-3xl font-semibold text-loss">{m.toFixed(1)} <span className="text-xs font-normal text-muted-foreground">{t.gauge.months}</span></div>
      <div className="num mt-4 grid grid-cols-2 gap-2 border-t pt-3 text-xs">
        <div><div className="label-caps">{t.gauge.cash}</div><div className="font-semibold">{BASE.cash.toLocaleString("en-US")} B</div></div>
        <div className="text-right"><div className="label-caps">{t.gauge.burn}</div><div className="font-semibold">~{Math.round(MONTHLY_BURN).toLocaleString("en-US")} B</div></div>
      </div>
    </div>
  );
}
