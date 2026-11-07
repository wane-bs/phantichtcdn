import { RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { useI18n } from "@/i18n/LanguageProvider";
import { marketDeltas } from "@/lib/market-feed";
import { useMarket } from "@/context/MarketContext";

export function MarketSync({ onViewToday }: { onViewToday: () => void }) {
  const { t, lang } = useI18n();
  const m = t.market;
  const { market, syncedAt, syncing, sync } = useMarket();
  const d = marketDeltas(market);
  const time = syncedAt ? syncedAt.toLocaleTimeString(lang === "vi" ? "vi-VN" : "en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit" }) : "â";

  const onSync = async () => {
    await sync();
    toast.success(m.synced, { description: t.mode.engaged, action: { label: m.viewToday, onClick: onViewToday } });
  };

  return (
    <div className="flex items-center gap-2">
      <div className="num hidden items-center gap-3 rounded-full border bg-panel/60 px-3 py-1 text-[11px] xl:flex" aria-live="polite">
        <span>{m.jet} <b className="text-foreground">${market.fuel.toFixed(1)}</b> <span className={d.fuel > 0 ? "text-loss" : "text-gain"}>({d.fuel > 0 ? "+" : "â"}{Math.abs(d.fuel).toFixed(1)})</span></span>
        <span className="text-muted-foreground">Â·</span>
        <span>USD/VND <b className="text-foreground">{market.fx.toLocaleString("en-US")}</b> <span className={d.fx > 0 ? "text-loss" : "text-gain"}>({d.fx > 0 ? "+" : "â"}{Math.abs(d.fx)})</span></span>
        <span className="text-muted-foreground">Â· {m.lastSync} {time}</span>
      </div>
      <button onClick={onSync} disabled={syncing} aria-label={m.sync}
        className="inline-flex items-center gap-1.5 rounded-full border border-primary/50 bg-primary/15 px-3 py-1 text-[11px] font-semibold text-primary transition-colors hover:bg-primary/25 disabled:opacity-70">
        <RefreshCw className={`h-3.5 w-3.5 ${syncing ? "animate-spin" : ""}`} />
        <span className="hidden sm:inline">{syncing ? m.syncing : m.sync}</span>
      </button>
    </div>
  );
}
