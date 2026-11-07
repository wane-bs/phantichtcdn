import { useState } from "react";
import { annual } from "./data";
import { useI18n } from "@/i18n/LanguageProvider";
import { commonSize, yoy, type LineKind } from "@/lib/statement-views";

const fmt = (n: number) => n.toLocaleString("en-US");
type Row = (typeof annual)[number];
type Mode = "abs" | "yoy" | "cs";
const lines: { key: "revenue" | "grossProfit" | "assets" | "liabilities" | "equity" | "cash"; kind: LineKind }[] = [
  { key: "revenue", kind: "pl" }, { key: "grossProfit", kind: "pl" }, { key: "assets", kind: "bs" },
  { key: "liabilities", kind: "bs" }, { key: "equity", kind: "bs" }, { key: "cash", kind: "bs" },
];
const pct = (n: number) => (n >= 0 ? "+" : "") + n.toFixed(1) + "%";

export function Statements() {
  const { t } = useI18n();
  const f = t.fs;
  const [mode, setMode] = useState<Mode>("abs");
  const cell = (key: (typeof lines)[number]["key"], kind: LineKind, i: number): { v: string; neg: boolean } => {
    const a = annual[i]!;
    if (mode === "abs") return { v: fmt(a[key]), neg: a[key] < 0 };
    if (mode === "cs") { const c = commonSize(a[key], kind, a); return { v: c.toFixed(1) + "%", neg: c < 0 }; }
    const prev = annual[i - 1]?.[key];
    const g = yoy(a[key], prev);
    if (g === null) return { v: "â", neg: false };
    return { v: pct(g) + (prev! < 0 ? "*" : ""), neg: g < 0 };
  };
  const ratios: [string, (a: Row) => string][] = [
    [f.grossMargin, (a) => ((a.grossProfit / a.revenue) * 100).toFixed(1) + "%"],
    [f.la, (a) => (a.liabilities / a.assets).toFixed(2) + "x"],
  ];
  const modes: [Mode, string][] = [["abs", f.absolute], ["yoy", f.yoy], ["cs", f.common]];
  return (
    <div className="terminal-panel p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-sm font-semibold">{f.title}</h3>
        <div className="inline-flex flex-wrap rounded-full border bg-panel-raised/40 p-0.5 text-[11px] font-medium">
          {modes.map(([m, l]) => (
            <button key={m} aria-pressed={mode === m} onClick={() => setMode(m)}
              className={`rounded-full px-3 py-1 transition-colors ${mode === m ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"}`}>{l}</button>
          ))}
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="num w-full min-w-[640px] text-xs">
          <thead><tr className="border-b text-muted-foreground"><th className="py-2 text-left font-medium">{f.item}</th>{annual.map((a) => <th key={a.year} className="py-2 text-right font-medium">{a.year}</th>)}</tr></thead>
          <tbody>
            {lines.map(({ key, kind }) => (
              <tr key={key} className="border-b border-border/50 hover:bg-panel-raised/40">
                <td className="py-2 font-sans">{f[key]}</td>
                {annual.map((a, i) => { const c = cell(key, kind, i); return <td key={a.year} className={`py-2 text-right ${c.neg ? "text-loss" : mode === "yoy" && c.v !== "â" ? "text-gain" : ""}`}>{c.v}</td>; })}
              </tr>
            ))}
            {mode === "abs" && ratios.map(([l, fn]) => (
              <tr key={l} className="border-b border-border/50 hover:bg-panel-raised/40">
                <td className="py-2 font-sans">{l}</td>
                {annual.map((a) => { const v = fn(a); return <td key={a.year} className={`py-2 text-right ${v.startsWith("-") ? "text-loss" : ""}`}>{v}</td>; })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {mode !== "abs" && <p className="mt-3 text-[10px] text-muted-foreground">{mode === "yoy" ? f.yoyNote : f.commonNote}</p>}
    </div>
  );
}

type Status = "pass" | "caution" | "anomaly";
const badge: Record<Status, string> = {
  pass: "border-gain/40 bg-gain/10 text-gain",
  caution: "border-warn/40 bg-warn/10 text-warn",
  anomaly: "border-loss/40 bg-loss/15 text-loss",
};

export function Diagnostics() {
  const { t } = useI18n();
  const d = t.diag;
  const rows: { group: string; name: string; stat: string; note: string; s: Status }[] = [
    { group: d.adf, name: d.fx, stat: "ADF = -53.77 Â· p < 0.001", note: d.fxNote, s: "pass" },
    { group: d.adf, name: d.tc, stat: "ADF = -3.55 Â· p = 0.0069", note: d.tcNote, s: "pass" },
    { group: d.adf, name: d.oil, stat: "p = 0.69", note: d.oilNote, s: "caution" },
    { group: d.coint, name: "ln(TC) ~ ln(Rev)", stat: "p = 0.45", note: d.cointNote, s: "caution" },
    { group: d.sloan, name: "Sloan", stat: d.sloanVal, note: d.sloanNote, s: "anomaly" },
  ];
  return (
    <div className="terminal-panel p-5">
      <h3 className="text-sm font-semibold">{d.title}</h3>
      <div className="mt-4 divide-y divide-border rounded-xl border">
        {rows.map((r) => (
          <div key={r.name} className="grid gap-2 p-4 md:grid-cols-[220px_200px_1fr_auto] md:items-center">
            <div>
              <div className="label-caps">{r.group}</div>
              <div className="text-sm font-medium">{r.name}</div>
            </div>
            <div className="num text-sm font-semibold">{r.stat}</div>
            <div className="text-xs leading-relaxed text-muted-foreground">{r.note}</div>
            <span className={`num w-fit rounded-full border px-2.5 py-0.5 text-[10px] font-semibold ${badge[r.s]}`}>{d[r.s]}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function Dossier() {
  const { t } = useI18n();
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {t.dossier.map(([title, body]) => (
        <div key={title} className="terminal-panel p-5"><div className="label-caps text-warn">{title}</div><p className="mt-2 text-sm leading-relaxed">{body}</p></div>
      ))}
    </div>
  );
}
