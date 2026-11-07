import { useI18n } from "@/i18n/LanguageProvider";
import { useMarket } from "@/context/MarketContext";

export function ModeToggle() {
  const { t } = useI18n();
  const { isLiveMode, setLiveMode } = useMarket();
  const opts: [boolean, string][] = [[false, t.mode.audited], [true, t.mode.live]];
  return (
    <div role="radiogroup" aria-label={t.mode.label} className="inline-flex items-center gap-1 rounded-full border bg-panel/60 p-0.5 text-[11px] font-medium">
      <span className="hidden pl-2 text-muted-foreground md:inline">{t.mode.label}:</span>
      {opts.map(([v, l]) => (
        <button key={l} role="radio" aria-checked={isLiveMode === v} onClick={() => setLiveMode(v)}
          className={`rounded-full px-3 py-1 transition-colors ${isLiveMode === v ? (v ? "bg-warn/20 text-warn" : "bg-primary text-primary-foreground") : "text-muted-foreground hover:text-foreground"}`}>
          {v && <span className={`mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-current ${isLiveMode ? "pulse-dot" : ""}`} />}{l}
        </button>
      ))}
    </div>
  );
}
