"""Evaluate the "Ask the data" AI against answers computed with Pandas.

Run from the project root:

    python evals/run_eval.py             # 3 rounds (30 real API calls)
    python evals/run_eval.py --rounds 1  # a single round (10 calls)

Makes one real API call per question in each round, to Claude Haiku. The correct
answers come from the sample dataset, never from hand-written numbers. Besides
the tables in the terminal, the full results are saved in evals/results.md.
"""

import argparse
import contextlib
import io
import logging
import re
import sys
import textwrap
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable

import anthropic

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
logging.getLogger("streamlit").setLevel(logging.ERROR)

from analysis import MONTH_NAMES, load_orders  # noqa: E402

# Importing app.py runs it in bare mode, which prints a Streamlit notice to stderr.
with contextlib.redirect_stderr(io.StringIO()):
    from app import MODEL, MONTH_NAMES_EN, ask_claude, build_summary  # noqa: E402

DEFAULT_ROUNDS = 3
MONEY_TOLERANCE = 0.01
UNKNOWN_PHRASES = ("nao sei", "i don't know", "i do not know")
ANSWER_PREVIEW_CHARS = 30
TABLE_HEADER = ("#", "Idioma", "Pergunta", "Esperado", "Resposta da IA", "Resultado")
REPORT_PATH = Path(__file__).parent / "results.md"

# Function words used to tell Portuguese from English (words that exist in both
# languages, such as "a", "e", "as", "do" or "no", are left out on purpose).
PT_WORDS = {
    "o", "os", "de", "da", "dos", "das", "em", "nos", "nas", "um", "uma", "foi",
    "que", "para", "por", "com", "mais", "nao", "ao", "entre", "teve", "vendeu",
    "gerou", "faturou", "sao", "pelo", "pela", "periodo", "ficou", "tem",
}
EN_WORDS = {
    "the", "of", "in", "was", "were", "with", "for", "to", "is", "are", "and",
    "from", "that", "this", "by", "most", "had", "has", "it", "its", "on", "at",
    "i", "don't", "know", "not", "which", "came", "total", "sold", "generated",
}
LANGUAGE_NAMES = {"pt": "português", "en": "inglês"}


@dataclass
class Case:
    language: str
    question: str
    expected_text: str
    check: Callable[[str], tuple[bool, str]]  # returns (passed, reason if failed)


@dataclass
class Result:
    number: int
    case: Case
    answer: str
    status: str
    note: str


def normalize(text):
    """Lowercase, drop accents and unify apostrophes for loose comparisons."""
    text = text.replace("’", "'")
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def plain_words(text):
    """Words only, without accents, case or punctuation."""
    return " ".join(re.findall(r"\w+", normalize(text)))


def repeats_question(question, answer):
    return plain_words(question) in plain_words(answer)


def detect_language(answer):
    """Return 'pt' or 'en' by counting function words, or None if undecided."""
    words = re.findall(r"[a-z']+", normalize(answer))
    pt_hits = sum(1 for word in words if word in PT_WORDS)
    en_hits = sum(1 for word in words if word in EN_WORDS)
    if pt_hits == en_hits:
        return None
    return "pt" if pt_hits > en_hits else "en"


def first_mentioned(answer, candidates):
    """Return the candidate whose name appears first in the answer, if any."""
    text = normalize(answer)
    best, best_position = None, None
    for canonical, variants in candidates.items():
        for variant in variants:
            match = re.search(rf"\b{re.escape(normalize(variant))}\b", text)
            if match and (best_position is None or match.start() < best_position):
                best, best_position = canonical, match.start()
    return best


def parse_number(token):
    """Parse '1.234,56', '1,234.56', '44.93' or '81' into a float."""
    for separator, other in ((",", "."), (".", ",")):
        if separator in token and other in token:
            if token.rfind(separator) > token.rfind(other):  # separator is decimal
                return float(token.replace(other, "").replace(separator, "."))
    for separator in (",", "."):
        if separator in token:
            head, _, tail = token.rpartition(separator)
            if token.count(separator) > 1 or len(tail) == 3:  # thousands separator
                return float(token.replace(separator, ""))
            return float(f"{head}.{tail}")
    return float(token)


def numbers_in(answer):
    return [parse_number(token) for token in re.findall(r"\d+(?:[.,]\d+)*", answer)]


def format_number(value):
    return str(int(value)) if value == int(value) else f"{value:.2f}"


def name_case(language, question, expected, expected_text, candidates):
    """The right name must be the first one mentioned in the answer."""

    def check(answer):
        if first_mentioned(answer, candidates) != expected:
            return False, "o nome certo não é o primeiro citado"
        return True, ""

    return Case(language, question, expected_text, check)


def number_case(language, question, expected_numbers):
    """Every expected number must appear in the answer."""

    def check(answer):
        found = numbers_in(answer)
        missing = [
            n for n in expected_numbers
            if not any(abs(value - n) <= MONEY_TOLERANCE for value in found)
        ]
        if missing:
            return False, "número ausente: " + ", ".join(map(format_number, missing))
        return True, ""

    shown = ", ".join(format_number(n) for n in expected_numbers)
    return Case(language, question, shown, check)


def unknown_case(language, question):
    def check(answer):
        text = normalize(answer)
        if any(phrase in text for phrase in UNKNOWN_PHRASES):
            return True, ""
        return False, 'não disse "não sei"'

    return Case(language, question, "não sei", check)


def build_cases(orders):
    """Build the 10 questions, with every correct answer computed from the data."""
    month = orders["order_date"].dt.month
    channels = {name: [name] for name in orders["channel"].unique()}
    products = {name: [name] for name in orders["product"].unique()}
    months = {n: [MONTH_NAMES[n], MONTH_NAMES_EN[n]] for n in MONTH_NAMES}

    channel_revenue = orders.groupby("channel")["total"].sum()
    product_units = orders.groupby("product")["quantity"].sum()
    product_revenue = orders.groupby("product")["total"].sum()
    month_revenue = orders.groupby(month)["total"].sum()
    shopee_october = orders[(orders["channel"] == "Shopee") & (month == 10)]["total"]
    may_ticket = orders[month == 5]["total"].mean()
    nuvemshop_orders = int((orders["channel"] == "Nuvemshop").sum())

    # The "unknown" question only makes sense if the data has no customer column.
    customer_columns = [c for c in orders.columns if "customer" in c or "client" in c]
    assert not customer_columns, "Dataset has customer data; pick another question."

    top_channel = channel_revenue.idxmax()
    top_product = product_units.idxmax()
    top_revenue_product = product_revenue.idxmax()
    top_month = month_revenue.idxmax()

    return [
        name_case("pt", "Qual canal teve o maior faturamento?",
                  top_channel, top_channel, channels),
        number_case("pt", "Qual foi o faturamento total?", [orders["total"].sum()]),
        name_case("pt", "Qual produto vendeu mais unidades?",
                  top_product, top_product, products),
        number_case("pt", "Qual foi o ticket médio?", [orders["total"].mean()]),
        name_case("pt", "Em qual mês o faturamento foi maior?",
                  top_month, MONTH_NAMES[top_month], months),
        number_case("pt", "Quanto a Shopee faturou em outubro?",
                    [shopee_october.sum()]),
        name_case("en", "Which product generated the most revenue?",
                  top_revenue_product, top_revenue_product, products),
        number_case("en", "How many orders came from Nuvemshop?", [nuvemshop_orders]),
        number_case("en", "What was the average ticket in May?", [may_ticket]),
        unknown_case("pt", "Quantos clientes diferentes fizeram pedidos?"),
    ]


def check_answer(case, answer):
    """Apply the rules shared by every question, then the question's own rule."""
    if repeats_question(case.question, answer):
        return False, "a resposta repete a pergunta"
    detected = detect_language(answer)
    if detected != case.language:
        found = LANGUAGE_NAMES.get(detected, "idioma não identificado")
        expected = LANGUAGE_NAMES[case.language]
        return False, f"a resposta deveria estar em {expected} (detectado: {found})"
    return case.check(answer)


def run_case(case, summary):
    """Ask the app's AI one question; return (answer, status, note)."""
    try:
        answer = ask_claude(case.question, summary)
    except (KeyError, FileNotFoundError):  # secret not configured
        return "", "Falha (chave)", "a chave da API não está configurada"
    except anthropic.APIError:
        return "", "Falha (API)", "a chamada à API falhou"
    passed, note = check_answer(case, answer)
    return answer, "Acerto" if passed else "Erro", note


def count_hits(results):
    return sum(1 for r in results if r.status == "Acerto")


def print_table(results):
    """Print the results with left-aligned, fixed-width columns."""
    widths = [2, 6, 44, 17, ANSWER_PREVIEW_CHARS, 9]
    rows = [TABLE_HEADER]
    for r in results:
        preview = textwrap.shorten(r.answer, ANSWER_PREVIEW_CHARS, placeholder="...")
        rows.append((str(r.number), r.case.language, r.case.question,
                     r.case.expected_text, preview, r.status))
    for row in rows:
        print("  ".join(cell.ljust(width) for cell, width in zip(row, widths)))


def write_report(rounds):
    """Save question, correct answer, full AI answer and result of every round."""
    per_round = len(rounds[0])
    total_hits = sum(count_hits(results) for results in rounds)
    lines = [
        "# Resultados do eval",
        "",
        f"- Data: {date.today().isoformat()}",
        f"- Modelo: `{MODEL}`",
        f"- Rodadas: {len(rounds)} ({per_round} perguntas cada)",
        f"- Total de acertos: **{total_hits}/{len(rounds) * per_round}**",
        "",
        "## Acertos por rodada",
        "",
        "| Rodada | Acertos |",
        "|---|---|",
    ]
    for index, results in enumerate(rounds, start=1):
        lines.append(f"| {index} | {count_hits(results)}/{per_round} |")

    round_headers = " | ".join(f"Rodada {i}" for i in range(1, len(rounds) + 1))
    lines += [
        "",
        "## Resultado por pergunta",
        "",
        f"| # | Idioma | Pergunta | Resposta certa | {round_headers} |",
        "|---|---|---|---|" + "---|" * len(rounds),
    ]
    for position, first in enumerate(rounds[0]):
        statuses = " | ".join(results[position].status for results in rounds)
        lines.append(
            f"| {first.number} | {first.case.language} | {first.case.question} | "
            f"{first.case.expected_text} | {statuses} |"
        )

    for index, results in enumerate(rounds, start=1):
        lines += ["", f"## Rodada {index}: {count_hits(results)}/{per_round}"]
        for r in results:
            lines += [
                "",
                f"### {r.number}. {r.case.question}",
                "",
                f"- **Idioma:** {r.case.language}",
                f"- **Resposta certa:** {r.case.expected_text}",
                f"- **Resultado:** {r.status}",
            ]
            if r.note:
                lines.append(f"- **Motivo:** {r.note}")
            # Code block so GitHub does not render paired "$" signs as math.
            lines += ["- **Resposta completa da IA:**", "", "```text",
                      r.answer or "(sem resposta)", "```"]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rounds", type=int, default=DEFAULT_ROUNDS,
                        help=f"number of rounds (default {DEFAULT_ROUNDS})")
    rounds_wanted = parser.parse_args().rounds

    sys.stdout.reconfigure(encoding="utf-8")
    orders = load_orders()
    summary = build_summary(orders)
    cases = build_cases(orders)

    rounds = []
    for index in range(1, rounds_wanted + 1):
        print(f"Rodada {index}/{rounds_wanted}: enviando {len(cases)} perguntas "
              "à IA do app...\n")
        results = [
            Result(number, case, *run_case(case, summary))
            for number, case in enumerate(cases, start=1)
        ]
        print_table(results)
        print(f"\nRodada {index}: {count_hits(results)}/{len(cases)}\n")
        rounds.append(results)

    total_hits = sum(count_hits(results) for results in rounds)
    per_round = " | ".join(
        f"Rodada {i}: {count_hits(r)}/{len(cases)}" for i, r in enumerate(rounds, 1)
    )
    print(per_round)
    print(f"Total de acertos: {total_hits}/{rounds_wanted * len(cases)}")
    write_report(rounds)
    print(f"Resultados completos salvos em {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
