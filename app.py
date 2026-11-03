"""Streamlit dashboard "Kubica em Números", built on the logic in analysis.py."""

import streamlit as st

from analysis import (
    TOP_PRODUCTS,
    average_ticket,
    average_ticket_by_month,
    format_brl,
    load_orders,
    revenue_by_channel,
    revenue_by_month,
    top_products_by_quantity,
)

st.set_page_config(page_title="Kubica em Números", layout="wide")


@st.cache_data
def get_orders():
    return load_orders()


def to_frame(series, label_name, value_name):
    """Turn a Series into a two-column DataFrame, ready for st.bar_chart."""
    return series.rename(value_name).rename_axis(label_name).reset_index()


def show_chart(title, series, label_name, value_name, horizontal=False):
    st.subheader(title)
    st.bar_chart(
        to_frame(series, label_name, value_name),
        x=label_name,
        y=value_name,
        horizontal=horizontal,
        sort=False,  # keep the order given by analysis.py (months in sequence)
    )


orders = get_orders()

st.title("Kubica em Números")
st.caption("Painel de vendas com dados fictícios, de janeiro a outubro de 2026.")

st.metric("Ticket médio", format_brl(average_ticket(orders)))

left, right = st.columns(2)
with left:
    show_chart(
        "Faturamento por mês (R$)",
        revenue_by_month(orders),
        "Mês",
        "Faturamento (R$)",
    )
    show_chart(
        f"Top {TOP_PRODUCTS} produtos mais vendidos",
        top_products_by_quantity(orders),
        "Produto",
        "Unidades vendidas",
        horizontal=True,
    )
with right:
    show_chart(
        "Faturamento por canal (R$)",
        revenue_by_channel(orders),
        "Canal",
        "Faturamento (R$)",
    )
    show_chart(
        "Ticket médio por mês (R$)",
        average_ticket_by_month(orders),
        "Mês",
        "Ticket médio (R$)",
    )
