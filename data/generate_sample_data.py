"""Generate a fictional orders dataset for the "Kubica em Números" dashboard.

All data is synthetic. Running this script always produces the same file,
because the random seed is fixed.
"""

import random
from pathlib import Path

import pandas as pd

SEED = 42
NUM_ORDERS = 300
START_DATE = "2026-01-01"
END_DATE = "2026-10-31"
OCTOBER_WEIGHT = 3  # October days are 3x more likely to receive an order
OUTPUT_PATH = Path(__file__).parent / "sample_orders.csv"

CHANNELS = ["Nuvemshop", "Shopee", "TikTok Shop"]
CHANNEL_WEIGHTS = [3, 4, 3]

# Fictional 3D-printed fidgets: (product name, unit price in BRL)
PRODUCTS = [
    ("Cubo Espiral", 15.90),
    ("Anel Giratório", 19.90),
    ("Corrente Flex", 24.90),
    ("Roda Zen", 29.90),
    ("Serpente Articulada", 34.90),
    ("Clique Hexa", 39.90),
    ("Pião Mini", 44.90),
    ("Gota Deslizante", 49.90),
    ("Engrenagem Infinita", 54.90),
    ("Esfera Labirinto", 59.90),
]

QUANTITIES = [1, 2, 3, 4]
QUANTITY_WEIGHTS = [60, 25, 10, 5]


def build_date_weights():
    """Return every day in the period and its sampling weight."""
    days = pd.date_range(START_DATE, END_DATE, freq="D")
    weights = [OCTOBER_WEIGHT if day.month == 10 else 1 for day in days]
    return days, weights


def generate_orders():
    """Create the orders as a DataFrame sorted by date."""
    random.seed(SEED)
    days, weights = build_date_weights()

    order_dates = random.choices(days, weights=weights, k=NUM_ORDERS)
    rows = []
    for order_date in sorted(order_dates):
        product, unit_price = random.choice(PRODUCTS)
        quantity = random.choices(QUANTITIES, weights=QUANTITY_WEIGHTS)[0]
        rows.append(
            {
                "order_date": order_date.date().isoformat(),
                "channel": random.choices(CHANNELS, weights=CHANNEL_WEIGHTS)[0],
                "product": product,
                "quantity": quantity,
                "unit_price": unit_price,
                "total": round(quantity * unit_price, 2),
            }
        )

    orders = pd.DataFrame(rows)
    orders.insert(0, "order_id", [f"KB-{i:04d}" for i in range(1, len(orders) + 1)])
    return orders


def main():
    orders = generate_orders()
    orders.to_csv(OUTPUT_PATH, index=False)
    print(f"{len(orders)} orders saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
