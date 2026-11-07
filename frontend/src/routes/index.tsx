import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Overview } from "@/components/hvn/Overview";
import { StressTest } from "@/components/hvn/StressTest";
import { Statements, Diagnostics, Dossier } from "@/components/hvn/OtherTabs";
import { MarketSync } from "@/components/hvn/MarketSync";
import { ModeToggle } from "@/components/hvn/ModeToggle";
import { LanguageToggle } from "@/components/hvn/LanguageToggle";
import { useI18n } from "@/i18n/LanguageProvider";
import type { ScenarioId } from "@/components/hvn/scenarios";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "HVN Financial Intelligence â Vietnam Airlines Stress-Testing" },
      { name: "description", content: "Executive overview, macro stress-testing and audited FY2020âFY2024 financials for Vietnam Airlines (HVN)." },
      { property: "og:title", content: "HVN Financial Intelligence Platform" },
      { property: "og:description", content: "Quantitative stress-testing and financial analytics for Vietnam Airlines (HOSE: HVN)." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

const tabIds = ["overview", "stress", "fs", "stats", "dossier"] as const;
type TabId = (typeof tabIds)[number];

function Index() {
  const { t } = useI18n();
  const [tab, setTab] = useState<TabId>("overview");
  const [preset, setPreset] = useState<ScenarioId | undefined>();
  const openScenario = (id: ScenarioId) => { setPreset(id); setTab("stress"); window.scrollTo({ top: 0 }); };
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-[1600px] flex-wrap items-center justify-between gap-3 px-4 py-3 md:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <span className="num shrink-0 rounded-full bg-primary px-3 py-1 text-xs font-bold text-primary-foreground">HVN: HOSE</span>
            <p className="min-w-0 text-xs text-muted-foreground md:text-sm">
              <span className="font-semibold text-foreground">{t.header.company}</span> â {t.header.subtitle}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="num hidden items-center gap-1.5 rounded-full border border-gain/30 bg-gain/10 px-3 py-1 text-[10px] font-semibold uppercase text-gain sm:inline-flex">
              <span className="pulse-dot h-1.5 w-1.5 rounded-full bg-gain" /> {t.header.data}
            </span>
            <ModeToggle />
            <MarketSync onViewToday={() => openScenario("live")} />
            <LanguageToggle />
          </div>
        </div>
        <nav className="mx-auto flex max-w-[1600px] gap-1 overflow-x-auto px-4 pb-3 md:px-6">
          {tabIds.map((id) => (
            <button key={id} onClick={() => { setTab(id); if (id !== "stress") setPreset(undefined); }}
              className={`whitespace-nowrap rounded-full px-4 py-1.5 text-xs font-medium transition-colors ${tab === id ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-secondary hover:text-foreground"}`}>
              {t.nav[id]}
            </button>
          ))}
        </nav>
      </header>
      <main className="mx-auto max-w-[1600px] px-4 py-6 md:px-6">
        {tab === "overview" && <Overview onScenario={openScenario} />}
        {tab === "stress" && <StressTest key={preset ?? "base"} initialPreset={preset} />}
        {tab === "fs" && <Statements />}
        {tab === "stats" && <Diagnostics />}
        {tab === "dossier" && <Dossier />}
      </main>
      <footer className="border-t">
        <p className="mx-auto max-w-[1600px] px-4 py-4 text-[10px] leading-relaxed text-muted-foreground md:px-6">{t.footer}</p>
      </footer>
    </div>
  );
}
