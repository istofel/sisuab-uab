# MVP Scope — Importador SisUAB

**Versão:** 1.0 · **Data:** 23/09/2026 · **Status:** aguardando aprovação
**Fonte de verdade:** manual CAPES "Novo Modelo de Arquivo" + seção "Correções ao manual" do prompt original. Em caso de conflito, as correções prevalecem.
**Decisões já aprovadas:** validação contextual parcial (só período atual) · CPF duplicado é sempre ERRO, com correção manual · extração híbrida de PDF/DOCX/TXT.

---

## 1. Visão Geral do Produto

**Nome:** Importador SisUAB (**Premissa**: nome provisório)
**Tagline:** Da planilha bagunçada ao CSV que o SisUAB aceita, sem que nenhum dado saia do computador.

**Descrição:** aplicação web local (Streamlit) que recebe arquivos de matrícula de alunos UAB em PDF, CSV, XLSX/XLS, DOCX, JSON ou TXT. Ela extrai e consolida os registros, normaliza e valida cada campo com código determinístico e gera um único CSV no leiaute "Novo Modelo de Arquivo" do SisUAB2. Uma IA local (Ollama) ajuda apenas a ler texto livre, sugerir o mapeamento de colunas e propor correções pelo chat.

**Problema que resolve:**
- A secretária recebe dados em formatos diferentes: um arquivo por polo, planilha geral, lista em PDF, documento Word.
- O SisUAB ignora as linhas incorretas (manual, §4, regras 7 a 9), e o erro só aparece depois da importação.
- Há armadilhas técnicas invisíveis para quem não é da área: BOM do Excel, vírgula como separador, CPF sem zero à esquerda, notação científica, polo com grafia diferente e acento decomposto.
- Usar IA em nuvem para "arrumar a planilha" expõe CPF, e-mail e telefone a terceiros, o que é um risco perante a LGPD.

**Proposta de valor:** CSV aceito na primeira importação, com cada erro apontado por linha e campo, em português. A privacidade é garantida pela arquitetura, porque nada sai da máquina.

**Diferenciais:**
- Validação 100% determinística e coberta por testes. A IA nunca decide o conteúdo do CSV.
- Verificação final feita nos bytes do arquivo gerado (sem BOM, UTF-8 estrito, 7 campos) antes de liberar o download.
- Funciona sem IA para entradas estruturadas: se o Ollama estiver offline, CSV, XLSX, JSON e tabelas continuam funcionando.

---

## 2. Pesquisa de Mercado e Público-Alvo

Trata-se de uma ferramenta institucional, não de um produto comercial. Aqui, "mercado" são as instituições e coordenações que alimentam o SisUAB.

### 2.1 Tamanho de mercado

| Nível | Definição | Tamanho |
|-------|-----------|---------|
| TAM | IES públicas do Sistema UAB que cadastram alunos no SisUAB | O Edital CAPES nº 09/2022 selecionou propostas de IES públicas dos 26 estados e do DF, somando 131.102 vagas (fonte: O Imparcial, abr/2022, com base no resultado publicado no DOU). Número de IES: **estimativa** de 100 a 130 |
| SAM | Coordenações UAB que recebem dados heterogêneos dos polos e montam o CSV à mão | **estimativa**: a maioria das IES do TAM |
| SOM | IFTO, com 23 polos no Tocantins, no MVP; outras IES via GitHub depois | 1 IES e 1 a 3 usuárias (**Premissa**) |

### 2.2 Tendências relevantes

1. A LGPD (Lei 13.709/2018) pressiona órgãos públicos a não compartilhar dados pessoais com serviços de IA em nuvem.
2. LLMs locais de 3 a 8B parâmetros, quantizados, rodam em computadores comuns via Ollama (**estimativa** de desempenho, a medir na SPEC).
3. O Ollama aceita JSON Schema no parâmetro `format`, o que torna a saída estruturada confiável e dispensa parsing frágil.
4. Novas ofertas UAB por edital geram cargas de alunos recorrentes a cada semestre (**estimativa**).

### 2.3 Mapa competitivo

| Concorrente | Pontos fortes | Lacunas | Posicionamento |
|-------------|---------------|---------|----------------|
| Processo manual (Excel ou LibreOffice + manual CAPES) | Conhecido, sem instalação | Erros de BOM, separador e zeros; não valida CPF; retrabalho | Status quo a substituir |
| Importação direta no SisUAB | Oficial; valida CPF | Descarta linhas incorretas sem orientar a correção; não consolida várias fontes | É o destino, não um concorrente |
| IA em nuvem (ChatGPT, Gemini, Copilot) | Lê qualquer formato | Envia dados pessoais a terceiros; resultado não determinístico; pode inventar dados | Proibida pelo requisito de privacidade |
| Planilhas-modelo e scripts internos | Baratos | Frágeis, dependem de quem criou, não leem PDF nem DOCX | Substituídos por uma ferramenta testada |
| Validadores de CSV genéricos | Validam estrutura | Desconhecem as regras do SisUAB; muitos são online | Irrelevantes para o domínio |

### 2.4 Personas

**Persona primária: Márcia (fictícia)**, secretária da coordenação UAB do IFTO.
- Contexto: recebe listas dos 23 polos no início de cada oferta e nas atualizações; usa Excel e navegador; nunca usou terminal.
- Dores: importação rejeitada sem explicação clara; conferir CPF a olho; cada polo manda os dados num formato diferente.
- Job-to-be-done: "Quando as listas dos polos chegam, quero gerar um arquivo que o SisUAB aceite de primeira, para não perder dias com retrabalho."

**Persona secundária: Rafael (fictício)**, técnico de TI ou professor-desenvolvedor que instala e mantém a ferramenta.
- Contexto: instala via Docker ou script; edita `config/polos.txt` quando os polos mudam.
- Dores: pedidos de suporte recorrentes; medo de vazamento de dados de alunos.
- Job-to-be-done: "Quero instalar uma vez, com um comando, e não precisar intervir a cada importação."

### 2.5 Oportunidade de posicionamento

Nenhuma ferramenta reúne ao mesmo tempo as regras específicas do SisUAB, a leitura de entradas heterogêneas e a privacidade local. O posicionamento é: **"a IA ajuda a ler, o código garante o CSV"**.

---

## 3. Stack Tecnológica Recomendada

As versões fixas de cada biblioteca serão definidas na SPEC, após verificar as versões estáveis atuais.

| Camada | Escolha | Alternativa | Trade-off e justificativa |
|--------|---------|-------------|---------------------------|
| Frontend/UI | Streamlit | NiceGUI ou Gradio | O Streamlit já traz `st.data_editor`, chat e botão de download prontos. Em troca, ele reexecuta o script inteiro a cada interação, o que exige cuidado com o estado |
| Backend | Pacote Python puro (`core/`), chamado pela UI no mesmo processo | API FastAPI separada + frontend próprio | Um único processo simplifica a instalação. Uma API só faria sentido com outro cliente, o que está fora do escopo |
| Banco de dados | Nenhum: estado em memória (`st.session_state`) | SQLite local | Sem persistência, não há o que vazar nem apagar. Fechar a aba descarta o trabalho, o que é aceitável para uma sessão curta |
| Auth | Nenhuma; a app escuta só em `127.0.0.1` | Senha simples | A segurança vem do isolamento de rede, sem gestão de usuários |
| Infra/Deploy | Docker Compose + `run.sh`/`run.bat` com venv | Instalador PyInstaller | O Docker padroniza o ambiente e o script cobre máquinas sem Docker. O instalador fica para depois do MVP |
| IA/LLM | Ollama local, modelo instruct de 7 a 8B com saída em JSON Schema (**Premissa**: `qwen3:8b` ou equivalente, escolhido por benchmark com dados fictícios na SPEC) | llama.cpp server ou LM Studio | O Ollama oferece `/api/tags` e `format` com schema. Um modelo de 7 a 8B exige cerca de 8 GB de RAM livre (**estimativa**) |
| Extração | pdfplumber, python-docx, openpyxl, xlrd, pandas, charset-normalizer e o módulo `csv` da stdlib | PyMuPDF ou docling | Bibliotecas maduras, em Python puro. O `xlrd` é necessário porque o openpyxl só lê `.xlsx`. Não há OCR, então o PDF precisa ter texto |
| Validação | Pydantic v2 + email-validator com `check_deliverability=False` + funções puras | Validação manual | Tipagem e mensagens estruturadas. Com a verificação de entregabilidade desligada, nenhuma consulta DNS é feita |
| Correspondência de polo | `difflib` + `unicodedata` (stdlib) | rapidfuzz | Para 23 polos, a stdlib basta, sem dependência extra |
| Configuração | pydantic-settings lendo o `.env` | python-dotenv | Valida os tipos, por exemplo `LINE_ENDING` só aceita LF ou CRLF |
| Cliente Ollama | `requests`, que já vem com o Streamlit | SDK `ollama` | Nenhuma dependência nova e controle explícito de timeout |
| Testes | pytest | — | Exigido no prompt |

---

## 4. APIs e Integrações Externas

| Serviço | Finalidade | Justificativa |
|---------|------------|---------------|
| Ollama local (`OLLAMA_BASE_URL`) | `/api/tags` para listar modelos e `/api/chat` para extração e chat, com `format` em JSON Schema e `temperature=0` | É a única IA permitida |
| Pagamentos, e-mail, storage, analytics | **Nenhum** | Regra 1: nenhum dado sai da máquina |
| Observabilidade | Log local em arquivo, com CPF, e-mail e telefone mascarados (ex.: `*********01`), sem envio externo | Permite diagnóstico sem expor dados |

**Proteções de rede** (consequências diretas da regra 1):
- `.streamlit/config.toml` com `browser.gatherUsageStats = false` e `server.address = "127.0.0.1"`. O padrão do Streamlit expõe a app a toda a rede local.
- O seletor de modelos oculta os modelos cloud do Ollama (sufixo `-cloud` e/ou indicação de host remoto no `/api/tags`, a confirmar na SPEC), porque eles rodam em servidor externo.
- `OLLAMA_BASE_URL` só aceita loopback, `host.docker.internal` ou o serviço do compose (**Premissa**). Isso impede apontar para um servidor remoto por engano.
- No Docker, a porta é publicada como `127.0.0.1:8501:8501`.

> 💡 **Sugestão:** no profile em que o Ollama roda dentro do compose, colocar a app numa rede Docker `internal: true`, sem rota para a internet. O `ollama pull` é feito à parte, antes do uso.

---

## 5. Arquitetura do Sistema

```
┌────────────────────── Máquina da secretária (127.0.0.1) ──────────────────────┐
│                                                                               │
│  Navegador ──HTTP localhost:8501──► Streamlit (app/)                          │
│                                        │  estado: st.session_state (memória)  │
│                                        ▼                                      │
│               ┌──────────── core/ (Python puro, testável) ─────────────┐      │
│  uploads ───► │ 1 ingest     formato, codificação, separador, cabeçalho│      │
│  (BytesIO)    │ 2 extract    ├─ tabular: CSV, XLSX, XLS, JSON          │      │
│               │              ├─ tabelas de PDF/DOCX, TXT delimitado    │      │
│               │              └─ texto livre ──────► llm ───┐           │      │
│               │ 3 mapping    colunas → 7 campos            │ IA só     │      │
│               │ 4 normalize  trim, NFC, dígitos, caixa     │ sugere    │      │
│               │ 5 validate   regras → lista de problemas   │           │      │
│               │ 6 patches    editor/chat → confirmação ◄───┘           │      │
│               │ 7 export     bytes do CSV (QUOTE_NONE)                 │      │
│               │ 8 verify     relê os bytes → libera o download         │      │
│               └────────────────────────────────────────────────────────┘      │
│                                        │ HTTP localhost:11434                 │
│                                        ▼                                      │
│                    Ollama (no host ou no compose, profile "ollama")           │
│                                                                               │
│  config/polos.txt · config/ddds.txt · .env · logs/ (mascarados)               │
└───────────────────────────────────────────────────────────────────────────────┘
            ✕ sem saída para a internet: nenhuma API, CDN ou telemetria
```

### Padrões adotados

- **Pipeline de funções puras:** cada etapa, de `ingest` a `verify`, recebe e devolve dados. Tudo é testável sem Streamlit.
- **"A IA propõe, o código dispõe":** toda saída do LLM passa por schema Pydantic, normalização e validação completa. Ela nunca escreve direto no CSV.
- **Correção confirmada:** cada alteração é um patch `(linha, campo, valor_novo)`. Aplicar um patch dispara a revalidação de todos os registros, o que é barato no volume esperado.
- **Registro rastreável:** cada registro guarda o arquivo e a posição de origem (linha, página, tabela), usados nas mensagens de erro.
- **Processamento em memória:** os uploads chegam como `BytesIO` e o CSV é gerado em bytes para o `st.download_button`. Na maioria dos casos, nenhum arquivo temporário é criado. Quando for inevitável, usa-se `TemporaryDirectory`, descartado ao fim da etapa, com limpeza extra na inicialização.
- **Degradação graciosa:** com o Ollama offline, só a extração de texto livre, a sugestão de mapeamento e o chat ficam indisponíveis, com aviso na tela.

### Extração híbrida (decisão aprovada)

| Entrada | Caminho |
|---------|---------|
| CSV | charset-normalizer (UTF-8, cp1252, latin-1) + `csv.Sniffer` para o separador + heurística de cabeçalho |
| XLSX / XLS | pandas com openpyxl ou xlrd, todas as colunas como texto (`dtype=str`) |
| JSON | Lista de objetos, ou objeto que contém uma lista (**Premissa**) |
| PDF | pdfplumber: tabelas extraídas por código; páginas sem tabela vão como texto para a IA |
| DOCX | python-docx: tabelas extraídas por código; parágrafos vão para a IA |
| TXT | Se o `csv.Sniffer` detectar um delimitador consistente, é tratado como CSV; senão, vai para a IA |

O mapeamento de colunas é feito por sinônimos de cabeçalho, em código. Quando é ambíguo ou não há cabeçalho, a IA sugere e a usuária confirma.

### Gargalos e riscos técnicos do MVP

- LLM em CPU é lento em PDFs longos (**estimativa**: dezenas de segundos por página com 7 a 8B). Mitigação: processar por página, com barra de progresso.
- A IA pode omitir ou inventar registros ao ler texto livre. Ver R1 na seção 12.
- Um registro pode ficar dividido entre duas páginas do PDF.
- O Streamlit reexecuta o script a cada clique. Resultados caros, como a extração por IA, ficam guardados em `session_state` pelo hash do arquivo.
- No Linux, `host.docker.internal` exige `extra_hosts: ["host.docker.internal:host-gateway"]`.

---

## 6. Modelagem de Dados (Prévia)

Não há banco de dados. As entidades vivem em memória durante a sessão.

**ArquivoEntrada**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | str | Hash SHA-256 do conteúdo; evita reprocessar o mesmo arquivo |
| nome | str | Nome original |
| formato | enum | PDF, CSV, XLSX, XLS, DOCX, JSON ou TXT |
| codificacao | str ou None | Detectada, só para CSV e TXT |
| separador | str ou None | Detectado |
| tem_cabecalho | bool ou None | Detectado; a usuária pode corrigir |
| polo_padrao | str ou None | Polo aplicado a todas as linhas do arquivo, se a usuária informar |

**Registro**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | int | Sequencial global; é a linha no CSV de saída (**Premissa**: ordem de carregamento dos arquivos) |
| origem_arquivo | str | Nome do arquivo de origem |
| origem_local | str | Ex.: "linha 12" ou "página 3, tabela 1, linha 4" |
| metodo | enum | TABULAR, TABELA_DOC ou IA |
| bruto | dict[str, str] | Valores originais, exibidos para conferência |
| polo, cpf, situacao, email, ddd, telefone, publico_alvo | str | Os 7 campos normalizados |

**Problema**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| registro_id | int | Registro afetado |
| campo | enum | Um dos 7 campos, ou LINHA |
| severidade | enum | ERRO (bloqueia) ou AVISO (não bloqueia) |
| codigo | str | Ex.: `CPF_DV_INVALIDO`, `CPF_DUPLICADO`, `POLO_NAO_ENCONTRADO` |
| mensagem | str | Texto em português para a usuária |
| sugestao | str ou None | Valor proposto, aplicado só com confirmação |

**Correcao (patch)**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| registro_id | int | Registro alterado |
| campo | enum | Campo alterado |
| valor_anterior / valor_novo | str | Antes e depois |
| origem | enum | EDITOR, CHAT_IA, SUGESTAO ou LOTE (ex.: polo para o arquivo inteiro) |
| status | enum | PROPOSTA, APLICADA ou REJEITADA |

**ConfigSessao**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| modelo_ollama | str | Modelo selecionado |
| periodo_atual | int ou None | Ativa a validação contextual parcial |
| quebra_linha | enum | LF ou CRLF, vindo do `.env` |

**Listas de referência (arquivos editáveis, nunca fixas no código):**
- `config/polos.txt`: um polo por linha, UTF-8, normalizado em NFC.
- `config/ddds.txt`: os 67 DDDs brasileiros (fonte: Anatel).

**Segurança:** nada é persistido; o `session_state` é isolado por aba; os logs são mascarados. RLS não se aplica.

> 💡 **Sugestão:** botão "Limpar tudo" que zera a sessão, e aviso na tela de que fechar a aba descarta o trabalho.

---

## 7. Regras de Negócio Centrais

Resumo das regras. O detalhamento tipado (Validação, Invariante, Transição, Autorização) virá no PRD.

### 7.1 Formato do CSV (Invariante)

- RN-01: UTF-8 sem BOM, preservando acentos e Ç.
- RN-02: separador `;` e exatamente 7 campos por linha.
- RN-03: sem linha de cabeçalho.
- RN-04: sem aspas e sem apóstrofos (`csv.QUOTE_NONE`). Um campo que contenha `;`, `"`, `'` ou quebra de linha é ERRO, porque o gerador nunca escapa caracteres.
- RN-05: quebra de linha LF por padrão, CRLF configurável no `.env`.
- RN-06: nenhuma linha começa com `#` ou `;`. Isso já é garantido porque o campo 1 é sempre um polo da lista.
- RN-07: extensão `.csv`, uma linha por aluno, todos os arquivos consolidados num só CSV.

### 7.2 Campos (Validação)

| # | Campo | Normalização | ERRO | AVISO |
|---|-------|--------------|------|-------|
| 1 | Polo | Trim e NFC; espaços internos mantidos | Não idêntico a um item da lista (o valor aproximado vira sugestão); ausente leva a pedir o polo, com opção de aplicar ao arquivo inteiro; mais de 80 caracteres | — |
| 2 | CPF | Lido como texto; remove `.`, `-` e espaços; completa com zeros à esquerda até 11 dígitos | Dígito verificador inválido; sequência repetida; notação científica; caractere não numérico ou mais de 11 dígitos; duplicado (sempre, mesmo com dados idênticos, corrigido manualmente) | — |
| 3 | Situação | Trim e maiúsculas | Fora de CUR, CAN, TRC, DES, FDO, FAL, TRA, DTT, TCC | Ausente: preenche CUR |
| 4 | E-mail | Trim e remoção de espaços internos | Ausente; formato inválido; mais de 60 caracteres; contém `'`, `"` ou `;` | — |
| 5 | DDD | Só dígitos; remove o zero à esquerda (061 → 61) | Ausente; diferente de 2 dígitos; fora de `ddds.txt` | — |
| 6 | Telefone | Só dígitos; com 11 dígitos, separa DDD e telefone | Ausente; 8 dígitos; qualquer tamanho diferente de 9 | — |
| 7 | Público-alvo | Trim e maiúsculas (**Premissa**, ver pendência 1) | Fora de DS e PR | Ausente: preenche DS |

**Telefone com 8 dígitos (premissa aprovada):** continua sendo ERRO. Se começar com 6 a 9, a sugestão é acrescentar o 9. Se começar com 2 a 5, é fixo, e a sugestão é pedir um celular.

### 7.3 Validação contextual parcial (AVISO, decisão aprovada)

Só é aplicada se a usuária informar o período atual (P):
- CAN com P maior que 2 gera AVISO (**Premissa**: o "1º ano" corresponde aos períodos 1 e 2, já que o manual permite CAN "durante o 1º período quanto durante o 2º período").
- DES, TRC e TRA com P menor que 3 geram AVISO.
- TCC e FDO não são validados no MVP, porque exigem o total de períodos.
- FAL, CUR e DTT não têm regra contextual.

### 7.4 Download (Autorização)

- O download só é liberado com zero ERROS **e** com a verificação final de bytes aprovada.
- Qualquer edição invalida a verificação anterior e dispara a revalidação.

### 7.5 Uso da IA (Invariante)

- O LLM só: extrai texto livre para um JSON com schema fixo (temperatura 0); sugere o mapeamento de colunas; propõe patches no chat.
- Nenhuma saída do LLM chega ao CSV sem confirmação da usuária e sem passar pela validação completa.

### Fluxo de onboarding (instalação)

1. O TI roda `docker compose up -d` ou `run.bat`/`run.sh`.
2. O TI baixa o modelo com `ollama pull <modelo>`, conforme o README.
3. A secretária abre `http://localhost:8501`. A barra lateral mostra se o Ollama está online e quais modelos há.

### Fluxo principal de uso (fluxo de telas)

Página única em 4 etapas, com barra lateral fixa:

```
Barra lateral: Ollama ● online · URL · Modelo [▼] · Período atual (opcional) · [Limpar tudo]

 1 CARREGAR ──────► 2 CONFERIR LEITURA ──────► 3 CORRIGIR ─────────► 4 BAIXAR
 upload de um ou    por arquivo: formato,       tabela editável        preview em texto bruto
 vários arquivos    codificação, cabeçalho,     contadores ERRO/AVISO  verificação de bytes
                    mapeamento de colunas,      filtro "só com erro"   [Baixar CSV] só com
                    polo padrão se ausente,     sugestões [Aceitar]    zero erros
                    progresso da extração IA,   chat IA → patches
                    linhas descartadas          [Aplicar] → revalida
```

### Fluxo de cancelamento

Não se aplica, por ser uma ferramenta interna. O equivalente é "Limpar tudo" ou fechar a aba, o que descarta a sessão.

### Edge cases que o MVP já trata

- CPF em notação científica vindo como texto (ex.: `3,42E+10` num CSV salvo pelo Excel) é ERRO. Num XLSX, o valor numérico costuma estar íntegro e só perde os zeros à esquerda, que são recompletados.
- Mesmo aluno em dois arquivos (planilha geral + planilha do polo) gera ERRO de duplicidade, apontando as duas origens.
- Polo com acento decomposto (NFD) é normalizado para NFC antes da comparação.
- CSV já no formato SisUAB (sem cabeçalho, com `;`) é reconhecido pelo mapeamento posicional.
- PDF escaneado, sem texto, gera a mensagem "PDF sem texto; leitura de imagem não é suportada".
- E-mail com apóstrofo (válido por RFC) é ERRO, porque o CSV não admite apóstrofos.
- Ollama offline: os fluxos tabulares continuam funcionando, com aviso.

---

## 8. Monetização e Modelo de Negócio

Não se aplica: é uma ferramenta interna, sem custo de licença ou de infraestrutura, porque roda no hardware existente.
- **Modelo:** código aberto no GitHub, sem nenhum dado real no repositório.
- **Custo operacional (estimativa):** zero além do hardware; a máquina precisa de 8 a 16 GB de RAM para o modelo local.
- **Adoção por outras IES:** basta editar `config/polos.txt`.

> 💡 **Sugestão:** definir a licença. MIT favorece o reuso amplo por outras IES; AGPL-3.0 obriga quem modificar a publicar as melhorias.

---

## 9. Roadmap de Features

| ID | Feature | Prioridade | Complexidade | Dependências |
|----|---------|------------|--------------|--------------|
| F01 | Configuração: `.env`, `polos.txt`, `ddds.txt`, `config.toml` de privacidade | Essencial MVP | Baixa | — |
| F02 | Normalização e validação dos 7 campos, com testes | Essencial MVP | Média | F01 |
| F03 | Gerador do CSV + verificação de bytes | Essencial MVP | Baixa | F02 |
| F04 | Ingestão tabular (CSV com detecção, XLSX, XLS, JSON) + mapeamento por sinônimos | Essencial MVP | Média | F02 |
| F05 | UI: upload, relatório, `data_editor`, filtros, preview, download bloqueado | Essencial MVP | Média | F03, F04 |
| F06 | Cliente Ollama: status, `/api/tags` sem modelos cloud, chat com schema | Essencial MVP | Baixa | F01 |
| F07 | Extração híbrida de PDF/DOCX/TXT + conferência de contagem | Essencial MVP | Alta | F04, F06 |
| F08 | Sugestão de mapeamento ambíguo pela IA | Essencial MVP | Média | F04, F06 |
| F09 | Chat de correções → patches confirmáveis → revalidação | Essencial MVP | Média | F05, F06 |
| F10 | Validação contextual parcial (período atual) | Essencial MVP | Baixa | F02 |
| F11 | Empacotamento: Dockerfile, compose com profile `ollama`, `run.sh`/`run.bat`, README | Essencial MVP | Baixa | F05 |
| F12 | Validação contextual completa (total de períodos, TCC/FDO) | Pós-MVP v1 | Baixa | F10 |
| F13 | Instalador Windows com atalho | Pós-MVP v1 | Média | F11 |
| F14 | OCR local para PDF escaneado | Futuro | Alta | F07 |
| F15 | Perfis por IES, com várias listas de polos | Futuro | Baixa | F01 |

---

## 10. Fora do Escopo do MVP

| Item | Motivo da exclusão |
|------|--------------------|
| Consultar o SisUAB para checar duplicidade | Não há integração; decisão do prompt |
| Autenticação e multiusuário | Uso local, por uma usuária |
| Histórico de importações | Privacidade: não guardar nada elimina o risco |
| OCR de PDF escaneado | Complexidade; o PDF precisa ter texto |
| Validação de TCC/FDO por período | Exige o total de períodos (decisão aprovada) |
| Remoção automática de duplicatas | Decisão aprovada: correção manual |
| IA em nuvem ou qualquer API externa | Regra 1 |
| Envio do CSV ao SisUAB | O upload continua manual, no próprio SisUAB |
| Acesso pela rede (servidor compartilhado) | Faria os dados saírem da máquina da usuária |

---

## 11. Evolução da Arquitetura

Os cenários de 10 mil usuários, 1 milhão e multi-região não se aplicam: a arquitetura é local e de uma usuária por desenho. Os cenários realistas são:

| Cenário | O que muda |
|---------|-----------|
| Várias secretárias da mesma IES, em PCs diferentes | Cada PC roda sua instância; `polos.txt` é distribuído por Git ou pasta compartilhada |
| Adoção por outras IES | Perfis por IES (F15) e um guia de adoção no README |
| Volume alto (milhares de linhas por carga) | pandas já comporta; o gargalo seria só a IA, então a extração tabular é priorizada |
| Servidor institucional na rede | Exigiria revisar a regra 1, porque os dados trafegariam na rede, além de TLS, autenticação (LDAP) e relatório de impacto (LGPD). Seria um novo projeto, não uma evolução |

---

## 12. Riscos e Pontos de Atenção

| ID | Risco | Categoria | Impacto | Mitigação |
|----|-------|-----------|---------|-----------|
| R1 | A IA omite ou inventa registros ao ler texto livre | Técnico | Alto | Contar CPFs por regex no texto de origem e comparar com os registros extraídos; exigir que cada CPF extraído exista no texto de origem; revisão na tabela antes do download |
| R2 | Máquina sem RAM suficiente para o modelo | Técnico | Médio | Modelo menor configurável; fluxos tabulares funcionam sem IA |
| R3 | O SisUAB muda o leiaute ou a lista de polos | Dependência | Médio | Regras centralizadas em `core/`; polos em arquivo editável |
| R4 | Manual contraditório: o §3 diz que CPF já existente na oferta é ALTERADO, e a regra 9 do §4 diz que é IGNORADO | Dependência | Médio | Fora do alcance da app, que não consulta o SisUAB. Registrar no README e confirmar com o uso real ou com a CAPES |
| R5 | O manual informa que, na inclusão, o sistema grava o aluno como CURSANDO, então outra situação num aluno novo pode ser sobrescrita | Dependência | Baixo | Explicar no README e em dica na tela; não bloquear |
| R6 | Vazamento acidental: app exposta na rede, modelo cloud, URL remota ou log sem máscara | Regulatório (LGPD) | Alto | Proteções da seção 4 + testes que verificam a configuração e o mascaramento |
| R7 | Docker Desktop pesado ou difícil no PC da secretária | Técnico | Médio | `run.bat` como caminho alternativo |
| R8 | Reexecução do Streamlit perde ou duplica estado | Técnico | Médio | Estado centralizado em `session_state` e cache por hash |
| R9 | Dados reais em testes ou issues do GitHub | Regulatório | Médio | Só dados fictícios (CPFs gerados com dígito verificador válido); `.gitignore` cobre uploads e saídas |

> 💡 **Sugestões proativas:**
> - **LGPD:** documentar no README a finalidade do tratamento e a minimização (nada é persistido).
> - **Observabilidade:** log local mascarado, com rotação por tamanho.
> - **Acessibilidade:** ERRO e AVISO indicados por ícone e texto, nunca só por cor; mensagens em linguagem simples.
> - **Testes:** além dos exigidos, testes de privacidade (config do Streamlit, filtro de modelos cloud, mascaramento de logs).

---

## Pendências para o PRD

Premissas adotadas para seguir, a confirmar no PRD:

1. Converter o público-alvo para maiúsculas (`ds` → `DS`)? **Premissa:** sim.
2. Telefone com prefixo `55` ou `0` (12 ou 13 dígitos): **Premissa:** ERRO, sem tratamento automático.
3. DDD em coluna própria diferente do DDD embutido num telefone de 11 dígitos: **Premissa:** ERRO de conflito.
4. E-mail com caracteres não ASCII (ex.: acento): aceitar ou tratar como ERRO? **Sem premissa, decidir.**
5. Linhas sem nenhum dado reconhecível (títulos, totais): **Premissa:** listadas como "descartadas" para revisão, nunca somem em silêncio.
6. XLSX com várias abas: **Premissa:** ler todas as abas não vazias, com opção de desmarcar.

A árvore de pastas e as versões fixas das bibliotecas serão definidas na SPEC, antes de qualquer código.

---

## Resumo Executivo

O Importador SisUAB transforma listas de alunos em formatos variados num único CSV aceito pelo SisUAB2, seguindo o manual CAPES e as correções definidas. O foco é a secretária da UAB, que hoje monta o arquivo à mão e só descobre os erros depois da importação.

A oportunidade é reunir o que nenhuma alternativa entrega junto: as regras específicas do SisUAB, a leitura de PDF, planilhas e documentos, e privacidade total. O processo manual é frágil, e a IA em nuvem é inaceitável para CPF, e-mail e telefone.

A stack é Python com Streamlit no mesmo processo, sem banco e sem autenticação, com a app acessível apenas em `127.0.0.1`. O Ollama local é a única IA, usada só para ler texto livre, sugerir mapeamentos e propor correções. Toda validação e toda geração do CSV são feitas por código determinístico e testado.

A arquitetura é um pipeline de funções puras (ingestão, extração híbrida, mapeamento, normalização, validação, patches, exportação e verificação de bytes) independente da interface. O download só é liberado com zero erros e com o arquivo relido e aprovado byte a byte.

Próximo passo: aprovar este MVP Scope, confirmar as pendências e seguir para o PRD, com as regras tipadas e os critérios de aceite por feature.

---

## Checklist de qualidade

- [x] Premissas marcadas explicitamente
- [x] Dados com fonte ou marcados como estimativa
- [x] Cada decisão tecnológica com justificativa e alternativa
- [x] Roadmap sequenciado com dependências
- [x] Fora do escopo explícito, com motivo
- [x] Resumo executivo coeso
- [x] Sugestões proativas sinalizadas
