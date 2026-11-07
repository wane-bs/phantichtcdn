import { describe, expect, it } from "vitest";
import { commonSize, yoy } from "@/lib/statement-views";

describe("statement views", () => {
  it("FY2024 revenue YoY is +15.7%", () => {
    expect(yoy(105942, 91540)!).toBeCloseTo(15.73, 1);
  });
  it("first year has no YoY", () => {
    expect(yoy(40538, undefined)).toBeNull();
  });
  it("negative base: equity -17,026 -> -9,344 reads as improvement (+45.1%)", () => {
    expect(yoy(-9344, -17026)!).toBeCloseTo(45.12, 1);
  });
  it("FY2024 equity common-size is -16.1% of total assets", () => {
    expect(commonSize(-9344, "bs", { revenue: 105942, assets: 58187 })).toBeCloseTo(-16.06, 1);
  });
  it("FY2024 gross profit common-size is 13.1% of revenue", () => {
    expect(commonSize(13902, "pl", { revenue: 105942, assets: 58187 })).toBeCloseTo(13.12, 1);
  });
});
