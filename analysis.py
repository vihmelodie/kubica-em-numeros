"""Print a quick sales summary from the sample orders dataset."""

from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).parent / "data" / "sample_orders.csv"
TOP_PRODUCTS = 5

MONTH_NAMES = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}


def format_brl(value):
    """Format a number as Brazilian currency, e.g. R$ 1.234,56."""
    text = f"{value:,.2f}"
    return "R$ " + text.replace(",", "X").replace(".", ",").replace("X", ".")


def load_orders():
    return pd.read_csv(DATA_PATH, parse_dates=["order_date"])


def revenue_by_month(orders):
    monthly = orders.groupby(orders["order_date"].dt.month)["total"].sum()
    monthly.index = monthly.index.map(MONTH_NAMES)
    return monthly


def revenue_by_channel(orders):
    return orders.groupby("channel")["total"].sum().sort_values(ascending=False)


def top_products_by_quantity(orders):
    return (
        orders.groupby("product")["quantity"]
        .sum()
        .sort_values(ascending=False)
        .head(TOP_PRODUCTS)
    )


def average_ticket(orders):
    return orders["total"].sum() / len(orders)


def print_section(title, series, as_currency):
    print(f"\n{title}")
    print("-" * len(title))
    for label, value in series.items():
        shown = format_brl(value) if as_currency else f"{value} un."
        print(f"{label:<22}{shown:>16}")


def main():
    orders = load_orders()

    print_section("Faturamento por mês", revenue_by_month(orders), True)
    print_section("Faturamento por canal", revenue_by_channel(orders), True)
    print_section(
        f"Top {TOP_PRODUCTS} produtos mais vendidos (quantidade)",
        top_products_by_quantity(orders),
        False,
    )

    print("\nTicket médio")
    print("------------")
    print(format_brl(average_ticket(orders)))


if __name__ == "__main__":
    main()
