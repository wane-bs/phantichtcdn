import { describe, expect, it } from "vitest";
import { runStress } from "@/lib/stress-model";
import { LIVE_MARKET, marketDeltas } from "@/lib/market-feed";

describe("live market preset", () => {
  it("Jet A-1 $116.3 and FX 25,585 give EBIT â 3,410 (CAUTION) and 3.4 months runway", () => {
    const r = runStress(LIVE_MARKET.fuel, LIVE_MARKET.fx, LIVE_MARKET.lf);
    expect(r.ebit).toBeCloseTo(3410.1, 0);
    expect(r.solvency).toBe("CAUTION");
    expect(r.runway.toFixed(1)).toBe("3.4");
  });
  it("deltas vs baseline are +15.3 and â105", () => {
    expect(marketDeltas()).toEqual({ fuel: 15.3, fx: -105 });
  });
});
