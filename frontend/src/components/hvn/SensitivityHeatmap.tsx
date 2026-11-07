import { useI18n } from "@/i18n/LanguageProvider";
import { BASE, runStress } from "@/lib/stress-model";

const FUELS = [70, 87.5, 105, 122.5, 140];
const FXS = [24000, 24750, 25500, 26250, 27000];
const nearest = (arr: number[], v: number) => arr.reduce((b, x) => (Math.abs(x - v) < Math.abs(b - v) ? x : b));

export function SensitivityHeatmap({ fuel, fx }: { fuel: number; fx: number }) {
  const { t } = useI18n();
  const nf = nearest(FUELS, fuel), nx = nearest(FXS, fx);
  return (
    <div className="terminal-panel p-5">
      <h3 className="text-sm font-semibold">{t.heatmap.title}</h3>
      <p className="text-xs text-muted-foreground">{t.heatmap.sub}</p>
      <div className="mt-4 overflow-x-auto">
        <table className="num w-full min-w-[520px] border-separate border-spacing-1 text-xs">
          <thead>
            <tr>
              <th className="p-2 text-left text-[10px] font-medium text-muted-foreground">{t.heatmap.fuel}</th>
              {FXS.map((x) => <th key={x} className="p-2 text-right font-medium text-muted-foreground">{x.toLocaleString("en-US")}</th>)}
            </tr>
          </thead>
          <tbody>
            {FUELS.map((f) => (
              <tr key={f}>
                <td className="p-2 font-medium text-muted-foreground">${f}</td>
                {FXS.map((x) => {
                  const e = runStress(f, x, BASE.lf).ebit;
                  const tone = e >= 4000 ? "gain" : e >= 0 ? "warn" : "loss";
                  const a = Math.round(Math.min(1, Math.abs(e) / 15000) * 50 + 12);
                  const cur = f === nf && x === nx;
                  return (
                    <td key={x} title={cur ? t.heatmap.current : undefined}
                      className={`rounded-lg p-2 text-right font-semibold ${cur ? "ring-2 ring-primary" : ""}`}
                      style={{ background: `color-mix(in oklab, var(--${tone}) ${a}%, transparent)`, color: "var(--foreground)" }}>
                      {Math.round(e).toLocaleString("en-US")}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
