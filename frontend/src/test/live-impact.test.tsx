import { describe, expect, it } from "vitest";
import { act, renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { computeImpact } from "@/lib/live-impact";
import { LIVE_MARKET } from "@/lib/market-feed";
import { MarketProvider, useMarket } from "@/context/MarketContext";

describe("live market impact", () => {
  const r = computeImpact(LIVE_MARKET);
  it("EBIT 3,410, delta â3,021 (â47%)", () => {
    expect(Math.round(r.ebit)).toBe(3410);
    expect(Math.round(r.delta)).toBe(-3021);
    expect(Math.round(r.deltaPct)).toBe(-47);
  });
  it("EBIT margin 3.22% and ROA 4.02%", () => {
    expect(r.ebitMargin.toFixed(2)).toBe("3.22");
    expect(r.roa.toFixed(2)).toBe("4.02");
  });
  it("fuel cost +3,210 B, fuel share 38.8%", () => {
    expect(Math.round(r.extraFuelCost)).toBe(3210);
    expect(r.fuelShare.toFixed(1)).toBe("38.8");
  });
  it("runway 3.4 months, CAUTION, shock exceeds 2-sigma", () => {
    expect(r.runway.toFixed(1)).toBe("3.4");
    expect(r.solvency).toBe("CAUTION");
    expect(r.exceedsThreshold).toBe(true);
  });
});

describe("MarketContext", () => {
  const wrapper = ({ children }: { children: ReactNode }) => <MarketProvider>{children}</MarketProvider>;
  it("starts audited, sync engages live mode, toggle returns to audited", async () => {
    const { result } = renderHook(() => useMarket(), { wrapper });
    expect(result.current.isLiveMode).toBe(false);
    expect(Math.round(result.current.view.ebit)).toBe(6431);
    await act(() => result.current.sync());
    expect(result.current.isLiveMode).toBe(true);
    expect(Math.round(result.current.view.ebit)).toBe(3410);
    act(() => result.current.toggleLiveMode());
    expect(result.current.isLiveMode).toBe(false);
  });
});
