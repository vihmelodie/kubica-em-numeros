# Kubica em Números

## 1. Objetivo

"Kubica em Números" é um painel de vendas da Kubica, empresa de produtos impressos em 3D. Ele é feito em Python e Streamlit e tem uma caixa **"Pergunte aos dados"**, respondida pela API do Claude (modelo Haiku).

A versão pública usa dados fictícios no mesmo formato dos dados reais da Kubica.

## 2. Ferramentas

- Python 3.13 (versão do projeto, tanto local quanto no Streamlit Cloud)
- Pandas
- Streamlit
- SDK da Anthropic para Python
- Publicação no Streamlit Community Cloud

## 3. Convenções

- Seguir o PEP 8.
- `snake_case` para variáveis, funções e arquivos.
- `PascalCase` para classes.
- `MAIÚSCULAS` para constantes.
- Nomes no código em inglês.
- README e textos do app em português.
- Fazer commits pequenos, com mensagens claras em inglês.

## 4. Regras de segurança

- Nunca enviar dados reais de clientes nem da Kubica para o GitHub. Usar somente dados fictícios.
- Nunca colocar a chave da API no código.
- Manter `.env` e `.streamlit/secrets.toml` no `.gitignore`.
- Este repositório é público: textos, comentários e mensagens de commit devem ter tom profissional e não podem expor dados pessoais nem dados reais da Kubica.
