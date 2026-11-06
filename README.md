# PHÂN TÍCH TÀI CHÍNH DOANH NGHIỆP — VIETNAM AIRLINES (HVN)
> **Enterprise Financial Intelligence & Quantitative Stress-Testing Platform**  
> Dự án tham gia sự kiện: **Nghiên Connect #6 — "From Lovable to Buildable"** (Nhóm 2: Vibe Code Sprint & Showcase Battle)

---

## ⚖️ LEGAL & ACADEMIC DISCLAIMER (TUYÊN BỐ MIỄN TRỪ TRÁCH NHIỆM)

> [!IMPORTANT]
> **MỤC ĐÍCH NGHIÊN CỨU & HỌC THUẬT:**  
> Hệ thống này được phát triển hoàn toàn vì mục đích **học thuật, nghiên cứu khoa học dữ liệu tài chính doanh nghiệp và trình diễn năng lực Vibe Coding / Full-stack AI Engineering** tại sự kiện công nghệ cộng đồng Nghiên AI (Nghiên Connect #6).
>
> 1. **Không phải lời khuyên đầu tư:** Toàn bộ nội dung, chỉ số phân tích, mô hình dự báo, kết quả kiểm định thống kê và các kịch bản mô phỏng độ nhạy ($DOL, BEP$, Giá dầu Jet A-1, Tỷ giá USD/VND) trong dự án này **tuyệt đối không cấu thành lời khuyên đầu tư, khuyến nghị mua/bán, hoặc chào mời giao dịch cổ phiếu HVN hay bất kỳ tài sản tài chính nào**.
> 2. **Nguồn dữ liệu công khai:** Hệ thống chỉ sử dụng các nguồn dữ liệu công khai minh bạch (Báo cáo tài chính đã kiểm toán công bố của Tổng công ty Hàng không Việt Nam — CTCP, dữ liệu lịch sử từ SSI, và chuỗi thời gian vĩ mô mở từ Yahoo Finance / ExchangeRate API).
> 3. **Bảo mật & Zero-Trust:** Dự án không chứa bất kỳ thông tin nội bộ không công khai (MNPI), không hardcode bất kỳ khóa API bí mật hoặc mật khẩu nhạy cảm nào trong mã nguồn.

---

## 🏛️ KIẾN TRÚC HỆ THỐNG (CLEAN ARCHITECTURE)

Hệ thống được thiết kế theo mô hình tách biệt hoàn toàn giữa Tầng tính toán định lượng cục bộ và Tầng hiển thị tương tác đám mây:

```
[ Local Environment: ThinkPad / Debian ]
  └── uv & Python Data Engine (Stage 1 - Stage 5)
        ├── Clean & Validate Data (SSI BCTC, Jet Fuel, FX)
        ├── Core Formulas (DOL, DFL, BEP, DuPont, VaR, Stress-Testing)
        └── Statistical Diagnostics (ADF, Granger Causality, Sloan Accruals)
                 │
                 ▼ (Model Context Protocol: https://mcp.lovable.dev)
[ Cloud Environment: Lovable Pro ]
  └── Modern FinTech Frontend (React + TypeScript + Tailwind + Tremor)
        ├── Executive C-Suite Dashboard
        ├── Scenario & Macro Stress-Testing Simulator (Sliders)
        ├── Interactive Financial Statements & Ratio Drill-down
        └── Dynamic Research Report Viewer (Markdown + Charts)
```

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT & VẬN HÀNH NHANH (QUICK START)

### 1. Khởi tạo môi trường ảo bằng `uv`
```bash
# Đồng bộ môi trường và dependencies trong 1 giây
uv sync
```

### 2. Chạy Pipeline Tính toán Cốt lõi
```bash
# Chạy đầy đủ 6 giai đoạn (Ingestion -> Calculations -> Diagnostics -> Forecaster -> Reports)
PYTHONPATH=src uv run python src/pipeline_runner.py
```

### 3. Kích hoạt Crawlers Cập nhật Dữ liệu Vĩ mô
```bash
# Cập nhật giá dầu Brent/Jet A-1 và tỷ giá USD/VND mới nhất
uv run python scripts/crawlers/macro_crawler.py
```

### 4. Kết nối Lovable MCP Server
```bash
# Kích hoạt kết nối OAuth với Lovable Pro
npx -y mcp-remote https://mcp.lovable.dev
```

---

## 📂 CẤU TRÚC THƯ MỤC CHUẨN HÓA

```
phantichtcdn/
├── .agents/                 # Cấu hình MCP server cục bộ (.agents/mcp_config.json)
├── .github/workflows/       # GitHub Actions CI/CD bots (ci_pipeline_check, daily_market_update)
├── data/                    # Dữ liệu BCTC từ SSI và dữ liệu chuỗi vĩ mô dầu/tỷ giá
├── docs/                    # Tài liệu kiến trúc, cẩm nang handover và kịch bản pitching
│   ├── HANDOVER_NGHIEN_CONNECT.md   # Cẩm nang thực chiến buổi sáng mai tại Nghiên Connect
│   ├── SHOWCASE_PITCHING_3MINS.md   # Kịch bản demo 3 phút giật giải Top 3 Showcase
│   └── architecture_lovable_spec.md # Bản đặc tả kỹ thuật chi tiết để prompt Lovable Pro
├── bao_cao/                 # Kho tài liệu nghiên cứu chuyên đề chuyên sâu về HVN
├── scripts/
│   ├── crawlers/            # Scripts trích xuất dữ liệu vĩ mô và BCTC tự động
│   ├── diagnostics/         # Công cụ khảo sát, đối soát BCTC và schema
│   └── logs/                # Thư mục chứa log khảo sát (được bỏ qua trong git)
├── src/                     # Core Quant Analytics Engine & Streamlit Dashboard nội bộ
├── pyproject.toml           # Cấu hình môi trường Python tiêu chuẩn với uv/hatchling
└── requirements.txt         # Danh mục thư viện Python tương thích ngược
```

---

## 👨‍💻 TÁC GIẢ & BẢN QUYỀN HỌC THUẬT
- **Tác giả**: Nguyễn Trung Hieu (Mr.Híu)
- **Định hướng**: AI Finance Engineer / Builder CFO
- **Sự kiện đồng hành**: Nghiên Connect #6 — Nghiên AI & Lovable
