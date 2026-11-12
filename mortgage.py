"""Расчёт аннуитетного ипотечного платежа без внешних зависимостей."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def calculate(principal: str, annual_rate: str, years: str) -> dict[str, Decimal | int]:
    try:
        amount = Decimal(principal)
        rate = Decimal(annual_rate)
        term = Decimal(years)
    except (InvalidOperation, TypeError) as exc:
        raise ValueError("Введите числовые значения") from exc

    if not all(value.is_finite() for value in (amount, rate, term)):
        raise ValueError("Значения должны быть конечными числами")
    if amount <= 0 or rate < 0 or term <= 0 or term * 12 != int(term * 12):
        raise ValueError("Сумма и срок должны быть положительными, ставка — неотрицательной; срок задаётся целыми месяцами")

    months = int(term * 12)
    monthly_rate = rate / Decimal(1200)
    if monthly_rate == 0:
        payment = amount / months
    else:
        factor = (1 + monthly_rate) ** months
        payment = amount * monthly_rate * factor / (factor - 1)

    money = Decimal("0.01")
    payment = payment.quantize(money, rounding=ROUND_HALF_UP)
    total = amount.quantize(money, rounding=ROUND_HALF_UP) if monthly_rate == 0 else (payment * months).quantize(money)
    return {"monthly_payment": payment, "total_payment": total,
            "overpayment": (total - amount).quantize(money), "months": months}

