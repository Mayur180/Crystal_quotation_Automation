from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ProductService:
    """
    Loads CRYSTAL product information from JSON files.

    Product files are stored in:
        data/products/

    Example:
        data/products/AA-9043AC.json
    """

    def __init__(self, products_directory: str | Path | None = None):
        if products_directory is None:
            # Project root:
            # CRYSTAL_Quotation_Automation/
            project_root = Path(__file__).resolve().parents[2]
            products_directory = project_root / "data" / "products"

        self.products_directory = Path(products_directory)

        if not self.products_directory.exists():
            self.products_directory.mkdir(parents=True, exist_ok=True)

    def get_product(self, product_code: str) -> dict[str, Any]:
        """
        Load a product using its model/product code.

        Example:
            service.get_product("AA-9043AC")
        """

        product_code = product_code.strip().upper()

        if not product_code:
            raise ValueError("Product code cannot be empty.")

        product_file = self.products_directory / f"{product_code}.json"

        if not product_file.exists():
            raise FileNotFoundError(
                f"Product '{product_code}' was not found. "
                f"Expected file: {product_file}"
            )

        try:
            with product_file.open("r", encoding="utf-8") as file:
                product_data = json.load(file)

        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Product file '{product_file.name}' contains invalid JSON."
            ) from exc

        if not isinstance(product_data, dict):
            raise ValueError(
                f"Product file '{product_file.name}' must contain a JSON object."
            )

        return product_data

    def product_exists(self, product_code: str) -> bool:
        """
        Check whether a product exists.
        """

        product_code = product_code.strip().upper()

        if not product_code:
            return False

        product_file = self.products_directory / f"{product_code}.json"

        return product_file.exists()

    def list_products(self) -> list[dict[str, Any]]:
        """
        Return all available product records.
        """

        products: list[dict[str, Any]] = []

        for product_file in sorted(self.products_directory.glob("*.json")):
            try:
                with product_file.open("r", encoding="utf-8") as file:
                    product_data = json.load(file)

                if isinstance(product_data, dict):
                    products.append(product_data)

            except (json.JSONDecodeError, OSError):
                # Ignore invalid/unreadable files here.
                # Detailed errors are raised when get_product() is called.
                continue

        return products

    def list_product_codes(self) -> list[str]:
        """
        Return available product/model codes.
        """

        codes: list[str] = []

        for product_file in sorted(self.products_directory.glob("*.json")):
            codes.append(product_file.stem.upper())

        return codes

    def get_product_name(self, product_code: str) -> str:
        """
        Return the product name for a product code.
        """

        product = self.get_product(product_code)

        return str(
            product.get(
                "product_name",
                product_code.upper()
            )
        )

    def get_measuring_range(self, product_code: str) -> str:
        """
        Return the combined measuring range.
        """

        product = self.get_product(product_code)

        measuring_range = product.get("measuring_range", {})

        if isinstance(measuring_range, dict):
            combined = measuring_range.get("combined")

            if combined:
                return str(combined)

        return ""


if __name__ == "__main__":
    """
    Simple command-line test.

    This allows us to verify Step 4 before building
    the quotation generator.
    """

    service = ProductService()

    print("=" * 50)
    print("CRYSTAL PRODUCT SERVICE TEST")
    print("=" * 50)

    print("\nAvailable product codes:")

    product_codes = service.list_product_codes()

    if not product_codes:
        print("No products found.")
    else:
        for code in product_codes:
            print(f"  - {code}")

    print("\nTesting AA-9043AC...")

    try:
        product = service.get_product("AA-9043AC")

        print(f"Product Code : {product.get('product_code')}")
        print(f"Product Name : {product.get('product_name')}")
        print(f"Description  : {product.get('description')}")
        print(f"Model        : {product.get('product_code')}")
        print(f"Range        : {service.get_measuring_range('AA-9043AC')}")

        print("\nPRODUCT LOADING: OK")

    except Exception as exc:
        print(f"\nPRODUCT LOADING: FAILED")
        print(f"Error: {exc}")
