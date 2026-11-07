import { useState } from "react";
import { ShieldCheck, AlertTriangle, ShieldAlert } from "lucide-react";
import { BASE, runStress, type Solvency } from "@/lib/stress-model";
import { useI18n } from "@/i18n/LanguageProvider";
import { presets, type ScenarioId } from "./scenarios";
import { SensitivityHeatmap } from "./SensitivityHeatmap";

const f0 = (n: number) => Math.round(n).toLocaleString("en-US");
const signed = (n: number) => (n >= 0 ? "+" : "â") + f0(Math.abs(n));


const sv: Record<Solvency, { cls: string; bar: string; Icon: typeof ShieldCheck }> = {
  SAFE: { cls: "border-gain/40 bg-gain/10 text-gain", bar: "bg-gain", Icon: ShieldCheck },
  CAUTION: { cls: "border-warn/40 bg-warn/10 text-warn", bar: "bg-warn", Icon: AlertTriangle },
  "CRITICAL DISTRESS": { cls: "border-loss/50 bg-loss/15 text-loss", bar: "bg-loss", Icon: ShieldAlert },
};

function Slider({ label, value, set, min, max, step, display, base }: { label: string; value: number; set: (n: number) => void; min: number; max: number; step: number; display: string; base: string }) {
  return (
    <label className="block">
      <div className="flex items-baseline justify-between">
        <span className="label-caps">{label}</span>
        <span className="num text-sm font-semibold text-foreground">{display}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(e) => set(Number(e.target.value))} className="mt-2 w-full accent-primary" />
      <div className="num flex justify-between text-[10px] text-muted-foreground"><span>{min.toLocaleString("en-US")}</span><span>{base}</span><span>{max.toLocaleString("en-US")}</span></div>
    </label>
  );
}

export function StressTest({ initialPreset }: { initialPreset?: ScenarioId | undefined }) {
  const { t } = useI18n();
  const st0 = t.stress;
  const init = presets.find((p) => p.id === initialPreset) ?? presets[0]!;
  const [fuel, setFuel] = useState(init.fuel);
  const [fx, setFx] = useState(init.fx);
  const [lf, setLf] = useState(init.lf);
  const r = runStress(fuel, fx, lf);
  const s = sv[r.solvency];

  const steps = [
    { k: st0.baseline, v: BASE.ebit, total: true },
    { k: st0.fuelShock, v: r.fuelImpact },
    { k: st0.fxLoss, v: r.fxImpact },
    { k: st0.demand, v: r.demandImpact },
    { k: st0.final, v: r.ebit, total: true, final: true },
  ];
  const scale = Math.max(BASE.ebit, ...steps.map((x) => Math.abs(x.v))) || 1;
  // gauge: map EBIT -8000..10000 to 0..100
  const pos = Math.min(100, Math.max(0, ((r.ebit + 8000) / 18000) * 100));

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {presets.map((p) => {
          const active = p.fuel === fuel && p.fx === fx && p.lf === lf;
          return (
            <button key={p.id} onClick={() => { setFuel(p.fuel); setFx(p.fx); setLf(p.lf); }}
              className={`num rounded-full border px-4 py-1.5 text-xs transition-colors ${active ? "border-primary bg-primary/15 text-primary" : "text-muted-foreground hover:bg-panel-raised hover:text-foreground"}`}>
              {t.scenarios[p.id]}
            </button>
          );
        })}
      </div>

      <div className={`flex flex-wrap items-center gap-4 rounded-2xl border p-4 ${s.cls}`}>
        <s.Icon className="h-8 w-8 shrink-0" />
        <div className="flex-1">
          <div className="num text-lg font-bold tracking-wider">{t.solvency[r.solvency]}</div>
          <div className="text-xs opacity-90">{t.solvencyMsg[r.solvency]}</div>
        </div>
        <div className="text-right">
          <div className="label-caps">{st0.stressedEbit}</div>
          <div className="num text-3xl font-semibold">{f0(r.ebit)} <span className="text-sm">B VND</span></div>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="terminal-panel space-y-6 p-5">
          <h3 className="text-sm font-semibold">{st0.inputs}</h3>
          <Slider label={st0.fuel} value={fuel} set={setFuel} min={70} max={140} step={0.1} display={`$${fuel.toFixed(1)}/bbl`} base={`${st0.base} $101`} />
          <Slider label={st0.fx} value={fx} set={setFx} min={24000} max={27000} step={50} display={fx.toLocaleString("en-US")} base={`${st0.base} 25,690`} />
          <Slider label={st0.lf} value={lf} set={setLf} min={65} max={90} step={0.5} display={`${lf.toFixed(1)}%`} base={`${st0.base} 79.5%`} />
          <div className="num space-y-1 border-t pt-4 text-[10px] text-muted-foreground">
            <div>ÎFuel = (P â 101) Ã 8.2M bbl Ã FX</div>
            <div>FX Loss = $1.8B Ã (FX â 25,690)</div>
            <div>Demand = (LF â 79.5) Ã 850</div>
          </div>
        </div>

        <div className="terminal-panel p-5 lg:col-span-2">
          <h3 className="text-sm font-semibold">{st0.waterfall}</h3>
          <div className="mt-4 space-y-3">
            {steps.map((st) => {
              const w = (Math.abs(st.v) / scale) * 50;
              const neg = st.v < 0;
              const color = st.total ? ("final" in st ? s.bar : "bg-chart-5") : neg ? "bg-loss" : "bg-gain";
              return (
                <div key={st.k} className="grid grid-cols-[110px_1fr_90px] items-center gap-3 sm:grid-cols-[140px_1fr_100px]">
                  <span className={`text-xs ${st.total ? "font-semibold" : "text-muted-foreground"}`}>{st.k}</span>
                  <div className="relative h-6 rounded-lg bg-panel-raised/40">
                    <div className="absolute inset-y-0 left-1/2 w-px bg-border" />
                    <div className={`absolute inset-y-1 rounded-sm ${color}`} style={{ width: `${w}%`, left: neg ? `${50 - w}%` : "50%" }} />
                  </div>
                  <span className={`num text-right text-xs font-semibold ${st.total ? "" : neg ? "text-loss" : st.v > 0 ? "text-gain" : "text-muted-foreground"}`}>
                    {st.total ? f0(st.v) : signed(st.v)}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="mt-6 grid gap-4 border-t pt-5 sm:grid-cols-2">
            <div>
              <div className="label-caps">{st0.gauge}</div>
              <div className="relative mt-3 h-2.5 rounded-full" style={{ background: "linear-gradient(90deg, var(--loss) 0%, var(--loss) 44.4%, var(--warn) 44.4%, var(--warn) 66.7%, var(--gain) 66.7%)" }}>
                <div className="absolute -top-1 h-4.5 w-1 rounded-sm bg-foreground transition-all duration-75" style={{ left: `calc(${pos}% - 2px)` }} />
              </div>
              <div className="num mt-1 flex justify-between text-[10px] text-muted-foreground"><span>-8k</span><span>0</span><span>4k</span><span>10k</span></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <div className="label-caps">{st0.runway}</div>
                <div className={`num text-2xl font-semibold ${r.runway >= BASE.runway ? "text-gain" : r.runway >= 3 ? "text-warn" : "text-loss"}`}>{Number.isFinite(r.runway) ? r.runway.toFixed(1) : "â"} <span className="text-xs">{st0.mo}</span></div>
              </div>
              <div>
                <div className="label-caps">{st0.delta}</div>
                <div className={`num text-2xl font-semibold ${r.ebit >= BASE.ebit ? "text-gain" : "text-loss"}`}>{signed(r.ebit - BASE.ebit)}</div>
              </div>
            </div>
          </div>
          <p className="mt-3 text-[10px] text-muted-foreground">{st0.runwayNote}</p>
        </div>
      </div>
      <SensitivityHeatmap fuel={fuel} fx={fx} />
    </div>
  );
}
