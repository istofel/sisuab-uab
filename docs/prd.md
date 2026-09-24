# PRD — Importador SisUAB

**Versão:** 1.0 · **Data:** 23/09/2026 · **Status:** aguardando aprovação
**Base:** `mvp-scope.md` v1.0 (aprovado). Fonte de verdade das regras: manual CAPES "Novo Modelo de Arquivo" + "Correções ao manual" do prompt original, que prevalecem sobre o manual.
**Escopo deste documento:** o quê e por quê. Decisões de como construir (tecnologias, estrutura de código, versões) ficam na SPEC.

---

## 1. Visão Geral do Produto

**O que é:** aplicação local que recebe listas de matrícula de alunos UAB em PDF, CSV, planilha, documento Word, JSON ou texto, e gera um único arquivo CSV pronto para importar no SisUAB2. Toda validação é feita por regras fixas e testadas; uma IA que roda na própria máquina ajuda só a ler texto livre e a sugerir correções.

**Para quem:** secretária da coordenação UAB (usuária diária, não técnica) e o técnico que instala e mantém a ferramenta.

**Problema:** os polos enviam dados em formatos diferentes, e o SisUAB descarta as linhas incorretas. A montagem manual do CSV é lenta, sujeita a erros invisíveis (acentos, zeros à esquerda, separador, codificação) e, se feita com IA em nuvem, expõe dados pessoais.

**Proposta de valor:** um CSV aceito na primeira importação, com cada problema apontado por arquivo, linha e campo, em português simples, sem que nenhum dado saia do computador.

### Princípios de design (critérios de desempate)

1. **Privacidade acima de conveniência.** Nenhum dado de aluno sai da máquina, mesmo que isso custe uma funcionalidade.
2. **O código decide, a IA sugere.** Nada produzido pela IA vai para o arquivo sem confirmação da usuária e sem passar pela validação completa.
3. **Nada acontece em silêncio.** Todo preenchimento por padrão gera AVISO; toda linha descartada aparece numa lista; toda correção fica registrada.
4. **Na dúvida, perguntar.** Ambiguidade vira pergunta à usuária, nunca decisão automática.
5. **Linguagem da secretária.** Mensagens sem jargão, sempre dizendo onde está o problema e como resolver.

---

## 2. Objetivos e Métricas de Sucesso

### Objetivos do MVP

| ID | Objetivo | Descrição |
|----|----------|-----------|
| O1 | Arquivo aceito | O CSV gerado não tem linhas rejeitadas pelo SisUAB por formato ou dado inválido |
| O2 | Menos tempo | Preparar uma carga completa leva muito menos tempo que o processo manual |
| O3 | Zero exposição | Nenhum dado de aluno trafega para fora da máquina |
| O4 | Autonomia | A secretária usa a ferramenta sem ajuda do TI na rotina |

### Métricas de sucesso

| Métrica | Alvo MVP | Como medir |
|---------|----------|------------|
| Linhas rejeitadas pelo SisUAB, por arquivo gerado | 0 | Relatório de importação do SisUAB, anotado pela usuária no piloto |
| Tempo para preparar uma carga dos 23 polos | ≤ 30 min (**estimativa**; linha de base a medir no processo manual antes do piloto) | Cronometragem no piloto |
| Conexões de rede para fora da máquina durante o uso | 0 | Teste automatizado + inspeção de rede no piloto |
| Casos de teste obrigatórios passando | 100% | Suíte de testes |
| Registros de texto livre extraídos corretamente | ≥ 98% (**estimativa**) | Documentos fictícios de referência com gabarito |
| Chamados ao TI por mês, fora da instalação | 0 (**estimativa**) | Registro do TI |

---

## 3. Personas e Casos de Uso

### Persona primária — Márcia (fictícia)

**Perfil:** 47 anos, secretária da coordenação UAB do IFTO. Usa um computador com Windows 10 ou 11 e 8 a 16 GB de RAM (**Premissa**). Domina planilhas e navegador; não usa terminal. Recebe as listas dos polos no início de cada oferta e em cada atualização de situação.

**Casos de uso:** UC-01 a UC-13.

### Persona secundária — Rafael (fictício)

**Perfil:** 35 anos, técnico de TI ou professor-desenvolvedor. Usa Windows ou Linux. Instala a ferramenta, mantém a lista de polos e resolve problemas de ambiente.

**Casos de uso:** UC-14 a UC-17.

### Mapa de Casos de Uso

| ID | Caso de Uso | Persona | Feature (RF) | Prioridade |
|----|-------------|---------|--------------|------------|
| UC-01 | Carregar um ou vários arquivos de matrícula | Márcia | RF-02 | Essencial |
| UC-02 | Conferir como cada arquivo foi lido (cabeçalho, abas, colunas) | Márcia | RF-03, RF-04 | Essencial |
| UC-03 | Confirmar o mapeamento de colunas | Márcia | RF-05 | Essencial |
| UC-04 | Informar o polo de um arquivo que não tem polo | Márcia | RF-05, RF-10 | Essencial |
| UC-05 | Ver erros e avisos por linha e campo; filtrar só as linhas com erro | Márcia | RF-10 | Essencial |
| UC-06 | Corrigir um valor diretamente na tabela | Márcia | RF-10 | Essencial |
| UC-07 | Excluir uma linha (ex.: aluno repetido) | Márcia | RF-10 | Essencial |
| UC-08 | Aceitar ou recusar uma sugestão (polo aproximado, telefone) | Márcia | RF-10 | Essencial |
| UC-09 | Pedir correções em linguagem natural no chat | Márcia | RF-11 | Essencial |
| UC-10 | Revisar as linhas descartadas na leitura | Márcia | RF-03, RF-04 | Essencial |
| UC-11 | Informar o período atual da oferta | Márcia | RF-09 | Essencial |
| UC-12 | Conferir a prévia e baixar o CSV | Márcia | RF-12, RF-13 | Essencial |
| UC-13 | Limpar a sessão e começar de novo | Márcia | RF-15 | Essencial |
| UC-14 | Instalar e iniciar com um único comando | Rafael | RF-16 | Essencial |
| UC-15 | Editar a lista de polos válidos | Rafael | RF-01 | Essencial |
| UC-16 | Verificar a IA local e escolher o modelo | Rafael, Márcia | RF-14 | Essencial |
| UC-17 | Rodar os testes automatizados | Rafael | RF-16 | Essencial |

---

## 4. Requisitos Funcionais

### RF-01: Configuração e listas de referência

**Descrição:** o sistema lê as listas de referência e as preferências de um local editável, sem nenhuma regra fixa no código.

**Critérios de aceite:**
- A lista de polos válidos vem de um arquivo de texto editável, um polo por linha.
- A lista de DDDs válidos vem de um arquivo editável, com os 67 DDDs brasileiros (fonte: Anatel).
- A quebra de linha do CSV (padrão Linux ou Windows), o endereço da IA local, o modelo padrão e a porta vêm do arquivo de configuração.
- Alterar a lista de polos e reiniciar a aplicação muda o resultado da validação, sem alterar código.

**Regras:**
- Linhas em branco da lista de polos são ignoradas; espaços no início e no fim de cada polo são removidos | Tipo: Validação
- Polos da lista são comparados sempre na forma de acentuação composta (Á como um caractere só) | Tipo: Invariante
- Polo repetido na lista, ou polo com mais de 80 caracteres, impede a inicialização com mensagem clara | Tipo: Validação

**Tratamento de erros:**
- Lista de polos ausente ou vazia → aplicação exibe tela de orientação para o TI e não permite gerar CSV.
- Configuração com valor inválido (ex.: quebra de linha diferente de LF ou CRLF) → aplicação não inicia e informa qual chave está errada.

---

### RF-02: Recebimento de arquivos

**Descrição:** a usuária envia um ou vários arquivos de uma vez, de qualquer formato aceito, com todos os polos juntos ou um arquivo por polo.

**Critérios de aceite:**
- Aceita PDF (com texto), CSV, XLSX, XLS, DOCX, JSON e TXT.
- Aceita vários arquivos na mesma carga e permite adicionar mais arquivos depois.
- Cada arquivo aparece numa lista com nome, formato detectado e situação da leitura.
- Enviar de novo um arquivo idêntico não duplica os registros; o sistema avisa que ele já foi carregado.
- É possível remover um arquivo da carga, o que remove seus registros e revalida tudo.

**Regras:**
- Formato é identificado pelo conteúdo e pela extensão; divergência entre os dois gera AVISO | Tipo: Validação
- Arquivo acima do tamanho máximo (**Premissa**: 50 MB) é recusado | Tipo: Validação
- Todos os registros de todos os arquivos formam uma única carga, que gera um único CSV | Tipo: Invariante

**Tratamento de erros:**
- Formato não suportado → "O arquivo X não é de um tipo aceito. Envie PDF, CSV, XLSX, XLS, DOCX, JSON ou TXT."
- Arquivo corrompido ou protegido por senha → "Não foi possível abrir X. Verifique se o arquivo abre no seu computador e se não tem senha."
- Arquivo sem nenhum registro → AVISO no arquivo: "Nenhum aluno encontrado em X."

---

### RF-03: Leitura de arquivos estruturados (CSV, XLSX, XLS, JSON)

**Descrição:** o sistema lê arquivos tabulares por regras fixas, sem IA, preservando todos os valores como texto.

**Critérios de aceite:**
- Todos os valores são lidos como texto: um CPF que começa com zero não perde o zero na leitura.
- Em CSV e TXT delimitado, detecta a codificação (UTF-8, Windows-1252 ou Latin-1), o separador e a presença de cabeçalho.
- Em planilhas, lê todas as abas que têm dados; a usuária pode desmarcar abas.
- Em JSON, aceita uma lista de objetos ou um objeto que contenha uma lista de objetos (**Premissa**).
- A usuária vê, para cada arquivo, o que foi detectado e pode corrigir (ex.: "a primeira linha é cabeçalho: sim/não").
- Nomes acentuados (ARAGUAÍNA, XAMBIOÁ) aparecem corretos na tela independentemente da codificação de origem.

**Regras:**
- Linha totalmente vazia é ignorada e contada no resumo do arquivo | Tipo: Validação
- Linha com conteúdo, mas sem nada que se pareça com CPF, e-mail ou telefone (ex.: título, "Total: 35") vai para a lista de linhas descartadas, nunca some em silêncio | Tipo: Invariante
- A usuária pode trazer uma linha descartada de volta como registro; ela passa pela validação normalmente | Tipo: Transição de Estado
- Cada registro guarda sua origem: arquivo, aba (se houver) e número da linha | Tipo: Invariante

**Tratamento de erros:**
- Codificação não identificada com segurança → pergunta à usuária qual prévia está correta, mostrando as opções com acentos.
- Separador ambíguo → pergunta à usuária, com prévia das primeiras linhas.
- JSON fora das estruturas aceitas → "O JSON de X não está em um formato reconhecido (esperado: lista de alunos)."

---

### RF-04: Leitura de documentos (PDF, DOCX, TXT)

**Descrição:** leitura híbrida. Tabelas dos documentos são lidas por regras fixas; só o texto livre vai para a IA local, que devolve os registros num formato fixo.

**Critérios de aceite:**
- Tabelas de PDF e DOCX são lidas sem IA, com as mesmas regras do RF-03.
- TXT com delimitador consistente é tratado como CSV (RF-03).
- Texto livre (páginas sem tabela, parágrafos, TXT não delimitado) é enviado à IA local, em blocos, com barra de progresso.
- A IA devolve registros sempre na mesma estrutura: os 7 campos, o nome do aluno se houver e o local de origem (página ou parágrafo).
- Registros lidos pela IA ficam marcados como "lido pela IA" na tabela.
- Ao fim, o sistema compara quantos CPFs aparecem no texto original com quantos registros a IA devolveu.

**Regras:**
- A IA é configurada para respostas determinísticas e só recebe o texto do bloco, sem instruções vindas do documento com poder de mudar seu comportamento | Tipo: Validação
- Todo CPF de registro lido pela IA precisa existir no texto original (comparando só os dígitos); se não existir, é ERRO `CPF_NAO_ENCONTRADO_ORIGEM` (**Premissa**) | Tipo: Validação
- Diferença entre a quantidade de CPFs no texto e de registros extraídos gera AVISO no arquivo, listando os CPFs do texto que não viraram registro | Tipo: Validação
- Toda saída da IA passa por normalização e validação completas (RF-06 a RF-09) | Tipo: Invariante

**Tratamento de erros:**
- PDF sem texto (escaneado) → "O PDF X parece ser uma imagem escaneada. Esta versão não lê imagens; peça o arquivo original ao polo."
- IA indisponível → tabelas continuam sendo lidas; blocos de texto livre ficam como "não lidos", com a mensagem "A IA local está desligada; estes trechos não foram lidos." e botão para tentar de novo.
- Resposta da IA fora da estrutura esperada → o bloco é reenviado uma vez; se falhar de novo, fica como "não lido", com o trecho visível para a usuária.

---

### RF-05: Mapeamento de colunas

**Descrição:** o sistema associa as colunas de cada arquivo aos 7 campos do SisUAB e permite que a usuária confirme ou corrija.

**Critérios de aceite:**
- Colunas são associadas automaticamente por nomes conhecidos (ex.: "CPF", "Nº do CPF"; "E-mail", "Email"; "Celular", "Telefone", "WhatsApp"; "Polo"; "Situação", "Status"; "Público", "Tipo de vaga").
- Arquivo sem cabeçalho e com exatamente 7 colunas é associado pela posição do leiaute SisUAB.
- Colunas que não correspondem a nenhum campo ficam como "ignorar".
- Quando há mais de uma candidata para o mesmo campo, ou nenhuma associação segura, a IA sugere (se estiver disponível) e a usuária confirma; sem IA, a usuária escolhe.
- A leitura só avança depois que a usuária confirma o mapeamento de cada arquivo que teve ambiguidade.

**Regras:**
- Cada campo recebe no máximo uma coluna por arquivo | Tipo: Validação
- Campo sem coluna associada é tratado como ausente em todas as linhas daquele arquivo | Tipo: Invariante
- Sugestão de mapeamento da IA nunca é aplicada sem confirmação | Tipo: Autorização
- Se o arquivo não tiver coluna de polo, a usuária pode escolher um polo da lista e aplicá-lo a todas as linhas do arquivo | Tipo: Transição de Estado

> 💡 **Sugestão:** se houver coluna de nome do aluno, exibi-la na tabela como referência para a usuária identificar cada linha. Ela nunca vai para o CSV.

**Tratamento de erros:**
- Nenhuma coluna reconhecida → "Não reconheci as colunas de X. Indique qual coluna é o CPF, o e-mail etc."

---

### RF-06: Normalização

**Descrição:** antes de validar, o sistema limpa cada valor de forma previsível e reversível na tela (o valor original continua visível).

**Critérios de aceite:**
- Remove espaços no início e no fim de todos os campos.
- Nos campos 2 a 7, remove também os espaços internos.
- No Nome do Polo, mantém os espaços internos.
- Converte todos os textos para a forma de acentuação composta.
- CPF: remove pontos, traço e espaços; completa com zeros à esquerda até 11 dígitos, se tiver menos.
- Situação e público-alvo: convertidos para maiúsculas.
- DDD: mantém só dígitos e remove o zero à esquerda (061 → 61).
- Telefone: mantém só dígitos; com 11 dígitos, separa os 2 primeiros como DDD e os 9 restantes como telefone.
- A usuária consegue ver o valor original de qualquer célula normalizada.

**Regras:**
- Normalização nunca inventa conteúdo: só remove caracteres, completa zeros no CPF ou reorganiza DDD e telefone | Tipo: Invariante
- Telefone de 11 dígitos com DDD também informado em coluna própria: se os DDDs forem iguais, segue; se forem diferentes, é ERRO `DDD_CONFLITO` | Tipo: Validação
- Telefone de 8 dígitos nunca recebe o 9 automaticamente | Tipo: Invariante

---

### RF-07: Validação dos campos

**Descrição:** cada registro é validado campo a campo por regras fixas, gerando problemas com severidade.

**Critérios de aceite:**
- Todo problema indica arquivo, linha de origem, número do registro, campo, severidade, mensagem e, quando houver, sugestão.
- ERRO bloqueia o download; AVISO não bloqueia, mas aparece destacado.
- A mesma entrada gera sempre os mesmos problemas.

**Regras por campo** (todas do tipo Validação, exceto onde indicado):

| # | Campo | É ERRO quando | É AVISO quando |
|---|-------|---------------|----------------|
| 1 | Nome do Polo | Ausente; não é idêntico a um item da lista; tem mais de 80 caracteres | — |
| 2 | CPF | Ausente; tem caractere não numérico; tem mais de 11 dígitos; está em notação científica (ex.: 3,42E+10); tem todos os dígitos iguais; dígitos verificadores inválidos; aparece em mais de um registro (RF-08) | — |
| 3 | Situação | Fora de CUR, CAN, TRC, DES, FDO, FAL, TRA, DTT, TCC | Ausente: preenchida com CUR |
| 4 | E-mail | Ausente; formato inválido; mais de 60 caracteres; contém `'`, `"` ou `;`; contém caractere não ASCII (**PENDENTE P-01**) | — |
| 5 | DDD | Ausente; não tem 2 dígitos; não está na lista de DDDs; conflita com o DDD junto ao telefone | — |
| 6 | Telefone | Ausente; tem 8 dígitos; tem qualquer tamanho diferente de 9 depois da normalização, inclusive com prefixo 55 ou 0 | — |
| 7 | Público-alvo | Fora de DS e PR | Ausente: preenchido com DS |

- Preenchimento por padrão (CUR, DS) sempre gera AVISO no registro | Tipo: Invariante
- O CSV final nunca contém situação em minúsculas | Tipo: Invariante
- Validade de CPF não depende de consulta externa: só dos dígitos verificadores oficiais | Tipo: Invariante

**Sugestões automáticas** (aplicadas só com confirmação):
- Polo não idêntico, mas parecido com um item da lista (sem acento, caixa diferente, espaço a mais, erro de digitação) → sugere o item da lista.
- Telefone de 8 dígitos começando com 6, 7, 8 ou 9 → sugere acrescentar o 9.
- Telefone de 8 dígitos começando com 2, 3, 4 ou 5 → é fixo; sugere pedir um celular ao aluno (sem valor sugerido).

**Catálogo de mensagens:**

| Código | Severidade | Mensagem |
|--------|-----------|----------|
| POLO_AUSENTE | ERRO | Polo não informado. Escolha o polo desta linha ou aplique um polo a todo o arquivo. |
| POLO_INVALIDO | ERRO | O polo "X" não está na lista de polos válidos. |
| POLO_SUGESTAO | ERRO | O polo "X" não está escrito exatamente como no SisUAB. Você quis dizer "Y"? |
| POLO_TAMANHO | ERRO | O nome do polo passa de 80 caracteres. |
| CPF_AUSENTE | ERRO | CPF não informado. |
| CPF_NAO_NUMERICO | ERRO | O CPF "X" tem caracteres que não são números. |
| CPF_TAMANHO | ERRO | O CPF "X" tem mais de 11 dígitos. |
| CPF_CIENTIFICO | ERRO | O CPF aparece como "3,42E+10": o Excel cortou os dígitos. Digite o CPF completo. |
| CPF_REPETIDO | ERRO | CPF com todos os dígitos iguais não é válido. |
| CPF_DV_INVALIDO | ERRO | CPF inválido: os dígitos verificadores não conferem. Confira com o aluno. |
| CPF_DUPLICADO | ERRO | CPF repetido: também aparece em [arquivo, linha]. Corrija o CPF ou exclua a linha repetida. |
| CPF_NAO_ENCONTRADO_ORIGEM | ERRO | Este CPF não aparece no documento original; a leitura automática pode ter errado. Confira. |
| SITUACAO_INVALIDA | ERRO | A situação "X" não existe. Use CUR, CAN, TRC, DES, FDO, FAL, TRA, DTT ou TCC. |
| SITUACAO_PADRAO | AVISO | Situação não informada: preenchida como CUR (Cursando). |
| SITUACAO_CONTEXTO | AVISO | Ver RF-09. |
| EMAIL_AUSENTE | ERRO | E-mail não informado. |
| EMAIL_INVALIDO | ERRO | O e-mail "X" não é válido. |
| EMAIL_TAMANHO | ERRO | O e-mail passa de 60 caracteres. |
| EMAIL_CARACTERE | ERRO | O e-mail tem aspas, apóstrofo ou ponto e vírgula, que o SisUAB não aceita. |
| EMAIL_NAO_ASCII | ERRO | O e-mail tem acento ou caractere especial. (**PENDENTE P-01**) |
| DDD_AUSENTE | ERRO | DDD não informado. |
| DDD_INVALIDO | ERRO | O DDD "X" não existe no Brasil. |
| DDD_CONFLITO | ERRO | O DDD da coluna (X) é diferente do DDD junto ao telefone (Y). |
| TEL_AUSENTE | ERRO | Telefone não informado. |
| TEL_8_DIGITOS | ERRO | O telefone tem 8 dígitos; o SisUAB exige 9. [sugestão conforme o caso] |
| TEL_TAMANHO | ERRO | O telefone "X" não tem 9 dígitos. |
| PUBLICO_INVALIDO | ERRO | O público-alvo "X" não existe. Use DS (Demanda Social) ou PR (Professor da Rede). |
| PUBLICO_PADRAO | AVISO | Público-alvo não informado: preenchido como DS (Demanda Social). |

**Tratamento de erros:**
- Lista de DDDs indisponível → aplicação não permite gerar CSV (ver RF-01).

---

### RF-08: Duplicidade de CPF

**Descrição:** o sistema verifica CPFs repetidos entre todos os registros carregados, de todos os arquivos. Não consulta o SisUAB.

**Critérios de aceite:**
- Todas as ocorrências de um CPF repetido recebem ERRO, cada uma apontando as outras.
- Registros com dados idênticos em arquivos diferentes também são ERRO (decisão aprovada).
- A usuária resolve corrigindo um dos CPFs ou excluindo a linha repetida; depois disso, o erro some nas duas linhas.

**Regras:**
- A duplicidade é verificada depois da normalização (ex.: `012.345.678-90` e `1234567890` são o mesmo CPF) | Tipo: Validação
- O sistema nunca exclui nem mescla registros sozinho | Tipo: Autorização
- No arquivo final, nenhum CPF aparece mais de uma vez | Tipo: Invariante

---

### RF-09: Validação contextual parcial

**Descrição:** se a usuária informar o período atual da oferta, o sistema avisa quando a situação parece incompatível com ele.

**Critérios de aceite:**
- O período atual é opcional; sem ele, nenhum aviso contextual aparece.
- Alterar o período revalida todos os registros imediatamente.

**Regras** (todas geram AVISO, nunca ERRO):
- CAN com período atual maior que 2 → "CAN só deveria ser informado no 1º ano (períodos 1 e 2). Período atual: P." (**Premissa**: 1º ano = períodos 1 e 2, conforme o manual) | Tipo: Validação
- DES, TRC ou TRA com período atual menor que 3 → "X só deveria ser informado a partir do 3º período. Período atual: P." | Tipo: Validação
- TCC e FDO não são verificados, pois exigem o total de períodos (decisão aprovada) | Tipo: Validação
- FAL, CUR e DTT não têm regra contextual | Tipo: Validação

**Tratamento de erros:**
- Período informado que não é número inteiro positivo → campo recusa o valor e mostra "Informe o período como número (ex.: 3)."

---

### RF-10: Relatório e edição

**Descrição:** a usuária vê todos os registros numa tabela editável, com os problemas de cada campo, e corrige o que for preciso.

**Critérios de aceite:**
- Mostra contadores: total de registros, registros com ERRO, registros só com AVISO, registros sem problema, linhas descartadas.
- Filtro "somente com erro".
- Cada célula com problema fica destacada por ícone e texto, não só por cor, com a mensagem ao passar o mouse ou ao selecionar.
- A usuária pode editar qualquer célula; a edição revalida tudo.
- A usuária pode excluir um registro, com confirmação.
- Sugestões aparecem com os botões "Aceitar" e "Recusar". Para polo, há também "Aceitar em todas as linhas com o mesmo valor original".
- Para arquivo sem polo, há a ação "Aplicar polo a todas as linhas deste arquivo", com escolha feita na lista de polos.
- Cada linha mostra sua origem (arquivo, aba, linha) e, se houver, o nome do aluno como referência.

**Regras:**
- Toda alteração (edição, sugestão aceita, correção do chat, polo em lote, exclusão) é registrada com valor anterior e novo, e pode ser desfeita enquanto a sessão estiver aberta | Tipo: Transição de Estado
- Após qualquer alteração, todos os registros são revalidados, inclusive a duplicidade | Tipo: Transição de Estado
- O polo só pode ser escolhido na lista de polos válidos, nunca digitado livremente nas ações de lote | Tipo: Validação

**Tratamento de erros:**
- Edição que gera novo problema → o problema aparece na hora, na mesma célula, sem perder a edição.

---

### RF-11: Chat de correções com a IA

**Descrição:** a usuária pede correções em linguagem natural; a IA responde com uma lista de alterações que a usuária confirma antes de aplicar.

**Critérios de aceite:**
- A usuária escreve pedidos como "coloca o polo de Gurupi em todas as linhas do arquivo 2" ou "por que a linha 14 está com erro?".
- Quando o pedido é de correção, a IA devolve alterações no formato (registro, campo, valor novo), mostradas numa lista com caixas de seleção.
- A usuária aplica todas, algumas ou nenhuma. Aplicar revalida tudo.
- Quando o pedido é uma pergunta, a IA explica usando as mensagens do validador.
- Toda alteração proposta pela IA exibe o alerta: "Confira: valores sugeridos pela IA podem estar errados."

**Regras:**
- A IA só propõe alterações de campo; não exclui registros nem muda regras | Tipo: Autorização
- Nenhuma alteração da IA é aplicada sem confirmação explícita | Tipo: Autorização
- Alteração que aponta para registro ou campo inexistente é descartada, com aviso na conversa | Tipo: Validação
- Alteração aplicada passa pela normalização e pela validação completa como qualquer edição | Tipo: Invariante

**Tratamento de erros:**
- IA indisponível → campo do chat desabilitado com "A IA local está desligada. Você ainda pode corrigir direto na tabela."
- Resposta da IA fora do formato → "Não entendi a resposta da IA. Tente escrever o pedido de outro jeito."

---

### RF-12: Geração do CSV

**Descrição:** o sistema monta o arquivo final a partir dos registros validados, seguindo o leiaute SisUAB com as correções.

**Critérios de aceite:**
- Codificação UTF-8 sem marca de início (BOM), preservando acentos e Ç.
- Separador `;` e exatamente 7 campos por linha, na ordem: Polo; CPF; Situação; E-mail; DDD; Telefone; Público-alvo.
- Sem cabeçalho, sem aspas e sem apóstrofos em nenhum campo.
- Uma linha por aluno, na ordem de carregamento dos arquivos e das linhas.
- Quebra de linha conforme a configuração (Linux por padrão, Windows opcional).
- Extensão `.csv`; nome sugerido `sisuab_AAAAMMDD_HHMM.csv` (**Premissa**).
- Exemplo de linha válida: `ARAGUAÍNA-TO CIMBA;01234567890;CUR;aluno@exemplo.com;63;987654321;DS`

**Regras:**
- Nenhuma linha começa com `#` ou `;` | Tipo: Invariante
- O gerador nunca escapa nem envolve valores em aspas: um valor com caractere proibido é bloqueado antes, na validação | Tipo: Invariante
- O último registro termina com quebra de linha (**Premissa**, ver P-02) | Tipo: Invariante
- Registros excluídos e linhas descartadas não entram no arquivo | Tipo: Invariante

---

### RF-13: Verificação final e download

**Descrição:** antes de liberar o download, o sistema relê o arquivo gerado byte a byte e confirma cada exigência.

**Critérios de aceite:**
- A prévia mostra o conteúdo exatamente como será gravado, em texto bruto.
- A verificação confirma:
  - o arquivo não começa com a marca BOM (bytes EF BB BF);
  - decodifica em UTF-8 estrito;
  - toda linha tem 7 campos;
  - não há cabeçalho;
  - não há aspas nem apóstrofos;
  - todos os campos passam no validador;
  - não há CPF duplicado;
  - a situação está em maiúsculas em todas as linhas;
  - o nome do polo é idêntico a um item da lista em todas as linhas.
- O botão "Baixar CSV" só fica habilitado com zero ERROS e verificação aprovada.
- Se a verificação falhar, o motivo aparece em português e o download continua bloqueado.

**Regras:**
- Download habilitado se, e somente se, houver zero ERROS e a verificação do arquivo atual tiver passado | Tipo: Autorização
- Qualquer alteração depois da verificação invalida a verificação e bloqueia o download até nova verificação | Tipo: Transição de Estado
- AVISOS pendentes aparecem resumidos junto ao botão, mas não bloqueiam | Tipo: Validação

**Tratamento de erros:**
- Falha na verificação com zero ERROS no validador (indica defeito do sistema) → mensagem "O arquivo gerado não passou na conferência final (motivo: X). Isso é uma falha do sistema; avise o TI." e download bloqueado.

---

### RF-14: IA local: status e escolha de modelo

**Descrição:** a barra lateral mostra o provedor de IA local, seu endereço, se está online e quais modelos locais estão instalados.

**Critérios de aceite:**
- Mostra o nome do provedor, o endereço e o status online ou offline, com botão "Verificar de novo".
- Lista só os modelos instalados localmente; modelos que rodam em servidor externo nunca aparecem.
- Pré-seleciona o modelo padrão da configuração, se estiver instalado.
- Trocar o modelo não apaga os registros carregados.

**Regras:**
- O endereço da IA só pode apontar para a própria máquina ou para o serviço local da instalação (**Premissa**) | Tipo: Validação
- Modelo que roda fora da máquina nunca pode ser selecionado | Tipo: Autorização

**Tratamento de erros:**
- IA offline → status "offline", com orientação "A IA local não está respondendo. Planilhas e tabelas continuam funcionando." Nenhum bloqueio dos fluxos tabulares.
- Nenhum modelo instalado → "Nenhum modelo de IA instalado. Peça ao TI para instalar o modelo indicado no manual."
- Endereço configurado fora da máquina → a aplicação recusa o endereço e explica o motivo.

---

### RF-15: Privacidade e registro de eventos

**Descrição:** garantias de que nenhum dado de aluno sai da máquina ou fica guardado.

**Critérios de aceite:**
- A aplicação só é acessível a partir da própria máquina.
- Nenhuma chamada a serviços externos, bibliotecas carregadas da internet ou telemetria.
- Registros de eventos (log) nunca mostram CPF, e-mail ou telefone completos: são mascarados (ex.: CPF `*********90`).
- Nenhum dado de aluno é gravado em disco; arquivos temporários, se inevitáveis, são apagados ao fim da etapa.
- Botão "Limpar tudo" descarta arquivos, registros, correções e conversa, com confirmação.
- A tela avisa que fechar a aba descarta o trabalho.

**Regras:**
- A aplicação não mantém nenhum dado de aluno depois que a sessão termina | Tipo: Invariante
- Nenhum dado de aluno sai da máquina em nenhuma situação | Tipo: Invariante

---

### RF-16: Instalação e documentação

**Descrição:** a ferramenta é instalada e iniciada com um único comando e vem documentada em português.

**Critérios de aceite:**
- Instala e inicia com um único comando, em duas modalidades: com contêiner e sem contêiner.
- A IA local pode ficar fora da instalação (já existente na máquina) ou vir junto, como opção.
- Há um arquivo de configuração de exemplo, sem valores sensíveis.
- O manual em português cobre instalação, uso passo a passo, edição da lista de polos e os riscos conhecidos do manual CAPES (R4 e R5).
- A suíte de testes roda com um comando e usa apenas dados fictícios.

---

## 5. Requisitos Não-Funcionais

| Categoria | Requisito | Métrica | Prioridade |
|-----------|-----------|---------|------------|
| Performance | Inicialização da aplicação | ≤ 10 s (**estimativa**) | Média |
| Performance | Leitura e validação de uma planilha de 2.000 linhas | ≤ 5 s | Alta |
| Performance | Revalidação depois de uma edição (2.000 registros) | ≤ 2 s | Alta |
| Performance | Leitura de texto livre pela IA | ≤ 60 s por página em computador sem placa de vídeo (**estimativa**), com progresso visível | Média |
| Capacidade | Volume por sessão | Até 5.000 registros e 50 MB por arquivo (**Premissa**) | Média |
| Compatibilidade | Sistemas operacionais | Windows 10/11 e Linux (Ubuntu 22.04+); macOS sem garantia no MVP (**Premissa**) | Alta |
| Compatibilidade | Navegadores | Versões atuais de Chrome, Edge e Firefox | Alta |
| Memória | Uso da aplicação + IA local | Aplicação ≤ 1 GB; IA conforme o modelo (8 a 16 GB de RAM na máquina, **estimativa**) | Média |
| Armazenamento | Dados persistidos | Nenhum dado de aluno; só logs mascarados, com tamanho limitado | Alta |
| Segurança/Privacidade | Comunicação externa | Zero conexões para fora da máquina; acesso só local | Alta |
| Confiabilidade | Determinismo | Mesma entrada estruturada → arquivo idêntico byte a byte | Alta |
| Usabilidade | Caminho até o download | 4 etapas; todo erro indica onde está e como resolver | Alta |
| Acessibilidade | Indicação de problemas | Nunca só por cor: sempre ícone + texto | Média |
| Manutenibilidade | Testes | 100% dos casos obrigatórios; ≥ 90% de cobertura nas regras de normalização, validação, geração e verificação | Alta |
| Idioma | Interface | Português do Brasil | Alta |

---

## 6. Arquitetura de Informação e Navegação

### 6.1 Layout principal

```
┌───────────────────────┬─────────────────────────────────────────────────────────┐
│ BARRA LATERAL         │ [1 Carregar] [2 Conferir leitura] [3 Corrigir] [4 Baixar]│
│                       ├─────────────────────────────────────────────────────────┤
│ IA local              │                                                         │
│  Provedor · ● online  │  ÁREA DA ETAPA ATUAL                                    │
│  Endereço             │                                                         │
│  [Verificar de novo]  │  Etapa 3, por exemplo:                                  │
│  Modelo [▼]           │  ┌ Contadores: 350 registros · 12 ERRO · 8 AVISO ┐      │
│                       │  │ [ ] Somente com erro                          │      │
│ Oferta                │  ├ Tabela editável (origem, nome ref., 7 campos) ┤      │
│  Período atual [  ]   │  │ ⛔ célula com erro  ⚠ célula com aviso        │      │
│                       │  └───────────────────────────────────────────────┘      │
│ [Limpar tudo]         │  Sugestões pendentes [Aceitar] [Recusar]                │
│                       │  ┌ Chat com a IA ──────────────────────────────┐        │
│ Aviso: fechar a aba   │  │ pedido → alterações propostas [✓] [Aplicar] │        │
│ descarta o trabalho   │  └─────────────────────────────────────────────┘        │
└───────────────────────┴─────────────────────────────────────────────────────────┘
```

### 6.2 Hierarquia de áreas

| Área | Conteúdo | Tipo |
|------|----------|------|
| Barra lateral | IA local, período atual, limpar tudo | Fixa, sempre visível |
| Etapa 1: Carregar | Envio de arquivos e lista de arquivos carregados | Single-page (etapa) |
| Etapa 2: Conferir leitura | Por arquivo: formato, codificação, cabeçalho, abas, mapeamento, polo padrão, progresso da IA, linhas descartadas | Single-page (etapa) |
| Etapa 3: Corrigir | Contadores, filtro, tabela editável, sugestões, chat | Single-page (etapa) |
| Etapa 4: Baixar | Prévia bruta, resultado da verificação, avisos pendentes, botão de download | Single-page (etapa) |
| Confirmações | Excluir registro, limpar tudo, aplicar em lote | Modal |

A usuária pode voltar a qualquer etapa. Avançar para a etapa 3 exige mapeamento confirmado nos arquivos ambíguos.

### 6.3 Estados da tela

| Estado | Gatilho | O que aparece |
|--------|---------|---------------|
| Configuração inválida | Lista de polos ou DDDs ausente, configuração errada | Tela de orientação para o TI, sem acesso às etapas |
| Vazio | Nenhum arquivo carregado | Área de envio com a instrução "Arraste os arquivos dos polos aqui" e os formatos aceitos |
| Carregando | Leitura ou extração em andamento | Barra de progresso por arquivo; na IA, progresso por bloco |
| Aguardando confirmação | Mapeamento ambíguo, codificação ou separador incertos | Destaque no arquivo com a pergunta e a prévia |
| Com erros | Existe pelo menos um ERRO | Contadores em destaque; etapa 4 mostra "Corrija os N erros para liberar o download" |
| Pronto para baixar | Zero ERROS e verificação aprovada | Prévia, resumo dos avisos e botão habilitado |
| Verificação falhou | Conferência final reprovou o arquivo | Banner com o motivo e orientação para avisar o TI |
| IA offline | Provedor local não responde | Status offline na barra lateral; chat desabilitado; blocos de texto livre "não lidos"; fluxos tabulares normais |
| Erro de operação | Falha ao abrir arquivo, resposta inválida da IA | Banner com mensagem descritiva e como resolver |

---

## 7. User Flows Detalhados

### UF-01: Primeiro uso

```
[TI executa o comando único de instalação]
    │
    ▼
[Aplicação inicia] ── configuração inválida ── [Tela de orientação para o TI]
    │
    ▼
[Secretária abre o endereço local no navegador]
    │
    ▼
[Barra lateral verifica a IA local] ── offline ── [Status offline + orientação; fluxos tabulares liberados]
    │
    │ online
    ▼
[Lista modelos locais] ── nenhum modelo ── [Mensagem: pedir ao TI para instalar]
    │
    ▼
[Estado Vazio da etapa 1]
```

### UF-02: Fluxo principal com planilhas (happy path)

```
[Etapa 1: envia 23 planilhas, uma por polo]
    │
    ▼
[Leitura por regras fixas] ── arquivo ilegível ── [Mensagem no arquivo; demais seguem]
    │
    ▼
[Etapa 2: confere detecções] ── mapeamento ambíguo ── [Confirma sugestão ou escolhe coluna]
    │                         ── sem coluna de polo ── [Escolhe polo e aplica ao arquivo]
    ▼
[Normalização + validação de todos os registros]
    │
    ▼
[Etapa 3: contadores e tabela] ── há ERROS ── [Corrige na tabela, aceita sugestões ou usa o chat]
    │                                              │
    │ zero ERROS                                   └── revalida tudo ──┐
    ▼                                                                  │
[Etapa 4: prévia bruta + verificação] ◄────────────────────────────────┘
    │
    ├── verificação falhou ── [Banner com motivo; download bloqueado]
    │
    ▼
[Baixar CSV] → arquivo salvo na pasta de downloads
```

### UF-03: Documento com texto livre (PDF, DOCX ou TXT)

```
[Envia um PDF com páginas de tabela e páginas de texto corrido]
    │
    ▼
[Tabelas lidas por regras fixas]
    │
    ▼
[Texto livre enviado à IA por blocos] ── IA offline ── [Blocos "não lidos" + botão tentar de novo]
    │                                 ── resposta inválida ── [Reenvia uma vez; se falhar, "não lido"]
    ▼
[Registros marcados "lido pela IA"]
    │
    ▼
[Conferência: CPFs no texto × registros extraídos]
    │         ── diferença ── [AVISO no arquivo com os CPFs faltantes]
    │         ── CPF inexistente no texto ── [ERRO no registro]
    ▼
[Segue para a etapa 3 como no UF-02]
```

### UF-04: Troca de contexto (modelo ou período)

```
[Altera o período atual na barra lateral]
    │
    ▼
[Revalida todos os registros] → avisos contextuais atualizados; verificação anterior invalidada

[Troca o modelo de IA]
    │
    ▼
[Registros mantidos] → novas leituras e o chat passam a usar o novo modelo
```

### UF-05: Correção pelo chat

```
[Escreve: "coloca DS em todo mundo do polo de Palmas"]
    │
    ▼
[IA devolve lista de alterações] ── formato inválido ── [Mensagem: reformular pedido]
    │                            ── registro inexistente ── [Alteração descartada com aviso]
    ▼
[Lista com caixas de seleção + alerta "Confira"]
    │
    ├── recusa tudo ── [Nada muda]
    │
    ▼
[Aplica as selecionadas] → normaliza, revalida tudo, registra no histórico
```

### UF-06: CPF duplicado entre arquivos

```
[Planilha geral + planilha do polo contêm o mesmo aluno]
    │
    ▼
[ERRO CPF_DUPLICADO nas duas linhas, cada uma apontando a outra]
    │
    ├── exclui uma das linhas (com confirmação) ── [Revalida: erro some]
    │
    └── corrige o CPF de uma das linhas ── [Revalida: erro some se o novo CPF for válido e único]
```

### 7.1 Estados por ação

```
Ação: Enviar arquivos
  Gatilho:      arrastar ou selecionar arquivos na etapa 1
  Validação:    formato aceito, tamanho ≤ limite, arquivo não repetido → mensagem por arquivo se falhar
  Loading:      barra de progresso por arquivo
  Sucesso:      arquivo na lista com "lido" e total de registros → etapa 2 sugerida
  Erro:         mensagem no arquivo com causa → remover ou reenviar
  Estado do UI: botão de avançar desabilitado enquanto há leitura em andamento
```

```
Ação: Confirmar leitura e mapeamento de um arquivo
  Gatilho:      botão "Confirmar" no cartão do arquivo, na etapa 2
  Validação:    nenhum campo associado a duas colunas → "O campo X está em duas colunas; escolha uma."
  Loading:      indicador no cartão enquanto normaliza e valida
  Sucesso:      cartão marcado como confirmado; contadores atualizados
  Erro:         mensagem no cartão → corrigir o mapeamento
  Estado do UI: etapa 3 bloqueada enquanto houver arquivo ambíguo não confirmado
```

```
Ação: Aplicar polo a todas as linhas de um arquivo
  Gatilho:      botão "Aplicar polo a todo o arquivo" + escolha na lista
  Validação:    polo escolhido pertence à lista (a escolha é só por lista)
  Loading:      indicador breve
  Sucesso:      "Polo X aplicado a N linhas." → revalidação
  Erro:         não se aplica (escolha restrita à lista)
  Estado do UI: modal de confirmação mostra quantas linhas serão alteradas
```

```
Ação: Aceitar sugestão
  Gatilho:      botão "Aceitar" (ou "Aceitar em todas as linhas com o mesmo valor", para polo)
  Validação:    a sugestão ainda corresponde ao valor atual da célula
  Loading:      indicador breve
  Sucesso:      célula atualizada, sugestão removida, alteração no histórico → revalidação
  Erro:         valor mudou desde a sugestão → "Este valor foi alterado; a sugestão foi descartada."
  Estado do UI: botões da sugestão desabilitados durante a aplicação
```

```
Ação: Editar célula
  Gatilho:      editar o valor na tabela e sair da célula
  Validação:    normalização + validação completa
  Loading:      nenhum perceptível (≤ 2 s)
  Sucesso:      problema da célula some ou muda; contadores atualizados
  Erro:         novo problema aparece na célula, sem perder o valor digitado
  Estado do UI: download bloqueado até nova verificação
```

```
Ação: Excluir registro
  Gatilho:      ação "Excluir" na linha
  Validação:    confirmação "Excluir o registro N (origem X)? Ele não irá para o CSV."
  Loading:      indicador breve
  Sucesso:      linha removida, alteração no histórico (pode desfazer) → revalidação
  Erro:         não se aplica
  Estado do UI: download bloqueado até nova verificação
```

```
Ação: Enviar mensagem no chat
  Gatilho:      Enter ou botão "Enviar"
  Validação:    IA online e mensagem não vazia → "A IA local está desligada." se offline
  Loading:      indicador "A IA está pensando..." na conversa
  Sucesso:      resposta ou lista de alterações propostas
  Erro:         "Não entendi a resposta da IA. Tente escrever o pedido de outro jeito."
  Estado do UI: campo de mensagem desabilitado até a resposta
```

```
Ação: Aplicar alterações do chat
  Gatilho:      botão "Aplicar selecionadas"
  Validação:    ao menos uma selecionada; registro e campo existem
  Loading:      indicador breve
  Sucesso:      "N alterações aplicadas." → revalidação, histórico atualizado
  Erro:         alterações inválidas listadas como descartadas
  Estado do UI: lista de propostas travada durante a aplicação
```

```
Ação: Gerar e verificar o CSV
  Gatilho:      entrar na etapa 4 (automático) ou botão "Verificar de novo"
  Validação:    zero ERROS → senão "Corrija os N erros para liberar o download."
  Loading:      indicador "Conferindo o arquivo..."
  Sucesso:      prévia bruta + "Arquivo conferido" + botão de download habilitado
  Erro:         banner com o motivo da reprovação; download bloqueado
  Estado do UI: botão de download desabilitado até a verificação passar
```

```
Ação: Baixar CSV
  Gatilho:      botão "Baixar CSV"
  Validação:    verificação atual aprovada e nenhuma alteração depois dela
  Loading:      nenhum
  Sucesso:      navegador salva o arquivo; mensagem "Arquivo pronto para importar no SisUAB."
  Erro:         verificação invalidada → volta ao estado "Com erros" ou refaz a verificação
  Estado do UI: botão permanece disponível para baixar de novo o mesmo arquivo
```

```
Ação: Limpar tudo
  Gatilho:      botão na barra lateral
  Validação:    confirmação "Isso apaga todos os arquivos, correções e a conversa. Continuar?"
  Loading:      indicador breve
  Sucesso:      estado Vazio da etapa 1
  Erro:         não se aplica
  Estado do UI: modal bloqueia as demais ações até a resposta
```

```
Ação: Verificar a IA de novo
  Gatilho:      botão "Verificar de novo" na barra lateral
  Validação:    endereço aponta para a própria máquina
  Loading:      status "verificando..."
  Sucesso:      status online + lista de modelos atualizada
  Erro:         status offline + orientação
  Estado do UI: seletor de modelo desabilitado durante a verificação
```

---

## 8. Especificação de Features

### Feature: Leitura (RF-02 a RF-05)

**Descrição:** transforma arquivos heterogêneos em registros com origem rastreável, usando IA só onde não há estrutura.

**Componentes internos:** detector de formato; leitor tabular; leitor de tabelas de documentos; leitor de texto livre com IA; conferência de contagem; mapeador de colunas; lista de linhas descartadas.

**Regras:**
- Registro sempre carrega arquivo, aba e linha, ou página e bloco | Tipo: Invariante
- Leitura por IA só ocorre em trechos sem estrutura tabular | Tipo: Validação

**Tratamento de erros:** falha em um arquivo nunca interrompe a leitura dos demais.

**Limitações do MVP:** sem leitura de imagens (PDF escaneado); registros divididos entre duas páginas de PDF podem precisar de correção manual.

### Feature: Normalização e validação (RF-06 a RF-09)

**Descrição:** aplica as regras do SisUAB e as correções ao manual, sem nenhuma dependência da IA.

**Componentes internos:** normalizador por campo; validador por campo; verificador de duplicidade; validador contextual; catálogo de mensagens; gerador de sugestões.

**Regras:**
- Nenhuma regra que não esteja no manual ou nas correções, salvo as premissas marcadas | Tipo: Invariante
- A validação é pura: mesma entrada, mesmo resultado | Tipo: Invariante

**Tratamento de erros:** valor que não pode ser interpretado vira ERRO do campo, nunca uma falha da aplicação.

**Limitações do MVP:** sem validação contextual de TCC e FDO; sem consulta ao SisUAB.

### Feature: Correção (RF-10 e RF-11)

**Descrição:** permite resolver cada problema na própria ferramenta, com rastreabilidade.

**Componentes internos:** tabela editável; histórico de alterações com desfazer; ações em lote; chat com propostas estruturadas.

**Regras:**
- Toda alteração tem origem registrada: edição, sugestão, chat, lote ou exclusão | Tipo: Invariante
- Nenhuma alteração automática sem confirmação | Tipo: Autorização

**Tratamento de erros:** proposta inválida é descartada com aviso, sem afetar as demais.

**Limitações do MVP:** o histórico dura só a sessão.

### Feature: Exportação (RF-12 e RF-13)

**Descrição:** gera o arquivo e prova, relendo os bytes, que ele cumpre o leiaute.

**Componentes internos:** gerador do arquivo; verificador final; prévia bruta.

**Regras:**
- O verificador é independente do gerador: relê o arquivo como um leitor externo faria | Tipo: Invariante

**Tratamento de erros:** reprovação na verificação bloqueia o download e informa o motivo.

**Limitações do MVP:** um único arquivo por carga; não envia ao SisUAB.

### Feature: IA local (RF-14 e parte de RF-04, RF-05 e RF-11)

**Descrição:** assistente opcional para leitura de texto livre, sugestão de mapeamento e correções por conversa.

**Componentes internos:** verificador de status; listador de modelos locais; cliente de respostas estruturadas.

**Regras:**
- Sem a IA, todos os fluxos tabulares funcionam por completo | Tipo: Invariante

**Tratamento de erros:** timeout ou resposta inválida → uma nova tentativa e, depois, estado "não lido" ou mensagem no chat.

**Limitações do MVP:** um provedor de IA local; qualidade depende do modelo e do hardware.

---

## 9. Modelo de Dados

Não há banco de dados: todas as entidades existem só enquanto a sessão está aberta. O detalhamento técnico fica na SPEC.

### Entidades e relacionamentos

```
Carga (sessão) 1 ──── N Arquivo
Arquivo        1 ──── N Registro
Arquivo        1 ──── N Linha descartada
Registro       1 ──── N Problema
Registro       1 ──── N Alteração (histórico)
Registro       1 ──── 0..N Sugestão
```

- Excluir um Arquivo remove seus Registros, Linhas descartadas, Problemas e Sugestões; o histórico registra a remoção.
- Excluir um Registro remove seus Problemas e Sugestões; a Alteração de exclusão fica no histórico e pode ser desfeita.

### Valores permitidos

| Atributo | Valores |
|----------|---------|
| Situação | CUR, CAN, TRC, DES, FDO, FAL, TRA, DTT, TCC |
| Público-alvo | DS (Demanda Social), PR (Professor da Rede) |
| Severidade | ERRO, AVISO |
| Método de leitura | Tabular, Tabela de documento, IA |
| Origem da alteração | Edição, Sugestão, Chat, Lote, Exclusão |
| Estado da sugestão | Pendente, Aceita, Recusada, Descartada |
| Estado da proposta do chat | Proposta, Aplicada, Recusada, Descartada |

### Máquinas de estado

**Carga:**
```
VAZIA ──envio──► LENDO ──leitura concluída──► AGUARDANDO_CONFIRMAÇÃO ──confirmação──► EM_CORREÇÃO
                                   └──sem ambiguidade──────────────────────────────►  EM_CORREÇÃO
EM_CORREÇÃO ──zero ERROS + verificação aprovada──► PRONTA
PRONTA ──qualquer alteração──► EM_CORREÇÃO
qualquer estado ──Limpar tudo──► VAZIA
```

**Registro (derivado, recalculado a cada validação):** COM_ERRO, SÓ_AVISO ou OK.

**Sugestão:** PENDENTE → ACEITA | RECUSADA | DESCARTADA (quando o valor muda antes da decisão).

### Invariantes de dados

- Nenhum dado de aluno persiste depois da sessão.
- Todo registro tem origem.
- Estado PRONTA implica zero ERROS e verificação do arquivo atual aprovada.

**Estratégia de migração:** não se aplica, porque não há persistência.

---

## 10. Integrações e Dependências

| Dependência | Tipo | Propósito |
|-------------|------|-----------|
| Provedor de IA local, na própria máquina | Opcional em tempo de uso | Leitura de texto livre, sugestão de mapeamento, chat |
| Lista de polos válidos (arquivo editável) | Obrigatória | Validação do Nome do Polo |
| Lista de DDDs válidos (arquivo editável) | Obrigatória | Validação do DDD |

**Capacidades consumidas do provedor de IA local:**

| Capacidade | Propósito | Quando usada |
|------------|-----------|--------------|
| Verificar se está ativo | Status na barra lateral | Ao abrir e ao clicar em "Verificar de novo" |
| Listar modelos instalados | Seletor de modelo | Ao verificar o status |
| Gerar resposta em estrutura fixa | Leitura de texto livre, mapeamento, chat | Durante a leitura e no chat |

Nenhum outro serviço é consumido. Endereços, versões e formatos técnicos ficam na SPEC.

---

## 11. Requisitos de Instalação e Distribuição

- **Pré-requisitos do usuário final:** computador com 8 a 16 GB de RAM (**estimativa**), navegador atual e o provedor de IA local com um modelo instalado (opcional para fluxos tabulares).
- **Instalação:** um único comando, com ou sem contêiner, executado pelo TI.
- **Uso:** a secretária abre um endereço local no navegador; um atalho na área de trabalho é recomendado.
- **Arquivos editáveis:** lista de polos, lista de DDDs e arquivo de configuração (endereço da IA, modelo padrão, porta, quebra de linha).
- **Dados do usuário:** nenhum dado de aluno é guardado; só logs mascarados.
- **Estrutura de diretórios e comandos:** definidos na SPEC.

---

## 12. Roadmap e Priorização

**Sprint plan** (**estimativa**, desenvolvedor solo)

| Sprint | Semanas | Features (RF) | Entregável |
|--------|---------|---------------|------------|
| 1 | 1 | RF-01, RF-06, RF-07, RF-08, RF-09, RF-12, RF-13 | Núcleo de regras testado: dados já estruturados viram CSV verificado |
| 2 | 1 | RF-02, RF-03, RF-05, RF-10 | Interface completa para planilhas, CSV e JSON, sem IA |
| 3 | 1–2 | RF-14, RF-04, RF-11 | Leitura de documentos com IA, sugestão de mapeamento e chat |
| 4 | 1 | RF-15, RF-16 | Privacidade verificada, instalação em um comando, manual e piloto com a secretária |

**Pós-MVP v1**

| Feature | Prioridade |
|---------|------------|
| Validação contextual completa (total de períodos: TCC, FDO e "até o último") | Alta |
| Instalador com atalho para Windows | Média |
| Leitura de PDF escaneado, local | Baixa |
| Perfis por IES, com listas de polos diferentes | Baixa |

---

## 13. Fora de Escopo (MVP)

| Item | Motivo da exclusão |
|------|--------------------|
| Consulta ao SisUAB para checar alunos já cadastrados | Não há integração; decisão do prompt |
| Autenticação e vários usuários | Uso local por uma usuária |
| Histórico de importações entre sessões | Privacidade: não guardar dados |
| Leitura de PDF escaneado | Complexidade; exige arquivo com texto |
| Validação contextual de TCC e FDO | Exige total de períodos (decisão aprovada) |
| Remoção ou mesclagem automática de duplicatas | Decisão aprovada: correção manual |
| IA em nuvem ou qualquer serviço externo | Regra de privacidade |
| Envio automático do arquivo ao SisUAB | Upload segue manual no SisUAB |
| Acesso por outras máquinas da rede | Faria os dados saírem da máquina |

---

## 14. Riscos e Mitigações

| # | Risco | Prob. | Impacto | Mitigação |
|---|-------|-------|---------|-----------|
| R1 | IA omite ou inventa registros ao ler texto livre | Média | Alto | Conferência de contagem; CPF precisa existir no texto original; marcação "lido pela IA"; revisão antes do download |
| R2 | Máquina sem memória suficiente para a IA | Média | Médio | Modelo menor configurável; fluxos tabulares independentes da IA |
| R3 | CAPES muda o leiaute ou os polos | Baixa | Médio | Regras centralizadas; polos em arquivo editável |
| R4 | Manual contraditório: CPF já existente na oferta é ALTERADO (§3) ou IGNORADO (§4, regra 9) | Alta | Médio | Fora do alcance da ferramenta; documentado no manual de uso; confirmar no piloto |
| R5 | Na inclusão, o SisUAB grava o aluno como CURSANDO, podendo sobrescrever outra situação | Alta | Baixo | Dica na tela e no manual de uso; sem bloqueio |
| R6 | Vazamento acidental por configuração (acesso pela rede, modelo externo, log completo) | Baixa | Alto | Regras de RF-14 e RF-15 + testes automáticos de privacidade |
| R7 | IA do chat propõe valor inventado (ex.: e-mail) | Média | Médio | Confirmação obrigatória, alerta "Confira" e validação completa |
| R8 | Dados reais em testes ou no repositório | Baixa | Alto | Só dados fictícios; arquivos de entrada e saída fora do controle de versão |
| R9 | Instalação difícil no computador da secretária | Média | Médio | Duas modalidades de instalação; manual com passo a passo |

---

## 15. Critérios de Aceite Globais

O MVP está completo quando:

```
1. ✅ Instala e inicia com um único comando, com e sem contêiner, numa máquina limpa.
2. ✅ Uma carga com planilhas de vários polos gera um CSV com 7 campos, separador ";",
      UTF-8 sem BOM, sem cabeçalho e sem aspas, aceito na importação de teste do SisUAB.
3. ✅ Com qualquer ERRO pendente, o botão de download fica desabilitado.
4. ✅ A verificação final relê o arquivo e reprova qualquer desvio da lista do RF-13.
5. ✅ Todos os casos de teste obrigatórios passam: CPF válido, inválido, com zero à esquerda,
      formatado, repetido e em notação científica; duplicidade; DDD 061 → 61; telefone com
      8, 9 e 11 dígitos; polo exato, aproximado e ausente; espaços extras; público-alvo
      ausente; ARAGUAÍNA e XAMBIOÁ gravados e relidos corretamente; ausência de BOM;
      entrada com cabeçalho.
6. ✅ Um documento com texto livre é lido pela IA local e passa pela mesma validação,
      com a conferência de contagem funcionando.
7. ✅ Durante todo o uso, nenhuma conexão sai da máquina, e os logs não contêm
      CPF, e-mail ou telefone completos.
8. ✅ Com a IA desligada, uma carga de planilhas é processada até o download.
9. ✅ O manual em português cobre instalação, uso, edição da lista de polos e os riscos R4 e R5.
```

---

## 16. Glossário

| Termo | Definição |
|-------|-----------|
| UAB | Universidade Aberta do Brasil, sistema de ensino superior a distância coordenado pela CAPES |
| SisUAB2 | Sistema da CAPES onde as instituições cadastram e atualizam os alunos das ofertas UAB |
| Polo | Unidade de apoio presencial onde o aluno está vinculado; o nome deve ser idêntico ao registrado no SisUAB |
| Oferta | Turma de um curso UAB, com períodos definidos |
| Período atual | Período em andamento na oferta; opcional, usado nos avisos contextuais |
| Situação | Código de 3 letras do estado do aluno (CUR, CAN, TRC, DES, FDO, FAL, TRA, DTT, TCC) |
| Público-alvo | Código de ocupação da vaga: DS (Demanda Social) ou PR (Professor da Rede) |
| Carga | Conjunto de todos os arquivos enviados numa sessão, que gera um único CSV |
| Registro | Um aluno na carga, com os 7 campos e sua origem |
| Linha descartada | Linha de um arquivo que não parece conter dados de aluno; fica listada para revisão |
| ERRO | Problema que bloqueia o download |
| AVISO | Alerta destacado que não bloqueia o download |
| Sugestão | Valor proposto pelo sistema, aplicado só com confirmação |
| Proposta do chat | Alteração sugerida pela IA na conversa, aplicada só com confirmação |
| BOM | Marca invisível que alguns programas gravam no início de arquivos UTF-8; o SisUAB não deve recebê-la |
| Acentuação composta | Forma em que "Á" é um único caractere; evita que nomes visualmente iguais sejam considerados diferentes |
| Verificação final | Releitura do arquivo gerado para provar que cumpre o leiaute antes do download |
| IA local | Modelo de linguagem que roda na própria máquina, sem enviar dados para fora |

---

## Pendências

| ID | Tema | Situação |
|----|------|----------|
| P-01 | E-mail com acento ou caractere não ASCII | **Decisão necessária.** Opções: ERRO (conservador) ou aceitar |
| P-02 | Quebra de linha após o último registro | **Premissa:** o último registro termina com quebra de linha. O manual não trata disso |

**Premissas do MVP Scope incorporadas:** público-alvo em maiúsculas; telefone com prefixo 55 ou 0 é ERRO; conflito de DDD é ERRO; linhas sem dados de aluno ficam listadas como descartadas; todas as abas com dados são lidas, com opção de desmarcar; telefone de 8 dígitos tem sugestão conforme seja celular ou fixo.

---

## Checklist de qualidade

- [x] Princípios de design declarados
- [x] Mapa de casos de uso liga personas a features
- [x] RFs com critérios de aceite verificáveis
- [x] Regras classificadas por tipo
- [x] Tratamento de erros por feature
- [x] Estados da tela, incluindo vazio e erros
- [x] User flows com onboarding, happy path e ramificações de erro
- [x] Estados por ação com gatilho, validação, loading, sucesso, erro e estado do UI
- [x] Features com componentes, regras tipadas e limitações
- [x] Modelo de dados com constraints, estados e estratégia de migração (não se aplica)
- [x] Instalação e distribuição cobertas no nível de produto
- [x] Critérios de aceite globais binários
- [x] Fora de escopo com motivo
- [x] Roadmap em sprints com entregáveis
- [x] Sem menção a biblioteca, framework, linguagem ou infraestrutura
