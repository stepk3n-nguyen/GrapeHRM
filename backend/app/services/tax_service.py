"""
Tính thuế thu nhập cá nhân (TNCN) theo luật Việt Nam — biểu lũy tiến từng phần.

Công thức tháng:
  thu nhập tính thuế = tổng thu nhập − BH bắt buộc − giảm trừ bản thân − giảm trừ người phụ thuộc
  thuế TNCN = lũy tiến từng phần trên thu nhập tính thuế (dùng phương pháp "khấu trừ nhanh").

Mức giảm trừ theo Nghị quyết 954/2020/UBTVQH14 (áp dụng từ 2020):
  • Bản thân: 11.000.000đ/tháng
  • Mỗi người phụ thuộc: 4.400.000đ/tháng
"""

PERSONAL_DEDUCTION = 11_000_000          # giảm trừ bản thân / tháng
DEPENDENT_DEDUCTION = 4_400_000          # giảm trừ mỗi người phụ thuộc / tháng

# Biểu thuế lũy tiến từng phần theo THÁNG: (trần bậc, thuế suất, số trừ nhanh).
# Số trừ nhanh giúp tính 1 dòng thay vì cộng dồn từng bậc.
_BRACKETS = [
    (5_000_000,   0.05, 0),
    (10_000_000,  0.10, 250_000),
    (18_000_000,  0.15, 750_000),
    (32_000_000,  0.20, 1_650_000),
    (52_000_000,  0.25, 3_250_000),
    (80_000_000,  0.30, 5_850_000),
    (float("inf"), 0.35, 9_850_000),
]


def taxable_income(gross, insurance, num_dependents=0):
    """Thu nhập tính thuế = gross − BH bắt buộc − giảm trừ gia cảnh (không âm)."""
    reductions = PERSONAL_DEDUCTION + max(num_dependents, 0) * DEPENDENT_DEDUCTION
    return max(float(gross) - float(insurance) - reductions, 0.0)


def personal_income_tax(taxable):
    """Thuế TNCN tháng từ thu nhập tính thuế (đã trừ giảm trừ)."""
    taxable = float(taxable)
    if taxable <= 0:
        return 0.0
    for ceiling, rate, quick in _BRACKETS:
        if taxable <= ceiling:
            return round(taxable * rate - quick, 2)
    return 0.0


def compute_pit(gross, insurance, num_dependents=0):
    """Tiện ích: trả về (thu_nhập_tính_thuế, thuế_TNCN)."""
    ti = taxable_income(gross, insurance, num_dependents)
    return ti, personal_income_tax(ti)
