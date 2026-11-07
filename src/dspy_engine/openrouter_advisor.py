"""
OpenRouter Strategic Advisor Module with Hybrid Resilience
Hỗ trợ cả OpenRouter API (với API Key từ .env) và Dynamic Quant Generator.
Tự động fallback an toàn, không bao giờ để giao diện bị crash hay gián đoạn.
"""

import os
import sys
import json
import requests
from pathlib import Path

def get_openrouter_api_key():
    key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("openrouter")
    if key:
        return key.strip().strip("'\"")

    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("openrouter") or line.startswith("OPENROUTER"):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        return parts[1].strip().strip("'\"")
    return None

def generate_dynamic_quant_recommendations(fuel_price: float, fx_rate: float, stressed_ebit: float, runway_months: float):
    """
    Sinh 3 khuyến nghị tài chính chiến lược dựa trên logic định lượng (100% tất định và tin cậy).
    """
    fuel_delta = fuel_price - 101.0
    fx_delta = fx_rate - 25690.0

    # Khuyến nghị 1: Về vốn và khả năng sống sót
    if runway_months < 4.0:
        rec1_vi = f"Kích hoạt cơ chế đệm thanh khoản khẩn cấp khi Runway co lại còn {runway_months:.1f} tháng; đẩy nhanh giải ngân gói hỗ trợ Nhà nước."
        rec1_en = f"Activate emergency liquidity buffer as runway compresses to {runway_months:.1f} months; expedite state refinancing disbursements."
    else:
        rec1_vi = "Đẩy nhanh tiến độ phát hành tăng vốn điều lệ và tái cấu trúc tài chính để khôi phục vốn chủ sở hữu dương trước FY2026."
        rec1_en = "Accelerate equity rights issuance and balance sheet restructuring to restore positive net worth before FY2026."

    # Khuyến nghị 2: Về giá dầu
    if fuel_delta > 10.0:
        rec2_vi = f"Kích hoạt phòng vệ giá Jet A-1 cho 40-50% sản lượng năm khi giá dầu chạm ngưỡng ${fuel_price:.1f}/thùng (chiếm >38% chi phí)."
        rec2_en = f"Execute Jet A-1 collar hedging for 40-50% annual volume as fuel hits ${fuel_price:.1f}/bbl (>38% of operating costs)."
    else:
        rec2_vi = "Duy trì theo dõi biến động crack spread Singapore Jet A-1 và đàm phán hợp đồng cung ứng nhiên liệu dài hạn linh hoạt."
        rec2_en = "Monitor Singapore Jet A-1 crack spread dynamics and negotiate flexible long-term supply agreements."

    # Khuyến nghị 3: Về tỷ giá và nợ ngoại tệ
    if fx_delta > 200.0:
        rec3_vi = f"Tái cơ cấu danh mục nợ vay $1.8B USD sang VND hoặc công cụ hoán đổi tiền tệ chéo (CCS) để cắt lỗ tỷ giá khi USD tăng."
        rec3_en = f"Restructure $1.8B USD debt via Cross-Currency Swaps (CCS) or local currency refinancing to cap FX devaluation loss."
    else:
        rec3_vi = f"Tận dụng đà ổn định tỷ giá hiện tại ({fx_rate:,.0f} VND) để trả trước các khoản vay thuê tàu bay USD lãi suất thả nổi."
        rec3_en = f"Leverage favorable FX stability ({fx_rate:,.0f} VND) to prepay floating-rate USD aircraft finance leases."

    return {
        "source": "dynamic-quant-engine",
        "recs_vi": [rec1_vi, rec2_vi, rec3_vi],
        "recs_en": [rec1_en, rec2_en, rec3_en]
    }

def generate_strategic_recommendations(fuel_price: float, fx_rate: float, stressed_ebit: float, runway_months: float):
    """
    Thử nghiệm gọi OpenRouter API trước, nếu tài khoản chưa nạp credit/bị rate-limit thì tự động fallback sang Dynamic Quant Engine.
    """
    api_key = get_openrouter_api_key()
    if api_key:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://lotus-flight-financial-lens.lovable.app",
            "X-Title": "HVN Financial Intelligence Platform"
        }
        prompt = f"Phân tích HVN: Dầu ${fuel_price:.1f}, FX {fx_rate:,.0f}, EBIT {stressed_ebit:,.0f}B, Runway {runway_months:.1f}mo. Cho 3 khuyến nghị JSON."
        payload = {
            "model": "google/gemini-2.5-flash",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 300
        }
        try:
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=4)
            if res.status_code == 200:
                content = res.json()["choices"][0]["message"]["content"].strip()
                if "```" in content:
                    content = content.split("```json")[-1].split("```")[0].strip()
                data = json.loads(content)
                if "recs_vi" in data and "recs_en" in data:
                    return {
                        "source": "openrouter-ai",
                        "model": "google/gemini-2.5-flash",
                        "recs_vi": data["recs_vi"][:3],
                        "recs_en": data["recs_en"][:3]
                    }
        except Exception:
            pass

    # Fallback mượt mà
    return generate_dynamic_quant_recommendations(fuel_price, fx_rate, stressed_ebit, runway_months)

if __name__ == "__main__":
    recs = generate_strategic_recommendations(116.3, 25585.0, 3410.0, 3.4)
    print(json.dumps(recs, indent=2, ensure_ascii=False))
