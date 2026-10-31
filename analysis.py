"""Print a quick sales summary from the sample orders dataset and save charts."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # save images only, without opening a window

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "sample_orders.csv"
CHARTS_DIR = BASE_DIR / "charts"
TOP_PRODUCTS = 5
BAR_COLOR = "#2f6f9f"
LINE_COLOR = "#d1495b"

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


def average_ticket_by_month(orders):
    monthly = orders.groupby(orders["order_date"].dt.month)["total"].mean()
    monthly.index = monthly.index.map(MONTH_NAMES)
    return monthly


def print_section(title, series, as_currency):
    print(f"\n{title}")
    print("-" * len(title))
    for label, value in series.items():
        shown = format_brl(value) if as_currency else f"{value} un."
        print(f"{label:<22}{shown:>16}")


def save_chart(fig, filename):
    CHARTS_DIR.mkdir(exist_ok=True)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / filename, dpi=150)
    plt.close(fig)


def plot_revenue_by_month(monthly):
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(monthly.index, monthly.values, color=BAR_COLOR)
    ax.bar_label(
        bars, labels=[format_brl(v) for v in monthly.values], fontsize=8, padding=3
    )
    ax.set_title("Faturamento por mês")
    ax.set_ylabel("Faturamento (R$)")
    ax.tick_params(axis="x", rotation=45)
    save_chart(fig, "revenue_by_month.png")


def plot_revenue_by_channel(channels):
    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(channels.index, channels.values, color=BAR_COLOR)
    ax.bar_label(bars, labels=[format_brl(v) for v in channels.values], padding=3)
    ax.set_title("Faturamento por canal")
    ax.set_ylabel("Faturamento (R$)")
    save_chart(fig, "revenue_by_channel.png")


def plot_top_products(products):
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.barh(products.index, products.values, color=BAR_COLOR)
    ax.bar_label(bars, labels=[f"{v} un." for v in products.values], padding=4)
    ax.margins(x=0.1)
    ax.invert_yaxis()  # best seller on top
    ax.set_title(f"Top {TOP_PRODUCTS} produtos mais vendidos (quantidade)")
    ax.set_xlabel("Unidades vendidas")
    save_chart(fig, "top_products.png")


def plot_average_ticket(monthly_ticket, overall_ticket):
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(monthly_ticket.index, monthly_ticket.values, color=BAR_COLOR)
    ax.bar_label(
        bars,
        labels=[format_brl(v) for v in monthly_ticket.values],
        label_type="center",  # inside the bars, away from the dashed line
        color="white",
        fontsize=8,
    )
    ax.axhline(
        overall_ticket,
        color=LINE_COLOR,
        linestyle="--",
        label=f"Ticket médio geral: {format_brl(overall_ticket)}",
    )
    ax.set_title("Ticket médio por mês")
    ax.set_ylabel("Ticket médio (R$)")
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    save_chart(fig, "average_ticket.png")


def main():
    orders = load_orders()

    monthly = revenue_by_month(orders)
    channels = revenue_by_channel(orders)
    products = top_products_by_quantity(orders)
    ticket = average_ticket(orders)

    print_section("Faturamento por mês", monthly, True)
    print_section("Faturamento por canal", channels, True)
    print_section(
        f"Top {TOP_PRODUCTS} produtos mais vendidos (quantidade)", products, False
    )

    print("\nTicket médio")
    print("------------")
    print(format_brl(ticket))

    plot_revenue_by_month(monthly)
    plot_revenue_by_channel(channels)
    plot_top_products(products)
    plot_average_ticket(average_ticket_by_month(orders), ticket)
    print(f"\nGráficos salvos em {CHARTS_DIR}")


if __name__ == "__main__":
    main()
