# Platform-wide Live Market Mode

## Numbers check (all match your spec)
Using the existing stress model unchanged, with Jet A-1 $116.3, FX 25,585, LF 79.5:
- EBIT 3,410 B VND (â3,021, â47.0%), CAUTION, runway 3.4 months
- EBIT margin 3,410 / 105,942 = 3.22%; ROA (same tax 0.886 and interest 0.774 ratios) = 4.02%
- Fuel share: 35.8% of revenue + 3,210 B = 38.8% (revenue held at audited 105,942)

## Assumptions to confirm
1. **2-sigma fuel threshold:** there is no historical oil price series in the app. I will add a documented constant (annual Jet A-1 std. dev. approx. $7/bbl, so 2-sigma is approx. $14) clearly labelled as an assumption. Send me the real sigma if you have one.
2. **"AI" recommendations** are rule-based (picked from shock size: fuel, FX, runway) and carry an "AI-assisted" badge. No external AI call. Tell me if you want real AI generation (Lovable AI) instead.
3. Live mode starts **off** on every page load (Audited FY2024 by default). Audited figures are never overwritten; live values show alongside them.

## What you will see
- **Header:** a two-part pill toggle "Cháº¿ Äá»: BCTC Kiá»m toÃ¡n | Thá» trÆ°á»ng HÃ´m nay" / "View: Audited FY2024 | Live Market", next to the existing sync button and ticker. Clicking sync turns Live mode on everywhere and shows the toast.
- **Overview:** EBIT card shows 3,410 (amber, â3,021 B); Runway card shows 3.4 months (rose). Briefing alert says the $116.3 oil shock compresses EBIT by 47%, plus 3 live recommendations with the badge. Gauge needle animates to 3.4. DuPont shows 3.22% margin, 4.02% ROA. Chart highlights the extra fuel cost (+3,210 B) and fuel share 38.8%.
- **Financial Statements:** extra column "FY2024 (Stressed Live)" beside FY2024, with the variance highlighted.
- **Diagnostics:** new "Live Market Shock Test" card flagging +$15.3/bbl above the 2-sigma threshold.
- **Simulator:** when Live mode is turned on, the sliders jump to the live preset.
- Turning Live mode off restores every screen to the audited view.

## Technical details
- `src/lib/live-impact.ts` (new, pure): `computeLiveImpact(market)` returns ebit, delta, deltaPct, runway, solvency, ebitMargin, roa, extraFuelCost, fuelShare, shockSigma, exceedsThreshold, and recommendation keys. Uses `runStress` and `BASE`; `stress-model.ts` and `data.ts` stay untouched.
- `src/context/MarketContext.tsx` (new): `MarketProvider` with `isLiveMode`, `setLiveMode`, `toggleLiveMode`, `market`, `syncedAt`, `sync()`, `impact` (memoized). Mounted in `__root.tsx` inside `LanguageProvider`. `useMarket()` hook.
- `MarketSync.tsx`: reads from context; `sync()` sets live mode and fires the toast. New `ModeToggle.tsx` pill (`role="radiogroup"`, keyboard-accessible).
- Widgets that read `useMarket()`: `Overview.tsx` (KPIs, DuPont, chart reference line/annotation), `ExecutiveBriefing.tsx`, `RunwayGauge.tsx` (CSS transform transition approx. 250ms), `OtherTabs.tsx` (extra statement column and shock test card), `StressTest.tsx` (applies live preset on activation).
- `dictionary.ts`: new `mode`, `live` groups (alerts, recs x3, AI badge, column header, shock test text), VI and EN.
- Speed: everything is synchronous memoized maths; no network, so it is well under 300ms (sync still keeps its 0.5s spin by design; tell me if the spin should be shortened).
- Tests: `src/test/live-impact.test.ts` checks EBIT 3,410, delta â3,021, â47%, margin 3.22%, ROA 4.02%, fuel share 38.8%, runway 3.4, CAUTION, threshold exceeded; plus a context test that `sync()` turns Live mode on and toggle turns it off. Existing tests unchanged.
