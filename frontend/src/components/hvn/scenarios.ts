import { LIVE_MARKET } from "@/lib/market-feed";

export type ScenarioId = "base" | "mideast" | "vnd" | "worst" | "live";
export const presets: { id: ScenarioId; fuel: number; fx: number; lf: number }[] = [
  { id: "base", fuel: 101, fx: 25690, lf: 79.5 },
  { id: "mideast", fuel: 125, fx: 25690, lf: 79.5 },
  { id: "vnd", fuel: 101, fx: 26500, lf: 79.5 },
  { id: "worst", fuel: 140, fx: 27000, lf: 65 },
  { id: "live", ...LIVE_MARKET },
];
