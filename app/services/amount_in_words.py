"""
CRYSTAL / ARMATECH ASSOCIATES
Amount in Words Service
"""

from decimal import Decimal


# ============================================================
# NUMBER WORDS
# ============================================================

ONES = [
    "",
    "One",
    "Two",
    "Three",
    "Four",
    "Five",
    "Six",
    "Seven",
    "Eight",
    "Nine",
]

TEENS = [
    "Ten",
    "Eleven",
    "Twelve",
    "Thirteen",
    "Fourteen",
    "Fifteen",
    "Sixteen",
    "Seventeen",
    "Eighteen",
    "Nineteen",
]

TENS = [
    "",
    "",
    "Twenty",
    "Thirty",
    "Forty",
    "Fifty",
    "Sixty",
    "Seventy",
    "Eighty",
    "Ninety",
]


# ============================================================
# TWO DIGITS
# ============================================================

def two_digits(number):

    number = int(number)

    if number == 0:
        return ""

    if number < 10:
        return ONES[number]

    if number < 20:
        return TEENS[number - 10]

    tens = number // 10
    ones = number % 10

    if ones:
        return f"{TENS[tens]} {ONES[ones]}"

    return TENS[tens]


# ============================================================
# THREE DIGITS
# ============================================================

def three_digits(number):

    number = int(number)

    if number == 0:
        return ""

    hundreds = number // 100
    remainder = number % 100

    parts = []

    if hundreds:
        parts.append(
            f"{ONES[hundreds]} Hundred"
        )

    if remainder:
        parts.append(
            two_digits(remainder)
        )

    return " ".join(parts)


# ============================================================
# INDIAN NUMBER SYSTEM
# ============================================================

def number_to_words(number):

    number = int(number)

    if number == 0:
        return "Zero"

    parts = []

    crore = number // 10000000
    number %= 10000000

    lakh = number // 100000
    number %= 100000

    thousand = number // 1000
    number %= 1000

    remainder = number

    if crore:
        parts.append(
            f"{three_digits(crore)} Crore"
        )

    if lakh:
        parts.append(
            f"{three_digits(lakh)} Lakh"
        )

    if thousand:
        parts.append(
            f"{three_digits(thousand)} Thousand"
        )

    if remainder:
        parts.append(
            three_digits(remainder)
        )

    return " ".join(parts)


# ============================================================
# PUBLIC FUNCTION
# ============================================================

def amount_in_words(amount):

    """
    Convert a monetary amount into Indian English words.

    Example:
        158769
        ->
        One Lakh Fifty Eight Thousand Seven Hundred Sixty Nine
        Rupees Only
    """

    try:

        value = Decimal(str(amount))

    except Exception:

        value = Decimal("0")

    if value < 0:
        value = abs(value)

    rupees = int(
        value
    )

    paise = int(
        (
            value
            - Decimal(rupees)
        )
        * Decimal("100")
    )

    result = (
        f"{number_to_words(rupees)} Rupees"
    )

    if paise:

        result += (
            f" and "
            f"{number_to_words(paise)} Paise"
        )

    result += " Only"

    return result


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_amounts = [
        Decimal("100000"),
        Decimal("158769"),
        Decimal("1250000"),
        Decimal("12345678.50"),
    ]

    for value in test_amounts:

        print(
            f"{value:,.2f}"
            f" -> "
            f"{amount_in_words(value)}"
        )