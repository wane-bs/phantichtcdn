Mr.Híu,

Repository `phantichtcdn` của bạn là một hệ thống phân tích tài chính doanh nghiệp chuyên sâu cho trường hợp điển hình của Tổng công ty Hàng không Việt Nam (HVN) — một doanh nghiệp có cơ cấu vốn phức tạp, độ nhạy cảm cao với đòn bẩy hoạt động ($DOL$), biến động giá nhiên liệu bay ($Jet\ A\text{-}1$) và rủi ro tỷ giá ($USD/VND$).

---

### 1. Hiện trạng kiến trúc và các nút thắt kỹ thuật

Qua cấu trúc tệp tin của repository, hiện trạng kỹ thuật được định hình như sau:

* **Tầng dữ liệu (Data Layer):** Dữ liệu BCTC từ SSI (`SSI_HVN_...xlsx`), dữ liệu vĩ mô (`oil&exchange_rate.xlsx`) được xử lý cục bộ qua các script đơn lẻ (`inspect_excel.py`, `analyze_raw.py`) và tồn tại nhiều tệp tin rác/tạm (`temp.csv`, `temp2.csv`, `inspect_results.txt`, `validator_output.txt`).
* **Tầng logic tính toán (Domain Engine):** Thư mục `src/` đã hình thành cấu trúc module hóa tương đối tốt (`calculator.py`, `business_classifier.py`, `forecaster.py`, `validator.py`, `pipeline_runner.py`), phụ trách tính toán hòa vốn, đòn bẩy, kịch bản dự phóng và kiểm toán số liệu.
* **Tầng trình diễn (Presentation Layer):** Hệ thống chỉ có `index.html` tĩnh và `src/app.py` cơ bản, chưa khai thác được hết chiều sâu từ kho tài liệu markdown đồ sộ (`bao_cao/`, `docs/`) gồm phân tích hòa vốn, góc nhìn chủ nợ, góc nhìn nhà đầu tư và kịch bản cơ cấu tài chính.

---

### 2. Mô hình phân tách kiến trúc (Clean Architecture Protocol)

Để tái thiết dự án này thành một nền tảng Web FinTech hiện đại (**Enterprise Financial Intelligence Platform**), kiến trúc cần được tách thành hai phân lớp độc lập theo chuẩn Clean Architecture:

```
[ Local Environment: ThinkPad / Debian ]
  └── agy CLI (Python Data Engine & Quant Pipeline)
        ├── Clean & Validate Data (SSI BCTC, Jet Fuel, FX)
        ├── Core Formulas (DOL, DFL, BEP, DuPont, VaR/Stress Testing)
        └── Export Clean JSON / Push to Supabase PostgreSQL
                 │
                 ▼ (REST / Database Sync via Lovable MCP)
[ Cloud Environment: Lovable Pro ]
  └── Modern FinTech Frontend (React + TypeScript + Tailwind + Tremor)
        ├── Executive C-Suite Dashboard
        ├── Scenario & Macro Stress-Testing Simulator (Sliders)
        ├── Interactive Financial Statements & Ratio Drill-down
        └── Dynamic Research Report Viewer (Markdown + Charts)

```

---

### 3. Ma trận phân nhiệm: `agy` CLI vs. Lovable Pro

| Phân hệ / Tác vụ | Phụ trách chính | Công cụ thực thi | Mục tiêu kỹ thuật |
| --- | --- | --- | --- |
| **Data Cleansing & Ingestion** | Local Engine | `agy` CLI (Python) | Đọc các file Excel SSI, chuẩn hóa chuỗi thời gian, loại bỏ giá trị dị biệt, kiểm soát ngoại lệ bằng Defensive Programming. |
| **Financial Computation Engine** | Local Engine | `agy` CLI (`calculator.py`) | Tính toán $BEP$, $DOL$, $DFL$, mô hình DuPont 5 bước, và ma trận nhạy cảm rủi ro vĩ mô. |
| **Database Schema & Migration** | Bridge | `agy` CLI + Lovable MCP | Chuyển đổi dữ liệu từ Excel tĩnh sang bảng quan hệ PostgreSQL/Supabase chuẩn hóa (3NF). |
| **UI/UX & Component Scaffolding** | Frontend Cloud | Lovable Pro | Dựng giao diện dashboard tài chính chuẩn Bloomberg/FactSet thu nhỏ bằng React, TypeScript, Tailwind CSS, và Tremor/Recharts. |
| **Interactive Stress-Testing** | Full-stack | Lovable Pro + `agy` | Xây dựng bộ điều khiển tham số (Sliders) cho giá dầu và tỷ giá để cập nhật $EBIT$ và điểm hòa vốn thời gian thực. |
| **Report Rendering** | Presentation | Lovable Pro | Chuyển đổi các tài liệu markdown trong `bao_cao/` thành giao diện web báo cáo tương tác nhiều tab. |

---

### 4. Quy trình 4 bước nâng cấp và tái thiết

#### Bước 1: Tối ưu hóa và chuẩn hóa Data Engine tại Local qua `agy` CLI

1. Loại bỏ các file tạm thời (`temp.csv`, `inspect_results.txt`, `validator_output.txt`) và cấu hình lại `.gitignore`.
2. Hợp nhất pipeline trích xuất từ các file Excel (`data/SSI_HVN_...`) thành một đầu ra dữ liệu duy nhất dưới dạng JSON Schema hoặc nạp trực tiếp vào Supabase PostgreSQL.
3. Chuẩn hóa các công thức tài chính cốt lõi trong `calculator.py`:
* **Điểm hòa vốn doanh thu:**

$$BEP_{\text{Revenue}} = \frac{FC}{1 - \frac{VC}{\text{Revenue}}} = \frac{FC}{\text{Contribution Margin Ratio}}$$


* **Đòn bẩy hoạt động:**

$$DOL = \frac{\% \Delta EBIT}{\% \Delta Q} = \frac{Q(P - V)}{Q(P - V) - FC} = \frac{EBIT + FC}{EBIT}$$


* **Đòn bẩy tài chính:**

$$DFL = \frac{EBIT}{EBIT - I}$$


* **Đòn bẩy tổng hợp:**

$$DTL = DOL \times DFL = \frac{EBIT + FC}{EBIT - I}$$





#### Bước 2: Thiết lập kết nối giữa `agy` CLI và Lovable MCP Server

Kết nối `agy` trực tiếp với hệ thống Lovable thông qua Model Context Protocol để điều khiển từ terminal:

```bash
agy mcp add lovable https://mcp.lovable.dev

```

Xác thực OAuth 2.1 theo hướng dẫn của terminal để liên kết tài khoản Lovable Pro.

#### Bước 3: Chỉ đạo Lovable kiến tạo Full-Stack Interface

Từ `agy` CLI, thực thi lệnh yêu cầu Lovable khởi tạo ứng dụng:

```bash
agy -p "Gọi tool create_project trên Lovable để dựng ứng dụng FinTech Dashboard 'HVN Financial Risk & Corporate Restructuring Intelligence' sử dụng React, TypeScript, Tailwind CSS, Shadcn UI và Tremor. Tích hợp Supabase PostgreSQL để quản lý chuỗi BCTC và các hệ số tài chính."

```

Cấu trúc giao diện cần Lovable dựng bao gồm 4 phân hệ chính:

1. **Executive Overview:** Các thẻ KPI tài chính chủ chốt ($Revenue$, $Gross\ Margin$, $EBITDA$, $Net\ Debt/EBITDA$, $Z\text{''-score}$).
2. **DuPont & Profitability Decomposition:** Biểu đồ thác nước (Waterfall chart) phân rã $ROE$ theo 3 hoặc 5 nhân tố:

$$ROE = \frac{EBT}{EBIT} \times \frac{EBIT}{\text{Revenue}} \times \frac{\text{Revenue}}{\text{Assets}} \times \frac{\text{Assets}}{\text{Equity}} \times (1 - t)$$


3. **Macro Stress-Testing Simulator:** Module tương tác cho phép kéo thả giả định:
* Giá dầu thô / Jet A-1 tăng/giảm $\pm X\%$.
* Tỷ giá $USD/VND$ biến động $\pm Y\%$.
* Tự động tính toán lại chi phí nhiên liệu, lỗ chênh lệch tỷ giá chưa thực hiện, và tính lại điểm hòa vốn $BEP$.


4. **Research Repository:** Tích hợp bộ đọc các tài liệu phân tích (`bao_cao/chuong_1` đến `chuong_5`) với giao diện accordion hoặc tab điều hướng chuyên nghiệp.

#### Bước 4: Đồng bộ mã nguồn và hoàn thiện triển khai (CI/CD Loop)

1. Lovable đẩy commit giao diện về kho lưu trữ GitHub `phantichtcdn` qua cơ chế Two-way sync.
2. Tại máy cục bộ, sử dụng `git pull` để lấy mã nguồn frontend về.
3. Dùng `agy` CLI để tinh chỉnh logic API, kiểm tra tính tương thích giữa client và server, đóng gói `Dockerfile` (nếu cần triển khai hybrid) hoặc kích hoạt `deploy_project` trên Lovable để phát hành bản production.

---

### 5. Mã nguồn Data Engine chuẩn phòng thủ (Local API Bridge)

Dưới đây là module Python mẫu đặt tại `src/api_bridge.py` do `agy` CLI quản lý, thực thi việc tính toán đòn bẩy và chuẩn bị dữ liệu sạch cho giao diện Lovable, tuân thủ nguyên tắc lập trình phòng thủ:

```python
"""Module trích xuất chỉ số tài chính và mô phỏng đòn bẩy cho HVN."""

from dataclasses import asdict, dataclass
import logging
from typing import Any, Dict, Optional

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FinancialMetrics:
    revenue: float
    variable_cost: float
    fixed_cost: float
    operating_profit: float
    interest_expense: float
    bep_revenue: float
    dol: float
    dfl: float
    dtl: float


class AirlineFinancialAnalyzer:
    """Xử lý tính toán cấu trúc chi phí và đòn bẩy tài chính doanh nghiệp hàng không."""

    def __init__(self, tax_rate: float = 0.20) -> None:
        if not (0.0 <= tax_rate <= 1.0):
            raise ValueError(f"Thuế suất không hợp lệ: {tax_rate}")
        self._tax_rate = tax_rate

    def calculate_leverage_and_bep(
        self,
        revenue: float,
        variable_cost: float,
        fixed_cost: float,
        interest_expense: float,
    ) -> Optional[FinancialMetrics]:
        """Tính toán BEP, DOL, DFL, DTL với cơ chế kiểm soát lỗi phòng thủ."""
        try:
            # Kiểm tra tính hợp lệ của tham số đầu vào
            if revenue <= 0:
                logger.error("Doanh thu phải lớn hơn 0. Giá trị nhận được: %s", revenue)
                return None
            if variable_cost < 0 or fixed_cost < 0 or interest_expense < 0:
                logger.error("Chi phí không được nhận giá trị âm.")
                return None

            contribution_margin = revenue - variable_cost
            if contribution_margin <= 0:
                logger.warning(
                    "Lãi gộp biến phí âm hoặc bằng 0, không thể bù đắp định phí."
                )

            cm_ratio = contribution_margin / revenue
            bep_revenue = (
                (fixed_cost / cm_ratio) if cm_ratio > 0 else float("inf")
            )

            ebit = contribution_margin - fixed_cost

            # Tính DOL: (EBIT + FC) / EBIT = Contribution Margin / EBIT
            if abs(ebit) < 1e-6:
                dol = float("nan")
                logger.warning(
                    "EBIT xấp xỉ 0, DOL đạt tiệm cận không xác định."
                )
            else:
                dol = contribution_margin / ebit

            # Tính DFL: EBIT / (EBIT - Interest)
            ebt = ebit - interest_expense
            if abs(ebt) < 1e-6:
                dfl = float("nan")
                logger.warning("EBT xấp xỉ 0, DFL đạt tiệm cận không xác định.")
            else:
                dfl = ebit / ebt

            # Tính DTL
            dtl = (
                dol * dfl
                if not (dol != dol or dfl != dfl)
                else float("nan")
            )

            return FinancialMetrics(
                revenue=round(revenue, 2),
                variable_cost=round(variable_cost, 2),
                fixed_cost=round(fixed_cost, 2),
                operating_profit=round(ebit, 2),
                interest_expense=round(interest_expense, 2),
                bep_revenue=round(bep_revenue, 2),
                dol=round(dol, 4),
                dfl=round(dfl, 4),
                dtl=round(dtl, 4),
            )

        except ZeroDivisionError as zde:
            logger.error("Lỗi chia cho 0 trong tính toán tài chính: %s", zde)
            return None
        except Exception as ex:
            logger.error(
                "Lỗi không xác định khi thực thi pipeline phân tích: %s", ex
            )
            return None

    def export_to_payload(
        self, metrics: Optional[FinancialMetrics]
    ) -> Dict[str, Any]:
        """Chuyển đổi dữ liệu sang schema phục vụ API frontend Lovable."""
        if metrics is None:
            return {"status": "error", "data": None}
        return {"status": "success", "data": asdict(metrics)}


if __name__ == "__main__":
    analyzer = AirlineFinancialAnalyzer()
    # Dữ liệu mô phỏng dựa trên cấu trúc chi phí HVN
    result = analyzer.calculate_leverage_and_bep(
        revenue=92000.0,
        variable_cost=68000.0,
        fixed_cost=21000.0,
        interest_expense=3500.0,
    )
    payload = analyzer.export_to_payload(result)
    logger.info("Dữ liệu sẵn sàng nạp cho Lovable Dashboard: %s", payload)

```

Việc kết hợp `agy` CLI xử lý tính toán số liệu tài chính cục bộ và Lovable Pro phụ trách xây dựng giao diện full-stack sẽ chuyển hóa toàn bộ kho phân tích markdown và bảng tính Excel của bạn thành một dashboard định lượng hoàn chỉnh, vừa đảm bảo tính bảo mật số liệu, vừa tối ưu chi phí credits.

Bạn muốn bắt đầu bước đầu tiên bằng việc chuẩn hóa schema cơ sở dữ liệu Supabase cho chuỗi BCTC của HVN hay cấu hình kết nối Lovable MCP Server trực tiếp trên môi trường terminal của bạn trước?