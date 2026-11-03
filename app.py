"""Streamlit dashboard "Kubica em Números", built on the logic in analysis.py."""

import json

import altair as alt
import anthropic
import streamlit as st

from analysis import (
    MONTH_NAMES,
    TOP_PRODUCTS,
    average_ticket,
    average_ticket_by_month,
    format_brl,
    load_orders,
    revenue_by_channel,
    revenue_by_month,
    top_products_by_quantity,
)

MODEL = "claude-haiku-5-5"
MAX_TOKENS = 2000
MAX_QUESTION_CHARS = 300

LANGUAGES = {"Português": "pt", "English": "en"}

MONTH_NAMES_EN = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}
PT_TO_EN = {MONTH_NAMES[number]: MONTH_NAMES_EN[number] for number in MONTH_NAMES}

# The interface language comes from the selector; the AI answers in the language
# of the question, so the prompts and the summary do not depend on the selector.
SUMMARY_LANGUAGE = "en"
SYSTEM_PROMPT = (
    "LANGUAGE RULE: reply in the same language as the user's question (a "
    "Portuguese question gets a Portuguese answer, an English question gets an "
    "English answer), whatever language the sales summary uses. "
    "You are a data analyst for a store that sells 3D-printed products. "
    "Use only the numbers in the sales summary provided "
    "(values in Brazilian reais, R$). "
    "Answer in up to 4 sentences and start directly with the fact: do not repeat "
    "or restate the question. "
    "Never mention internal field names from the summary (such as "
    "orders_by_channel); describe the data in plain words instead. "
    "If the summary does not contain the answer, say you do not know, in the "
    "language of the question (for example \"não sei\" or \"I don't know\"). "
    "Do not make up numbers.\n\n"
    "Format examples (made-up numbers, only to show the format):\n"
    "Question: Qual canal vendeu mais?\n"
    "Answer: O Canal A vendeu mais, com R$ 1.000,00.\n"
    "Question: Which product sold the most units?\n"
    "Answer: Product B sold the most units, with 50 units.\n\n"
    "Remember: reply in the language of the question, starting directly with "
    "the answer."
)
USER_PROMPT = "Sales summary (JSON):\n{summary}\n\nQuestion: {question}"

TEXTS = {
    "pt": {
        "title": "Kubica em Números",
        "caption": "Painel de vendas com dados fictícios, de janeiro a outubro de 2026.",
        "average_ticket": "Ticket médio",
        "chart_revenue_by_month": "Faturamento por mês (R$)",
        "chart_revenue_by_channel": "Faturamento por canal (R$)",
        "chart_top_products": "Top {n} produtos mais vendidos",
        "chart_ticket_by_month": "Ticket médio por mês (R$)",
        "label_month": "Mês",
        "label_channel": "Canal",
        "label_product": "Produto",
        "label_revenue": "Faturamento (R$)",
        "label_units": "Unidades vendidas",
        "label_ticket": "Ticket médio (R$)",
        "ask_title": "Pergunte aos dados",
        "ask_label": "Escreva uma pergunta sobre as vendas",
        "ask_placeholder": "Ex.: Qual canal vendeu mais?",
        "ask_button": "Perguntar",
        "ask_empty": "Escreva uma pergunta antes de enviar.",
        "ask_spinner": "Analisando os dados...",
        "error_generic": (
            "Não foi possível responder agora. Tente novamente em instantes."
        ),
        "error_no_key": (
            "A chave de acesso à API não está configurada neste ambiente, "
            "então a resposta não está disponível."
        ),
    },
    "en": {
        "title": "Kubica in Numbers",
        "caption": "Sales dashboard with fictional data, from January to October 2026.",
        "average_ticket": "Average ticket",
        "chart_revenue_by_month": "Revenue by month (R$)",
        "chart_revenue_by_channel": "Revenue by channel (R$)",
        "chart_top_products": "Top {n} best-selling products",
        "chart_ticket_by_month": "Average ticket by month (R$)",
        "label_month": "Month",
        "label_channel": "Channel",
        "label_product": "Product",
        "label_revenue": "Revenue (R$)",
        "label_units": "Units sold",
        "label_ticket": "Average ticket (R$)",
        "ask_title": "Ask the data",
        "ask_label": "Write a question about the sales",
        "ask_placeholder": "E.g.: Which channel sold the most?",
        "ask_button": "Ask",
        "ask_empty": "Write a question before submitting.",
        "ask_spinner": "Analyzing the data...",
        "error_generic": "We could not answer right now. Please try again shortly.",
        "error_no_key": (
            "The API access key is not configured in this environment, "
            "so answers are not available."
        ),
    },
}

st.set_page_config(page_title="Kubica em Números", layout="wide")


@st.cache_data
def get_orders():
    return load_orders()


def translate_months(series, language):
    """Month names come in Portuguese from analysis.py; translate if needed."""
    if language == "en":
        return series.rename(index=PT_TO_EN)
    return series


def escape_dollars(value):
    """Streamlit renders paired $ signs as LaTeX; escape them to show R$ as text."""
    return value.replace("$", r"\$")


def to_frame(series, label_name, value_name):
    """Turn a Series into a two-column DataFrame, ready for the chart."""
    return series.rename(value_name).rename_axis(label_name).reset_index()


def number_axis(language, title):
    """Value axis whose tick labels follow the language: 3.500 (pt) or 3,500 (en)."""
    if language == "pt":
        # Swap separators through a placeholder: "," -> "_", "." -> ",", "_" -> "."
        label_expr = (
            "replace(replace(replace(format(datum.value, ','), "
            "regexp(',', 'g'), '_'), regexp('\\\\.', 'g'), ','), "
            "regexp('_', 'g'), '.')"
        )
        return alt.Axis(title=title, labelExpr=label_expr)
    return alt.Axis(title=title, format=",")


def show_chart(title, series, label_name, value_name, language, horizontal=False):
    st.subheader(escape_dollars(title))
    frame = to_frame(series, label_name, value_name)
    # sort=None keeps the order given by analysis.py (months in sequence)
    label_axis = alt.Axis(title=label_name)
    value_axis = number_axis(language, value_name)
    if horizontal:
        encoding = {
            "x": alt.X(f"{value_name}:Q", axis=value_axis),
            "y": alt.Y(f"{label_name}:N", sort=None, axis=label_axis),
        }
    else:
        encoding = {
            "x": alt.X(f"{label_name}:N", sort=None, axis=label_axis),
            "y": alt.Y(f"{value_name}:Q", axis=value_axis),
        }
    st.altair_chart(
        alt.Chart(frame).mark_bar().encode(**encoding), width="stretch"
    )


def build_summary(orders):
    """Aggregate numbers only: the full orders table is never sent to the API."""
    by_product = orders.groupby("product").agg(
        units_sold=("quantity", "sum"), revenue=("total", "sum")
    )
    by_channel = orders.groupby("channel").agg(
        orders=("order_id", "count"), revenue=("total", "sum")
    )
    channel_by_month = (
        orders.groupby([orders["order_date"].dt.month, "channel"])["total"]
        .sum()
        .unstack(fill_value=0)
        .round(2)
    )
    channel_by_month.index = channel_by_month.index.map(MONTH_NAMES_EN)
    monthly_revenue = translate_months(revenue_by_month(orders), SUMMARY_LANGUAGE)
    monthly_ticket = translate_months(
        average_ticket_by_month(orders), SUMMARY_LANGUAGE
    )

    return {
        "period": (
            f"{orders['order_date'].min().date()} to {orders['order_date'].max().date()}"
        ),
        "currency": "BRL",
        "total_orders": int(len(orders)),
        "total_revenue": round(float(orders["total"].sum()), 2),
        "average_ticket": round(float(average_ticket(orders)), 2),
        "revenue_by_month": monthly_revenue.round(2).to_dict(),
        "average_ticket_by_month": monthly_ticket.round(2).to_dict(),
        "revenue_by_channel": revenue_by_channel(orders).round(2).to_dict(),
        "revenue_by_channel_by_month": channel_by_month.to_dict(orient="index"),
        "orders_by_channel": by_channel["orders"].astype(int).to_dict(),
        "top_products_by_quantity": {
            product: int(units)
            for product, units in top_products_by_quantity(orders).items()
        },
        "totals_by_product": {
            product: {
                "units_sold": int(row["units_sold"]),
                "revenue": round(float(row["revenue"]), 2),
            }
            for product, row in by_product.iterrows()
        },
    }


def ask_claude(question, summary):
    """Send the question and the summary to Claude; return the answer text."""
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        output_config={"effort": "low"},
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": USER_PROMPT.format(
                    summary=json.dumps(summary, ensure_ascii=False, indent=2),
                    question=question,
                ),
            }
        ],
    )
    if response.stop_reason == "refusal":
        return ""
    return "".join(block.text for block in response.content if block.type == "text")


def show_ask_section(orders, text):
    st.header(text["ask_title"])
    with st.form("ask_form"):
        question = st.text_input(
            text["ask_label"],
            placeholder=text["ask_placeholder"],
            max_chars=MAX_QUESTION_CHARS,
        )
        submitted = st.form_submit_button(text["ask_button"])

    if not submitted:
        return
    if not question.strip():
        st.warning(text["ask_empty"])
        return

    try:
        with st.spinner(text["ask_spinner"]):
            answer = ask_claude(question.strip(), build_summary(orders))
    except (KeyError, FileNotFoundError):  # secret not configured
        st.error(text["error_no_key"])
    except anthropic.APIError:
        st.error(text["error_generic"])
    else:
        if answer:
            st.write(escape_dollars(answer))
        else:
            st.error(text["error_generic"])


language_name = st.radio(
    "Idioma / Language", list(LANGUAGES), horizontal=True, index=0
)
language = LANGUAGES[language_name]
text = TEXTS[language]

orders = get_orders()

st.title(text["title"])
st.caption(text["caption"])

st.metric(text["average_ticket"], format_brl(average_ticket(orders)))

show_ask_section(orders, text)

left, right = st.columns(2)
with left:
    show_chart(
        text["chart_revenue_by_month"],
        translate_months(revenue_by_month(orders), language),
        text["label_month"],
        text["label_revenue"],
        language,
    )
    show_chart(
        text["chart_top_products"].format(n=TOP_PRODUCTS),
        top_products_by_quantity(orders),
        text["label_product"],
        text["label_units"],
        language,
        horizontal=True,
    )
with right:
    show_chart(
        text["chart_revenue_by_channel"],
        revenue_by_channel(orders),
        text["label_channel"],
        text["label_revenue"],
        language,
    )
    show_chart(
        text["chart_ticket_by_month"],
        translate_months(average_ticket_by_month(orders), language),
        text["label_month"],
        text["label_ticket"],
        language,
    )
