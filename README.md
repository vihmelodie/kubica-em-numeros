# Kubica em Números

Painel de vendas em Python e Streamlit que reúne os pedidos de três canais (Shopee, TikTok Shop e Nuvemshop) em um só lugar e permite fazer perguntas em linguagem natural sobre os números, respondidas pela API do Claude.

Desenvolvido com apoio do Claude Code.

## O problema que resolve

Quem vende em vários marketplaces costuma conferir os números canal por canal, em painéis diferentes. O "Kubica em Números" centraliza as vendas em uma única tela, com gráficos de faturamento, ticket médio e produtos mais vendidos. A caixa **"Pergunte aos dados"** permite fazer perguntas como "Qual canal teve o maior faturamento?" sem montar filtros ou tabelas.

## Captura de tela

<!-- Adicione aqui a imagem do app, por exemplo: ![Painel Kubica em Números](docs/screenshot.png) -->

## App publicado

<!-- Adicione aqui o link do app no Streamlit Community Cloud depois da publicação. -->

## Como rodar localmente

Requisitos: Python 3.13.

```bash
# 1. Crie e ative o ambiente virtual (Windows)
python -m venv .venv
.venv\Scripts\activate

# No macOS/Linux: source .venv/bin/activate

# 2. Instale as dependências
pip install -r requirements.txt
```

3. Crie o arquivo `.streamlit/secrets.toml` com a sua chave da API da Anthropic:

```toml
ANTHROPIC_API_KEY = "sua-chave-aqui"
```

Esse arquivo está no `.gitignore` e nunca deve ser enviado ao repositório.

```bash
# 4. Inicie o app
streamlit run app.py
```

O painel funciona sem a chave; apenas a caixa "Pergunte aos dados" depende dela.

## Como a IA é usada

O app **não envia a tabela de pedidos** para a API. Antes de cada pergunta, ele calcula um resumo agregado (faturamento total e por mês e canal, ticket médio, pedidos por canal e totais por produto) e envia somente esse resumo, junto com a pergunta. Dados de clientes não fazem parte do resumo. O modelo usado é o Claude Haiku e responde no idioma da pergunta (português ou inglês). Se a resposta não estiver no resumo, ele diz que não sabe.

## Avaliação (eval)

O script `evals/run_eval.py` faz 10 perguntas (português e inglês) com respostas conhecidas, em 3 rodadas. Resultado: **28/30 acertos** (10/10, 9/10 e 9/10). O relatório completo está em [`evals/results.md`](evals/results.md).

**Limitação:** os dois erros ocorreram na mesma pergunta (*"How many orders came from Nuvemshop?"*), com a resposta *"Nuvemshop received 81 orders."*. O número estava correto, mas a checagem de idioma, que conta palavras comuns de cada língua, não conseguiu identificar o idioma de uma resposta tão curta. Ou seja, são limitações da checagem automática em respostas curtas, e não um valor errado.

## Tecnologias

- Python 3.13
- Pandas
- Streamlit
- SDK da Anthropic para Python (modelo Claude Haiku)
- Publicação no Streamlit Community Cloud

## Dados fictícios

Todos os dados do repositório (`data/sample_orders.csv`) são fictícios, gerados por `data/generate_sample_data.py`, no mesmo formato dos dados reais da empresa. Nenhum dado real de clientes ou da Kubica é publicado aqui.

---

# English

## Kubica em Números

A sales dashboard built with Python and Streamlit that brings orders from three channels (Shopee, TikTok Shop and Nuvemshop) into a single view and lets you ask questions about the numbers in natural language, answered by the Claude API.

Developed with support from Claude Code.

### The problem it solves

Sellers on several marketplaces usually check their numbers channel by channel, in separate dashboards. Kubica em Números centralizes sales in one screen, with charts for revenue, average ticket and top products. The **"Pergunte aos dados"** (Ask the data) box lets you ask questions such as "Which channel had the highest revenue?" without building filters or tables.

### Screenshot

<!-- Add the app image here, for example: ![Kubica em Números dashboard](docs/screenshot.png) -->

### Live app

<!-- Add the Streamlit Community Cloud link here after publishing. -->

### Running locally

Requirements: Python 3.13.

```bash
# 1. Create and activate the virtual environment (Windows)
python -m venv .venv
.venv\Scripts\activate

# On macOS/Linux: source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
```

3. Create `.streamlit/secrets.toml` with your Anthropic API key:

```toml
ANTHROPIC_API_KEY = "your-key-here"
```

This file is listed in `.gitignore` and must never be committed.

```bash
# 4. Start the app
streamlit run app.py
```

The dashboard works without the key; only the "Pergunte aos dados" box needs it.

### How the AI is used

The app **does not send the orders table** to the API. Before each question, it computes an aggregated summary (total revenue, revenue by month and channel, average ticket, orders per channel and totals per product) and sends only that summary along with the question. Customer data is not part of the summary. The model is Claude Haiku, and it answers in the language of the question (Portuguese or English). If the answer is not in the summary, it says it does not know.

### Evaluation

The `evals/run_eval.py` script asks 10 questions (Portuguese and English) with known answers, in 3 rounds. Result: **28/30 correct** (10/10, 9/10 and 9/10). The full report is in [`evals/results.md`](evals/results.md).

**Limitation:** both misses were on the same question (*"How many orders came from Nuvemshop?"*), answered as *"Nuvemshop received 81 orders."*. The number was correct, but the language check, which counts common words of each language, could not identify the language of such a short answer. These are limitations of the automatic check on short answers, not wrong values.

### Technologies

- Python 3.13
- Pandas
- Streamlit
- Anthropic SDK for Python (Claude Haiku model)
- Deployed on Streamlit Community Cloud

### Fictional data

All data in this repository (`data/sample_orders.csv`) is fictional, generated by `data/generate_sample_data.py`, in the same format as the company's real data. No real customer or Kubica data is published here.
