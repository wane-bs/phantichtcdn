import { ShieldAlert, Lightbulb } from "lucide-react";
import { useI18n } from "@/i18n/LanguageProvider";
import { BASE } from "@/lib/stress-model";
import { annual } from "./data";

export function ExecutiveBriefing() {
  const { t } = useI18n();
  const fy = annual[annual.length - 1]!;
  const la = fy.liabilities / fy.assets;
  const health = fy.equity < 0 || BASE.runway < 3 ? "critical" : BASE.runway < 6 ? "watch" : "healthy";
  const hc = { critical: "border-loss/40 bg-loss/15 text-loss", watch: "border-warn/40 bg-warn/10 text-warn", healthy: "border-gain/40 bg-gain/10 text-gain" }[health];
  return (
    <div className="terminal-panel p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold">{t.briefing.title}</h3>
          <p className="text-xs text-muted-foreground">{t.briefing.subtitle}</p>
        </div>
        <span className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-[11px] font-semibold ${hc}`}>
          <span className="pulse-dot h-1.5 w-1.5 rounded-full bg-current" /> {t.briefing.health}: {t.briefing[health]}
        </span>
      </div>
      <div className="mt-4 flex items-start gap-3 rounded-xl border border-loss/40 bg-loss/10 p-4">
        <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-loss" />
        <div className="min-w-0">
          <div className="text-sm font-semibold text-loss">{t.briefing.alertTitle}</div>
          <div className="text-xs text-muted-foreground">{t.briefing.alertBody} = <span className="num font-semibold text-loss">{la.toFixed(2)}x</span></div>
        </div>
      </div>
      <div className="mt-4">
        <div className="label-caps flex items-center gap-1.5"><Lightbulb className="h-3.5 w-3.5 text-primary" />{t.briefing.recTitle}</div>
        <ol className="mt-2 grid gap-2 md:grid-cols-3">
          {t.briefing.recs.map((r, i) => (
            <li key={i} className="flex gap-3 rounded-xl bg-panel-raised/60 p-3 text-xs leading-relaxed">
              <span className="num flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground">{i + 1}</span>
              {r}
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
