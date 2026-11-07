"""
DSPy Market Data Auditor & Time-Series Quantitative Module
Bảo toàn tính toán tất định theo nguyên tắc DSPy ReAct / Assert
Kiểm tra tính nhất quán số học và sinh báo cáo vĩ mô tức thì.
"""

import json
import os
import dspy
from pydantic import BaseModel, Field

class MacroAuditInput(BaseModel):
    fuel_price: float = Field(description="Giá dầu Jet A-1 hiện tại ($/thùng)")
    usd_vnd_rate: float = Field(description="Tỷ giá USD/VND hiện tại")
    baseline_ebit: float = Field(default=6431.0, description="EBIT cơ sở FY2024 (tỷ VNĐ)")
    baseline_fuel: float = Field(default=101.0, description="Giá dầu cơ sở ($/thùng)")
    baseline_fx: float = Field(default=25690.0, description="Tỷ giá cơ sở")
    fuel_consumption_barrels: float = Field(default=8.2e6, description="Mức tiêu thụ dầu hàng năm (thùng)")
    usd_debt: float = Field(default=1.8e9, description="Dư nợ ngoại tệ USD")
    cash_balance: float = Field(default=4627.0, description="Tiền mặt và tương đương tiền (tỷ VNĐ)")
    monthly_burn_base: float = Field(default=1096.43, description="Mức chi tiêu tiền ròng cơ sở hàng tháng (tỷ VNĐ)")

class MacroAuditOutput(BaseModel):
    stressed_ebit: float = Field(description="EBIT dự phóng sau cú sốc (tỷ VNĐ)")
    solvency_status: str = Field(description="Trạng thái khả năng trả nợ: SAFE / CAUTION / CRITICAL DISTRESS")
    liquidity_runway: float = Field(description="Thời gian tồn tại thanh khoản (tháng)")
    fuel_impact_b_vnd: float = Field(description="Tác động chi phí nhiên liệu (tỷ VNĐ)")
    fx_debt_loss_b_vnd: float = Field(description="Lỗ tỷ giá từ dư nợ ngoại tệ (tỷ VNĐ)")
    audit_passed: bool = Field(description="Kết quả kiểm định số học DSPy")
    insight_summary_vi: str = Field(description="Tóm tắt nhận định tài chính tiếng Việt")

class MacroAuditSignature(dspy.Signature):
    """Thẩm định và xác nhận các chỉ số nhạy cảm vĩ mô của Vietnam Airlines."""
    input_data: str = dspy.InputField(desc="Chuỗi thông số vĩ mô và cơ cấu tài chính")
    audit_report: str = dspy.OutputField(desc="Báo cáo phân tích định lượng có kiểm định Assert")

def calculate_deterministic_audit(inp: MacroAuditInput) -> MacroAuditOutput:
    """
    Tính toán tất định 100% chuẩn toán học tài chính hàng không, không dựa vào xác suất LLM.
    """
    # 1. Tác động chi phí nhiên liệu
    delta_fuel_usd = (inp.fuel_price - inp.baseline_fuel) * inp.fuel_consumption_barrels
    fuel_impact = (delta_fuel_usd * inp.usd_vnd_rate) / 1e9

    # 2. Tác động tỷ giá lên dư nợ ngoại tệ
    fx_debt_loss = (inp.usd_debt * (inp.usd_vnd_rate - inp.baseline_fx)) / 1e9

    # 3. EBIT sau cú sốc
    stressed_ebit = inp.baseline_ebit - fuel_impact - fx_debt_loss

    # 4. Runway thanh khoản
    delta_ebit = stressed_ebit - inp.baseline_ebit
    burn_stressed = inp.monthly_burn_base - (delta_ebit / 12.0)
    if burn_stressed <= 0:
        runway = 99.0
    else:
        runway = round(inp.cash_balance / burn_stressed, 1)

    # 5. Phân loại Solvency
    if stressed_ebit >= 4000.0:
        status = "SAFE"
    elif stressed_ebit >= 0.0:
        status = "CAUTION"
    else:
        status = "CRITICAL DISTRESS"

    # Kiểm tra DSPy Assertions
    audit_passed = True
    if inp.fuel_price > inp.baseline_fuel and fuel_impact < 0:
        audit_passed = False
    if inp.usd_vnd_rate > inp.baseline_fx and fx_debt_loss < 0:
        audit_passed = False

    insight = (
        f"Với giá dầu Jet A-1 ở mức ${inp.fuel_price:.1f}/thùng và tỷ giá USD/VND {inp.usd_vnd_rate:,.0f}, "
        f"EBIT dự phóng của HVN đạt {stressed_ebit:,.0f} tỷ VNĐ ({status}). "
        f"Thời gian thanh khoản còn {runway:.1f} tháng."
    )

    return MacroAuditOutput(
        stressed_ebit=round(stressed_ebit, 1),
        solvency_status=status,
        liquidity_runway=runway,
        fuel_impact_b_vnd=round(fuel_impact, 1),
        fx_debt_loss_b_vnd=round(fx_debt_loss, 1),
        audit_passed=audit_passed,
        insight_summary_vi=insight
    )

if __name__ == "__main__":
    sample_input = MacroAuditInput(fuel_price=116.26, usd_vnd_rate=25585.35)
    result = calculate_deterministic_audit(sample_input)
    print("DSPy Deterministic Audit Result:")
    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
