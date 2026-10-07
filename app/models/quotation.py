from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass
class Customer:
    name: str = ""
    company: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    phone: str = ""
    email: str = ""


@dataclass
class QuotationItem:
    product_code: str
    product_name: str
    description: str = ""
    measuring_range: str = ""
    quantity: int = 1
    unit_price: Decimal = Decimal("0.00")

    @property
    def total_price(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass
class Quotation:
    quotation_number: str
    quotation_date: date

    customer: Customer

    items: list[QuotationItem] = field(default_factory=list)

    transportation: Decimal = Decimal("0.00")
    additional_items: Decimal = Decimal("0.00")

    cgst_rate: Decimal = Decimal("9.00")
    sgst_rate: Decimal = Decimal("9.00")

    packing_percentage: Decimal = Decimal("3.50")

    validity: str = "60 days"
    payment_terms: str = "100% advance with purchase order"
    warranty: str = "One year against manufacturing defects"
    delivery: str = "Within 4–6 weeks from confirmed order"
    freight: str = "To pay basis"
    installation_commissioning: str = "Free by engineers"

    sales_person: str = "Amol Lunawat"

    @property
    def subtotal(self) -> Decimal:
        return sum(
            (item.total_price for item in self.items),
            Decimal("0.00")
        )

    @property
    def taxable_value(self) -> Decimal:
        return (
            self.subtotal
            + self.transportation
            + self.additional_items
        )

    @property
    def cgst_amount(self) -> Decimal:
        return (
            self.taxable_value
            * self.cgst_rate
            / Decimal("100")
        )

    @property
    def sgst_amount(self) -> Decimal:
        return (
            self.taxable_value
            * self.sgst_rate
            / Decimal("100")
        )

    @property
    def gst_amount(self) -> Decimal:
        return self.cgst_amount + self.sgst_amount

    @property
    def grand_total(self) -> Decimal:
        return self.taxable_value + self.gst_amount


def create_default_quotation() -> Quotation:
    """Create a blank quotation with standard defaults."""

    return Quotation(
        quotation_number="AA/VMM/26-27/001",
        quotation_date=date.today(),
        customer=Customer(),
    )


if __name__ == "__main__":

    quotation = create_default_quotation()

    quotation.customer = Customer(
        name="Mr. Amol Lunawat",
        company="",
        address="",
        city="Pune",
        state="Maharashtra",
        phone="7020991684",
        email="armatech@gmail.com",
    )

    quotation.items.append(
        QuotationItem(
            product_code="AA-9043AC",
            product_name="AUTOMATIC VIDEO MEASURING MACHINE WITH CABINET",
            description="CRYSTAL Automatic Video Measuring System with Cabinet",
            measuring_range="500 × 400 × 200 mm",
            quantity=1,
            unit_price=Decimal("100000.00"),
        )
    )

    print("=" * 55)
    print("CRYSTAL QUOTATION MODEL TEST")
    print("=" * 55)

    print(f"Quotation No. : {quotation.quotation_number}")
    print(f"Date          : {quotation.quotation_date}")
    print(f"Customer      : {quotation.customer.name}")
    print(f"Product       : {quotation.items[0].product_code}")
    print(f"Quantity      : {quotation.items[0].quantity}")
    print(f"Unit Price    : ₹{quotation.items[0].unit_price:,.2f}")
    print(f"Subtotal      : ₹{quotation.subtotal:,.2f}")
    print(f"Taxable Value : ₹{quotation.taxable_value:,.2f}")
    print(f"CGST (9%)     : ₹{quotation.cgst_amount:,.2f}")
    print(f"SGST (9%)     : ₹{quotation.sgst_amount:,.2f}")
    print(f"Grand Total   : ₹{quotation.grand_total:,.2f}")

    print()
    print("QUOTATION MODEL: OK")