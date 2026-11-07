import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { BASE } from "@/lib/stress-model";
import { LIVE_MARKET, syncMarket } from "@/lib/market-feed";
import { computeImpact, type Impact } from "@/lib/live-impact";

type Market = typeof LIVE_MARKET;
type Ctx = {
  isLiveMode: boolean; setLiveMode: (v: boolean) => void; toggleLiveMode: () => void;
  market: Market; syncedAt: Date | null; syncing: boolean; sync: () => Promise<void>;
  impact: Impact; baseImpact: Impact; view: Impact;
};
const MarketCtx = createContext<Ctx | null>(null);
const baseImpact = computeImpact({ fuel: BASE.fuel, fx: BASE.fx, lf: BASE.lf });

export function MarketProvider({ children }: { children: ReactNode }) {
  const [isLiveMode, setLiveMode] = useState(false);
  const [market, setMarket] = useState<Market>(LIVE_MARKET);
  const [syncedAt, setSyncedAt] = useState<Date | null>(null);
  const [syncing, setSyncing] = useState(false);
  useEffect(() => setSyncedAt(new Date()), []);
  const impact = useMemo(() => computeImpact(market), [market]);
  const toggleLiveMode = useCallback(() => setLiveMode((v) => !v), []);
  const sync = useCallback(async () => {
    setSyncing(true);
    const r = await syncMarket();
    setMarket({ fuel: r.fuel, fx: r.fx, lf: r.lf });
    setSyncedAt(r.syncedAt);
    setSyncing(false);
    setLiveMode(true);
  }, []);
  const value = useMemo(() => ({ isLiveMode, setLiveMode, toggleLiveMode, market, syncedAt, syncing, sync, impact, baseImpact, view: isLiveMode ? impact : baseImpact }), [isLiveMode, toggleLiveMode, market, syncedAt, syncing, sync, impact]);
  return <MarketCtx.Provider value={value}>{children}</MarketCtx.Provider>;
}

export function useMarket() {
  const c = useContext(MarketCtx);
  if (!c) throw new Error("useMarket must be used within MarketProvider");
  return c;
}
