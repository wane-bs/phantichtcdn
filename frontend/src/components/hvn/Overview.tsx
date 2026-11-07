import { Bar, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AlertTriangle, TrendingUp, Gauge, Droplets, Landmark } from "lucide-react";
import { quarterly } from "./data";
import { useI18n } from "@/i18n/LanguageProvider";
import type { Dict } from "@/i18n/dictionary";
import { runStress } from "@/lib/stress-model";
import { presets, type ScenarioId } from "./scenarios";
import { ExecutiveBriefing } from "./ExecutiveBriefing";
import { RunwayGauge } from "./RunwayGauge";

const fmt = (n: number) => n.toLocaleString("en-US");

type Tone = "gain" | "warn" | "loss";
const toneText: Record<Tone, string> = { gain: "text-gain", warn: "text-warn", loss: "text-loss" };
const toneBg: Record<Tone, string> = {
  gain: "bg-gain/10 text-gain border-gain/30",
  warn: "bg-warn/10 text-warn border-warn/30",
  loss: "bg-loss/15 text-loss border-loss/40",
};

const getKpis = (t: Dict["kpi"]): { label: string; value: string; unit: string; badge: string; tone: Tone; icon: typeof TrendingUp; note: string }[] => [
  { label: t.revenue, value: "105,942", unit: "B VND", badge: t.revenueBadge, tone: "gain", icon: TrendingUp, note: t.revenueNote },
  { label: t.ebit, value: "6,431", unit: "B VND", badge: t.ebitBadge, tone: "gain", icon: Landmark, note: t.ebitNote },
  { label: t.equity, value: "-9,344", unit: "B VND", badge: t.equityBadge, tone: "loss", icon: AlertTriangle, note: t.equityNote },
  { label: t.dol, value: "4.12", unit: "x", badge: t.dolBadge, tone: "warn", icon: Gauge, note: t.dolNote },
  { label: t.runway, value: "4.2", unit: t.months, badge: t.runwayBadge, tone: "loss", icon: Droplets, note: t.runwayNote },
];

function KpiCard(k: ReturnType<typeof getKpis>[number]) {
  const Icon = k.icon;
  return (
    <div className={`terminal-panel relative overflow-hidden p-4 ${k.tone === "loss" ? "border-loss/50" : ""}`}>
      <div className={`absolute inset-x-0 top-0 h-0.5 ${k.tone === "gain" ? "bg-gain" : k.tone === "warn" ? "bg-warn" : "bg-loss"}`} />
      <div className="flex items-center justify-between">
        <span className="label-caps leading-snug">{k.label}</span>
        <Icon className={`h-4 w-4 ${toneText[k.tone]}`} />
      </div>
      <div className="mt-3 flex items-baseline gap-1.5">
        <span className={`num text-2xl font-semibold ${k.tone === "loss" ? "text-loss" : "text-foreground"}`}>{k.value}</span>
        <span className="num text-xs text-muted-foreground">{k.unit}</span>
      </div>
      <div className="mt-3 flex items-center justify-between gap-2">
        <span className={`num inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase ${toneBg[k.tone]}`}>
          {k.tone === "loss" && <span className="pulse-dot h-1.5 w-1.5 rounded-full bg-loss" />}
          {k.badge}
        </span>
        <span className="truncate text-[10px] text-muted-foreground">{k.note}</span>
      </div>
    </div>
  );
}

const dupontRows = [
  { k: "tax", f: "NPAT / EBT", v: "0.886", d: "x" },
  { k: "interest", f: "EBT / EBIT", v: "0.774", d: "x" },
  { k: "margin", f: "EBIT / Revenue", v: "6.07", d: "%" },
  { k: "turnover", f: "Revenue / Assets", v: "1.821", d: "x" },
  { k: "multiplier", f: "Assets / Equity", v: "-6.23", d: "x", bad: true },
];

function DuPont() {
  const { t } = useI18n();
  const d = t.dupont;
  return (
    <div className="terminal-panel p-5">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold">{d.title}</h3>
          <p className="text-xs text-muted-foreground">{d.sub}</p>
        </div>
        <span className="num rounded-full border border-loss/40 bg-loss/15 px-1.5 py-0.5 text-[10px] font-semibold text-loss">{d.distorted}</span>
      </div>
      <div className="mt-4 space-y-2">
        {dupontRows.map((s, i) => (
          <div key={s.k} className="flex items-center gap-3 rounded-xl bg-panel-raised/50 px-3 py-2">
            <span className="num w-5 text-xs text-muted-foreground">{i + 1}</span>
            <div className="flex-1">
              <div className="text-xs font-medium">{d[s.k as "tax"]}</div>
              <div className="num text-[10px] text-muted-foreground">{s.f}</div>
            </div>
            <span className={`num text-sm font-semibold ${s.bad ? "text-loss" : "text-foreground"}`}>
              {s.v}<span className="text-muted-foreground">{s.d}</span>
            </span>
          </div>
        ))}
      </div>
      <div className="mt-4 grid grid-cols-2 gap-2 border-t pt-4">
        <div>
          <div className="label-caps">{d.roa}</div>
          <div className="num text-lg font-semibold text-gain">7.58%</div>
        </div>
        <div>
          <div className="label-caps">{d.roe}</div>
          <div className="num text-lg font-semibold text-loss">-47.2%</div>
        </div>
      </div>
      <p className="mt-3 text-[11px] leading-relaxed text-muted-foreground">
        {d.note}
      </p>
    </div>
  );
}

const tip = {
  contentStyle: { background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 12, fontFamily: "var(--font-mono)", fontSize: 11 },
  labelStyle: { color: "var(--foreground)" },
  formatter: (v: unknown) => fmt(Number(v)) + " B",
};

function QuickScenarios({ onScenario }: { onScenario: (id: ScenarioId) => void }) {
  const { t } = useI18n();
  const tone = { SAFE: "text-gain", CAUTION: "text-warn", "CRITICAL DISTRESS": "text-loss" } as const;
  return (
    <div className="terminal-panel p-5">
      <div className="label-caps">{t.presetsCard.title}</div>
      <p className="text-xs text-muted-foreground">{t.presetsCard.subtitle}</p>
      <div className="mt-3 space-y-2">
        {presets.filter((p) => p.id !== "base").map((p) => {
          const r = runStress(p.fuel, p.fx, p.lf);
          return (
            <button key={p.id} onClick={() => onScenario(p.id)} className="flex w-full items-center justify-between gap-3 rounded-xl border bg-panel-raised/40 px-3 py-2.5 text-left transition-colors hover:border-primary/60 hover:bg-primary/10">
              <span className="text-xs font-medium">{t.scenarios[p.id]}</span>
              <span className="text-right">
                <span className={`num block text-sm font-semibold ${tone[r.solvency]}`}>{fmt(Math.round(r.ebit))}</span>
                <span className={`num block text-[9px] font-semibold ${tone[r.solvency]}`}>{t.solvency[r.solvency]}</span>
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function Overview({ onScenario }: { onScenario: (id: ScenarioId) => void }) {
  const { t } = useI18n();
  const o = t.overview;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_280px_300px]">
        <ExecutiveBriefing />
        <RunwayGauge />
        <QuickScenarios onScenario={onScenario} />
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {getKpis(t.kpi).map((k) => <KpiCard key={k.label} {...k} />)}
      </div>
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="terminal-panel p-5 xl:col-span-2">
          <div className="flex flex-wrap items-end justify-between gap-2">
            <div>
              <h3 className="text-sm font-semibold">{o.chartTitle}</h3>
              <p className="text-xs text-muted-foreground">{o.chartSub}</p>
            </div>
            <span className="num text-[10px] text-muted-foreground">{o.fuelShare}: <span className="text-warn">35.8%</span></span>
          </div>
          <div className="mt-4 h-[360px]">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={quarterly} margin={{ top: 5, right: 10, left: -5, bottom: 0 }}>
                <CartesianGrid stroke="var(--border)" strokeDasharray="2 4" vertical={false} />
                <XAxis dataKey="q" tick={{ fill: "var(--muted-foreground)", fontSize: 11, fontFamily: "var(--font-mono)" }} axisLine={{ stroke: "var(--border)" }} tickLine={false} />
                <YAxis yAxisId="l" tick={{ fill: "var(--muted-foreground)", fontSize: 11, fontFamily: "var(--font-mono)" }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v / 1000}k`} />
                <YAxis yAxisId="r" orientation="right" tick={{ fill: "var(--muted-foreground)", fontSize: 11, fontFamily: "var(--font-mono)" }} axisLine={false} tickLine={false} />
                <Tooltip {...tip} cursor={{ fill: "var(--panel-raised)", opacity: 0.4 }} />
                <Legend wrapperStyle={{ fontSize: 11, fontFamily: "var(--font-mono)" }} />
                <Bar yAxisId="l" dataKey="fuel" name={o.fuel} stackId="c" fill="var(--chart-2)" />
                <Bar yAxisId="l" dataKey="leasing" name={o.leasing} stackId="c" fill="var(--chart-4)" />
                <Bar yAxisId="l" dataKey="personnel" name={o.personnel} stackId="c" fill="var(--chart-5)" radius={[2, 2, 0, 0]} />
                <Line yAxisId="l" dataKey="revenue" name={o.revenue} stroke="var(--chart-1)" strokeWidth={2} dot={{ r: 3 }} />
                <Line yAxisId="r" dataKey="ebit" name={o.ebitR} stroke="var(--chart-3)" strokeWidth={2} strokeDasharray="4 3" dot={{ r: 3 }} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>
        <DuPont />
      </div>
    </div>
  );
}
