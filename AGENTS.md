# Importador SisUAB
Gera o CSV do SisUAB2 a partir de matrículas UAB, 100% local. Python 3.12 · Streamlit · Ollama.
Docs: `docs/mvp-scope.md` · `docs/prd.md` · `docs/spec.md`

## Comandos
- Dev: `python -m streamlit run app.py`
- Lint/format: `ruff check .` · `ruff format .`
- Testes: `pytest --cov=core --cov-fail-under=85` · `pytest -m smoke`
- Docker: `docker compose up -d --build` (Linux: `--profile ollama`)

## Padrões
- Textos da usuária só em `core/messages.py` e `ui/texts.py`
- Strings em NFC; dígitos via `[0-9]`, nunca `isdigit()`
- Exceções herdam de `ImportadorError`

## NUNCA
- streamlit em `core/`; requests fora de `core/llm/client.py` (INV-01)
- Dado de aluno em disco ou `st.cache_data` (ADR-02)
- Campo como int/float (ADR-06)
- Saída do LLM sem normalize + validate (ADR-03)
- Aplicar sugestão da IA sem confirmação (INV-12)
- `unsafe_allow_html`, fonte ou CDN externa (ADR-09)
- Host fora de `ALLOWED_OLLAMA_HOSTS` ou modelo remoto (INV-08, INV-14)
- Quando cometer um erro, registrar aqui a correção

## Stack fixada
ADRs fechados, não propor alternativas: Streamlit monolítico · estado em memória · Ollama via requests · CSV `QUOTE_NONE` · verificação independente.

## Diretórios
`core/` regras · `ui/` Streamlit · `config/` polos e DDDs · `tests/` · `tools/` benchmark

## Invariantes e build
INV-01–15 em spec §10.4; toda mudança passa por `bump_revision`. Build em spec §11, sem pular checkpoint. Passo atual: 28 (implementação local concluída; CI em push e importação piloto no SisUAB pendentes de acesso externo)

## Edge cases
- CPF duplicado, mesmo idêntico → ERRO, nunca remover sozinho
- Telefone de 8 dígitos → ERRO, nunca prefixar 9
- Polo aproximado → só sugestão

## Execução
- Toque apenas no que o pedido exige — não refatore, reformate nem "melhore" código adjacente
- Remova só os órfãos que suas mudanças criaram; código morto pré-existente, apenas mencione
- Ambiguidade: declare o que está confuso e pergunte antes de implementar
- Interpretações múltiplas: apresente-as, não escolha em silêncio
- Combine com o estilo existente do arquivo, mesmo que você faria diferente

## Correções registradas
- `header_key("Nº do CPF")` produz `nodocpf` por decomposição Unicode; o teste foi corrigido para esse valor.
- O smoke inicial no Windows deixava o processo filho do Python aberto; o teste agora encerra a árvore de processos e consulta o healthcheck por HTTP local.
- O chat deixava o modelo recusar CPF pontuado válido ou devolver JSON inválido em pedidos simples; correção explícita e explicação de erro por número de registro agora usam validação local e continuam exigindo confirmação para aplicar.
- A primeira correção do chat tratava apenas CPF; pedidos explícitos de valor por registro agora cobrem os sete campos, validam o valor normalizado e não separam um DDD incluído no telefone sem confirmação própria.
- A navegação com `st.radio` e chave própria emitia aviso quando também recebia `index`; a seleção inicial agora vem somente do estado de sessão, e os botões atualizam essa mesma chave antes da nova execução.
