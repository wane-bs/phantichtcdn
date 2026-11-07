const vi = {
  header: { company: "Tá»ng cÃ´ng ty HÃ ng khÃ´ng Viá»t Nam", subtitle: "Ná»n táº£ng PhÃ¢n tÃ­ch TÃ i chÃ­nh & Kiá»m Äá»nh Sá»©c chá»u Äá»±ng", data: "Dá»¯ liá»u: Kiá»m toÃ¡n FY2020-FY2024" },
  nav: { overview: "Tá»ng quan Äiá»u hÃ nh C-Suite", stress: "MÃ´ phá»ng CÃº sá»c VÄ© mÃ´", fs: "BÃ¡o cÃ¡o TÃ i chÃ­nh & Ratios", stats: "Kiá»m Äá»nh Kinh táº¿ lÆ°á»£ng", dossier: "Há» sÆ¡ TÃ¡i cÆ¡ cáº¥u" },
  kpi: {
    revenue: "Doanh thu thuáº§n (FY2024)", revenueBadge: "+15.7% so vá»i cÃ¹ng ká»³", revenueNote: "Kiá»m toÃ¡n, há»£p nháº¥t",
    ebit: "EBIT", ebitBadge: "Phá»¥c há»i +", ebitNote: "so vá»i -6,120 nÄm FY2022",
    equity: "Vá»n chá»§ sá» há»¯u (Ãm)", equityBadge: "Ãm vá»n chá»§", equityNote: "Theo dÃµi kháº£ nÄng hoáº¡t Äá»ng liÃªn tá»¥c",
    dol: "ÄÃ²n báº©y kinh doanh DOL", dolBadge: "ÄÃ²n báº©y cao", dolNote: "%ÎEBIT / %ÎDoanh thu",
    runway: "Thá»i gian tá»n táº¡i thanh khoáº£n (Runway)", runwayBadge: "Äá»m má»ng", runwayNote: "Tiá»n 4,627 B / chi tiÃªu thÃ¡ng", months: "ThÃ¡ng",
  },
  briefing: {
    title: "Báº£n tin Äiá»u hÃ nh", subtitle: "TÃ³m táº¯t cho Ban Tá»ng GiÃ¡m Äá»c Â· FY2024",
    alertTitle: "Cáº£nh bÃ¡o kháº£ nÄng thanh toÃ¡n", alertBody: "Vá»n chá»§ sá» há»¯u Ã¢m -9,344 B VND Â· Ná»£ pháº£i tráº£ / Tá»ng tÃ i sáº£n",
    health: "TÃ¬nh tráº¡ng", critical: "NghiÃªm trá»ng", watch: "Theo dÃµi", healthy: "LÃ nh máº¡nh",
    recTitle: "3 Khuyáº¿n nghá» Chiáº¿n lÆ°á»£c",
    recs: [
      "Äáº©y nhanh tÄng vá»n vÃ  tÃ¡i cáº¥p vá»n cÃ³ báº£o lÃ£nh NhÃ  nÆ°á»c Äá» khÃ´i phá»¥c vá»n chá»§ dÆ°Æ¡ng.",
      "PhÃ²ng ngá»«a rá»§i ro giÃ¡ Jet A-1 â nhiÃªn liá»u chiáº¿m 35.8% doanh thu.",
      "TÃ¡i cáº¥u trÃºc khoáº£n ná»£/thuÃª báº±ng USD ($1.8B) sang VND hoáº·c phÃ²ng ngá»«a tá»± nhiÃªn.",
    ],
  },
  gauge: { title: "Äá»ng há» Runway Thanh khoáº£n", cash: "Tiá»n & ÄTNH", burn: "Chi tiÃªu/thÃ¡ng", months: "thÃ¡ng" },
  presetsCard: { title: "Ká»ch báº£n Nhanh", subtitle: "Nháº¥n Äá» má» trong MÃ´ phá»ng CÃº sá»c", ebit: "EBIT sau cÃº sá»c" },
  overview: { chartTitle: "Doanh thu vs EBIT Â· CÆ¡ cáº¥u chi phÃ­ theo quÃ½", chartSub: "Q1'23 â Q4'24 Â· Tá»· VND", fuelShare: "Tá»¶ TRá»NG NHIÃN LIá»U/DT", fuel: "NhiÃªn liá»u Jet A-1", leasing: "ThuÃª tÃ u bay", personnel: "NhÃ¢n sá»±", revenue: "Doanh thu", ebitR: "EBIT (P)" },
  dupont: { title: "PhÃ¢n tÃ­ch DuPont 5 bÆ°á»c", sub: "FY2024 Â· Há»£p nháº¥t", distorted: "ROE Bá» BIáº¾N Dáº NG", tax: "GÃ¡nh náº·ng thuáº¿", interest: "GÃ¡nh náº·ng lÃ£i vay", margin: "BiÃªn EBIT", turnover: "VÃ²ng quay tÃ i sáº£n", multiplier: "Há» sá» nhÃ¢n vá»n", roa: "ROA (hoáº¡t Äá»ng)", roe: "ROE (bÃ¡o cÃ¡o)", note: "Vá»n chá»§ Ã¢m Äáº£o dáº¥u há» sá» nhÃ¢n: LNST dÆ°Æ¡ng hiá»n thá» thÃ nh ROE Ã¢m. HÃ£y dÃ¹ng ROA vÃ  ROIC Äá» ÄÃ¡nh giÃ¡ hiá»u quáº£." },
  scenarios: { base: "Ká»ch báº£n CÆ¡ sá»", mideast: "CÃº sá»c Dáº§u Trung ÄÃ´ng ($125)", vnd: "PhÃ¡ giÃ¡ VND (26,500)", worst: "Ká»ch báº£n Xáº¥u nháº¥t", live: "Thá» trÆ°á»ng HÃ´m nay" },
  mode: { label: "Cháº¿ Äá»", audited: "BCTC Kiá»m toÃ¡n", live: "Thá» trÆ°á»ng HÃ´m nay", engaged: "ToÃ n bá» ná»n táº£ng ÄÃ£ chuyá»n sang Thá» trÆ°á»ng HÃ´m nay" },
  market: { sync: "Cáº­p nháº­t Dá»¯ liá»u Thá» trÆ°á»ng", syncing: "Äang Äá»ng bá»â¦", synced: "Dá»¯ liá»u thá» trÆ°á»ng ÄÃ£ Äá»ng bá»", viewToday: "Xem ká»ch báº£n hÃ´m nay", lastSync: "Äá»ng bá» lÃºc", jet: "Jet A-1" },
  solvency: { SAFE: "AN TOÃN", CAUTION: "THáº¬N TRá»NG", "CRITICAL DISTRESS": "KHá»¦NG HOáº¢NG NGHIÃM TRá»NG" },
  solvencyMsg: { SAFE: "EBIT â¥ 4,000 B VND Â· Kháº£ nÄng tráº£ ná»£ ÄÆ°á»£c báº£o toÃ n", CAUTION: "0 â¤ EBIT < 4,000 B VND Â· DÆ° Äá»a cam káº¿t vay Äang thu háº¹p", "CRITICAL DISTRESS": "EBIT < 0 Â· Lá» hoáº¡t Äá»ng, cáº§n há» trá»£ NhÃ  nÆ°á»c" },
  stress: {
    stressedEbit: "EBIT sau cÃº sá»c", inputs: "Biáº¿n sá» VÄ© mÃ´", fuel: "GiÃ¡ nhiÃªn liá»u Jet A-1", fx: "Tá»· giÃ¡ USD/VND", lf: "Há» sá» sá»­ dá»¥ng gháº¿", base: "cÆ¡ sá»",
    waterfall: "PhÃ¢n rÃ£ tÃ¡c Äá»ng EBIT Â· Tá»· VND", baseline: "EBIT cÆ¡ sá»", fuelShock: "CÃº sá»c nhiÃªn liá»u", fxLoss: "Lá» tá»· giÃ¡ ná»£", demand: "Hiá»u á»©ng cáº§u", final: "EBIT sau cÃº sá»c",
    gauge: "Äá»ng há» kháº£ nÄng thanh toÃ¡n", runway: "Runway thanh khoáº£n", delta: "Î so vá»i cÆ¡ sá»", mo: "th",
    runwayNote: "Runway = 4,627 B tiá»n (kiá»m toÃ¡n FY2024) Ã· (chi tiÃªu thÃ¡ng cÆ¡ sá» â ÎEBIT/12).",
  },
  heatmap: { title: "Ma tráº­n Äá» nháº¡y 2D Â· EBIT (Tá»· VND)", sub: "GiÃ¡ Jet A-1 ($/thÃ¹ng) Ã Tá»· giÃ¡ USD/VND Â· Há» sá» gháº¿ giá»¯ á» 79.5%", fuel: "NhiÃªn liá»u â / Tá»· giÃ¡ â", current: "Ã gáº§n vá» trÃ­ thanh trÆ°á»£t hiá»n táº¡i" },
  fs: {
    title: "TrÃ¬nh khÃ¡m phÃ¡ BÃ¡o cÃ¡o TÃ i chÃ­nh Â· Há»£p nháº¥t kiá»m toÃ¡n", absolute: "Tuyá»t Äá»i (Tá»· VND)", yoy: "TÄng trÆ°á»ng YoY (%)", common: "Quy mÃ´ chung (%)",
    item: "Khoáº£n má»¥c", revenue: "Doanh thu thuáº§n", grossProfit: "Lá»£i nhuáº­n gá»p", assets: "Tá»ng tÃ i sáº£n", liabilities: "Ná»£ pháº£i tráº£", equity: "Vá»n chá»§ sá» há»¯u", cash: "Tiá»n & ÄTNH",
    grossMargin: "BiÃªn lá»£i nhuáº­n gá»p", la: "Ná»£ / Tá»ng tÃ i sáº£n",
    yoyNote: "YoY = (ká»³ nÃ y â ká»³ trÆ°á»c) / |ká»³ trÆ°á»c|. * = ká»³ gá»c Ã¢m, Ã½ nghÄ©a háº¡n cháº¿.", commonNote: "Khoáº£n má»¥c KQKD tÃ­nh theo % doanh thu; khoáº£n má»¥c CÄKT tÃ­nh theo % tá»ng tÃ i sáº£n.",
  },
  diag: {
    title: "Báº£ng Äiá»u khiá»n TÃ­nh toÃ n váº¹n Kinh táº¿ lÆ°á»£ng", adf: "Kiá»m Äá»nh ADF (tÃ­nh dá»«ng)", coint: "Kiá»m Äá»nh Äá»ng liÃªn káº¿t â ln(TC) vs ln(Doanh thu)", sloan: "PhÃ¢n tÃ­ch Dá»n tÃ­ch Sloan",
    pass: "Äáº T", caution: "THáº¬N TRá»NG", anomaly: "Báº¤T THÆ¯á»NG",
    fx: "Tá»· giÃ¡ (USD/VND)", tc: "Tá»ng chi phÃ­", oil: "GiÃ¡ dáº§u (Jet A-1)",
    fxNote: "Dá»«ng á» sai phÃ¢n báº­c 1 â há»£p lá» cho mÃ´ hÃ¬nh sai phÃ¢n", tcNote: "Dá»«ng á» sai phÃ¢n báº­c 1", oilNote: "KhÃ´ng dá»«ng á» má»©c gá»c â cáº§n láº¥y sai phÃ¢n trÆ°á»c khi mÃ´ hÃ¬nh hÃ³a",
    cointNote: "KhÃ´ng phÃ¡t hiá»n Äá»ng liÃªn káº¿t. Rá»§i ro há»i quy giáº£ máº¡o náº¿u mÃ´ hÃ¬nh á» má»©c gá»c mÃ  khÃ´ng láº¥y sai phÃ¢n.",
    sloanVal: "PhÃ¡t hiá»n báº¥t thÆ°á»ng", sloanNote: "Báº¥t thÆ°á»ng dá»n tÃ­ch do Äiá»u chá»nh lá»n tá»« thuÃª hoáº¡t Äá»ng tÃ u bay (chuyá»n Äá»i IFRS 16 / VAS).",
  },
  dossier: [
    ["CÆ¡ cáº¥u sá» há»¯u", "NhÃ  nÆ°á»c (CMSC ~86%), ANA Holdings lÃ  cá» ÄÃ´ng chiáº¿n lÆ°á»£c ~5.6%."],
    ["TÃ¡i cÆ¡ cáº¥u", "Káº¿ hoáº¡ch tÄng vá»n vÃ  tÃ¡i cáº¥p vá»n cÃ³ NhÃ  nÆ°á»c há» trá»£ nháº±m khÃ´i phá»¥c vá»n chá»§ dÆ°Æ¡ng vÃ o FY2026."],
    ["Rá»§i ro chÃ­nh", "Biáº¿n Äá»ng giÃ¡ Jet A-1, nghÄ©a vá»¥ thuÃª báº±ng USD, Äá»i A321neo bá» dá»«ng bay do Äá»ng cÆ¡ Pratt & Whitney."],
    ["Äá»ng lá»±c", "Phá»¥c há»i khÃ¡ch quá»c táº¿ (Trung Quá»c, ÄÃ´ng Báº¯c Ã), tá»i Æ°u Äá»i bay, lá»£i suáº¥t hÃ ng hÃ³a."],
  ] as [string, string][],
  footer: "TUYÃN Bá» MIá»N TRá»ª NGHIÃN Cá»¨U Há»C THUáº¬T & PHÃN TÃCH Äá»NH LÆ¯á»¢NG: Ná»n táº£ng nÃ y ÄÆ°á»£c phÃ¡t triá»n nghiÃªm ngáº·t cho nghiÃªn cá»©u thá»±c nghiá»m vÃ  trÃ¬nh diá»n giÃ¡o dá»¥c táº¡i NghiÃªn Connect #6. KhÃ´ng cáº¥u thÃ nh tÆ° váº¥n hay chÃ o má»i Äáº§u tÆ°.",
};
export type Dict = typeof vi;

const en: Dict = {
  header: { company: "Vietnam Airlines JSC", subtitle: "Financial Intelligence & Quantitative Stress-Testing Platform", data: "Data: Audited FY2020-FY2024" },
  nav: { overview: "Executive C-Suite Overview", stress: "Macro Stress-Testing Simulator", fs: "Financial Statements & Ratios", stats: "Econometric Diagnostics", dossier: "Restructuring Dossier" },
  kpi: {
    revenue: "Net Revenue (FY2024)", revenueBadge: "+15.7% YoY", revenueNote: "Audited, consolidated",
    ebit: "Operating EBIT", ebitBadge: "Turnaround +", ebitNote: "vs. -6,120 in FY2022",
    equity: "Owner's Equity (Negative)", equityBadge: "Negative Equity", equityNote: "Going-concern watchlist",
    dol: "Operating Leverage DOL", dolBadge: "High Leverage", dolNote: "%ÎEBIT / %ÎRevenue",
    runway: "Liquidity Runway", runwayBadge: "Low Buffer", runwayNote: "Cash 4,627 B / monthly burn", months: "Months",
  },
  briefing: {
    title: "Executive Briefing", subtitle: "Board summary Â· FY2024",
    alertTitle: "Solvency Alert", alertBody: "Owner's equity -9,344 B VND Â· Liabilities / Total assets",
    health: "Health", critical: "Critical", watch: "Watch", healthy: "Healthy",
    recTitle: "3 Strategic Recommendations",
    recs: [
      "Accelerate the capital increase and state-backed refinancing to restore positive equity.",
      "Hedge Jet A-1 exposure â fuel is 35.8% of revenue.",
      "Refinance USD lease/debt exposure ($1.8B) into VND or a natural hedge.",
    ],
  },
  gauge: { title: "Liquidity Runway Countdown", cash: "Cash & ST Inv.", burn: "Monthly burn", months: "months" },
  presetsCard: { title: "Quick Scenarios", subtitle: "Click to open in the Stress Simulator", ebit: "Stressed EBIT" },
  overview: { chartTitle: "Revenue vs EBIT Â· Quarterly Cost Structure", chartSub: "Q1'23 â Q4'24 Â· B VND", fuelShare: "FUEL SHARE OF REV", fuel: "Fuel Jet A-1", leasing: "Aircraft Leasing", personnel: "Personnel", revenue: "Revenue", ebitR: "EBIT (R)" },
  dupont: { title: "DuPont 5-Stage Decomposition", sub: "FY2024 Â· Consolidated", distorted: "ROE DISTORTED", tax: "Tax Burden", interest: "Interest Burden", margin: "EBIT Margin", turnover: "Asset Turnover", multiplier: "Equity Multiplier", roa: "ROA (operating)", roe: "ROE (reported)", note: "Negative book equity inverts the multiplier: positive NPAT shows as negative ROE. Use ROA and ROIC for performance." },
  scenarios: { base: "Base Case", mideast: "Middle East Oil Shock ($125)", vnd: "VND Devaluation (26,500)", worst: "Worst Case Scenario", live: "Today's Live Market" },
  mode: { label: "View", audited: "Audited FY2024", live: "Live Market", engaged: "Entire platform switched to Live Market view" },
  market: { sync: "Sync Live Market", syncing: "Syncingâ¦", synced: "Market data synchronized", viewToday: "View today's scenario", lastSync: "Last sync", jet: "Jet A-1" },
  solvency: { SAFE: "SAFE", CAUTION: "CAUTION", "CRITICAL DISTRESS": "CRITICAL DISTRESS" },
  solvencyMsg: { SAFE: "EBIT â¥ 4,000 B VND Â· Debt service capacity intact", CAUTION: "0 â¤ EBIT < 4,000 B VND Â· Covenant headroom eroding", "CRITICAL DISTRESS": "EBIT < 0 Â· Operating loss, state support required" },
  stress: {
    stressedEbit: "Stressed EBIT", inputs: "Macro Inputs", fuel: "Jet A-1 Fuel Price", fx: "USD/VND Exchange Rate", lf: "Passenger Load Factor", base: "base",
    waterfall: "EBIT Impact Waterfall Â· B VND", baseline: "Baseline EBIT", fuelShock: "Fuel Shock", fxLoss: "FX Debt Loss", demand: "Demand Effect", final: "Stressed EBIT",
    gauge: "Solvency Gauge", runway: "Liquidity Runway", delta: "Î vs Base", mo: "mo",
    runwayNote: "Runway = 4,627 B cash (audited FY2024) Ã· (base monthly burn â ÎEBIT/12).",
  },
  heatmap: { title: "2D Sensitivity Heatmap Â· EBIT (B VND)", sub: "Jet A-1 ($/bbl) Ã USD/VND Â· Load factor held at 79.5%", fuel: "Fuel â / FX â", current: "Cell nearest current slider position" },
  fs: {
    title: "Financial Statements Explorer Â· Audited Consolidated", absolute: "Absolute (B VND)", yoy: "YoY Growth (%)", common: "Common-size (%)",
    item: "Line item", revenue: "Net Revenue", grossProfit: "Gross Profit", assets: "Total Assets", liabilities: "Total Liabilities", equity: "Owner's Equity", cash: "Cash & ST Inv.",
    grossMargin: "Gross Margin", la: "Liabilities / Assets",
    yoyNote: "YoY = (current â prior) / |prior|. * = negative base, limited meaning.", commonNote: "P&L lines as % of revenue; balance-sheet lines as % of total assets.",
  },
  diag: {
    title: "Econometric Integrity Console", adf: "Augmented Dickey-Fuller Stationarity", coint: "Cointegration Test â ln(TC) vs ln(Revenue)", sloan: "Sloan Accruals Analysis",
    pass: "PASS", caution: "CAUTION", anomaly: "ANOMALY",
    fx: "FX Rate (USD/VND)", tc: "Total Cost", oil: "Oil Price (Jet A-1)",
    fxNote: "1st difference stationary â valid for differenced modeling", tcNote: "1st difference stationary", oilNote: "Non-stationary at level â difference before modeling",
    cointNote: "No cointegration detected. Spurious regression risk if modeled in levels without differencing.",
    sloanVal: "Anomaly Detected", sloanNote: "Accruals anomaly driven by heavy aircraft operating lease adjustments (IFRS 16 / VAS transition).",
  },
  dossier: [
    ["Ownership", "State-owned (CMSC ~86%), ANA Holdings strategic stake ~5.6%."],
    ["Restructuring", "Capital increase plan and state-backed refinancing to restore positive equity by FY2026."],
    ["Key Risks", "Jet A-1 price exposure, USD-denominated leases, Pratt & Whitney engine groundings on A321neo fleet."],
    ["Catalysts", "International traffic recovery (China, NE Asia), fleet optimization, cargo yields."],
  ],
  footer: "ACADEMIC RESEARCH & QUANTITATIVE ANALYSIS DISCLAIMER: This platform is developed strictly for empirical research and educational demonstrations at NghiÃªn Connect #6. Does not constitute investment advice or solicitation.",
};

export const dictionaries = { vi, en };
export type Lang = keyof typeof dictionaries;
