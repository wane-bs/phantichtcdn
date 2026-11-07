import { describe, expect, it } from "vitest";
import { runStress } from "@/lib/stress-model";

describe("stress model", () => {
  it("base case returns 6,431 EBIT and ~4.2 months runway on audited cash of 4,627", () => {
    const r = runStress(101, 25690, 79.5);
    expect(r.ebit).toBeCloseTo(6431);
    expect(r.runway).toBeCloseTo(4627 / (9210 / 8.4));
    expect(r.solvency).toBe("SAFE");
  });
  it("fuel at $125 costs (24 * 8.2M * 25,690)/1e9 B VND", () => {
    expect(runStress(125, 25690, 79.5).fuelImpact).toBeCloseTo(-(24 * 8.2e6 * 25690) / 1e9);
  });
  it("FX at 26,500 loses 1.8B * 810 / 1e9 on debt", () => {
    expect(runStress(101, 26500, 79.5).fxImpact).toBeCloseTo(-1458);
  });
  it("load factor +1pt adds 850 B VND", () => {
    expect(runStress(101, 25690, 80.5).demandImpact).toBeCloseTo(850);
  });
  it("solvency thresholds: >=4000 safe, 0..4000 caution, <0 distress", () => {
    expect(runStress(101, 25690, 76.5).solvency).toBe("CAUTION"); // 3881
    expect(runStress(140, 27000, 65).solvency).toBe("CRITICAL DISTRESS");
  });
});
