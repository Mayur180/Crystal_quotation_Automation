from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from app.models.quotation import Quotation


MONEY = Decimal("0.01")


def money(value: Decimal | float | int) -> Decimal:
    """Round a value to two decimal places."""

    return Decimal(str(value)).quantize(
        MONEY,
        rounding=ROUND_HALF_UP
    )


class QuotationCalculationService:
    """
    Handles all quotation financial calculations.
    """

    def calculate(self, quotation: Quotation) -> dict[str, Decimal]:
        """
        Calculate all financial values for a quotation.
        """

        subtotal = money(quotation.subtotal)

        additional_items = money(
            quotation.additional_items
        )

        transportation = money(
            quotation.transportation
        )

        taxable_value = money(
            subtotal
            + additional_items
            + transportation
        )

        cgst = money(
            taxable_value
            * quotation.cgst_rate
            / Decimal("100")
        )

        sgst = money(
            taxable_value
            * quotation.sgst_rate
            / Decimal("100")
        )

        total_gst = money(cgst + sgst)

        grand_total = money(
            taxable_value + total_gst
        )

        return {
            "subtotal": subtotal,
            "additional_items": additional_items,
            "transportation": transportation,
            "taxable_value": taxable_value,
            "cgst_rate": money(quotation.cgst_rate),
            "cgst_amount": cgst,
            "sgst_rate": money(quotation.sgst_rate),
            "sgst_amount": sgst,
            "gst_amount": total_gst,
            "grand_total": grand_total,
        }


if __name__ == "__main__":

    from decimal import Decimal

    from app.models.quotation import (
        Customer,
        QuotationItem,
    )

    quotation = Quotation(
        quotation_number="AA/VMM/26-27/007",
        quotation_date=__import__("datetime").date.today(),
        customer=Customer(
            name="Test Customer",
            company="Test Company",
            city="Pune",
            state="Maharashtra",
        ),
    )

    quotation.items.append(
        QuotationItem(
            product_code="AA-9043AC",
            product_name=(
                "AUTOMATIC VIDEO MEASURING "
                "MACHINE WITH CABINET"
            ),
            quantity=1,
            unit_price=Decimal("100000.00"),
        )
    )

    quotation.transportation = Decimal("5000.00")
    quotation.additional_items = Decimal("2000.00")

    service = QuotationCalculationService()

    result = service.calculate(quotation)

    print("=" * 60)
    print("CRYSTAL QUOTATION CALCULATION TEST")
    print("=" * 60)

    print(f"Subtotal       : ₹{result['subtotal']:,.2f}")
    print(
        f"Additional     : ₹{result['additional_items']:,.2f}"
    )
    print(
        f"Transportation : ₹{result['transportation']:,.2f}"
    )
    print(
        f"Taxable Value  : ₹{result['taxable_value']:,.2f}"
    )
    print(
        f"CGST (9%)      : ₹{result['cgst_amount']:,.2f}"
    )
    print(
        f"SGST (9%)      : ₹{result['sgst_amount']:,.2f}"
    )
    print(
        f"GST Total      : ₹{result['gst_amount']:,.2f}"
    )
    print(
        f"Grand Total    : ₹{result['grand_total']:,.2f}"
    )

    print()
    print("QUOTATION CALCULATION SERVICE: OK")