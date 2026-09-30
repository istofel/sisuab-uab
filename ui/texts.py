"""Rótulos e mensagens exibidos na interface."""

PAGE_TITLE = "Importador SisUAB com IA"
PAGE_CAPTION = "Da planilha ao CSV do SisUAB, com dados só neste computador."
STEPS = ("1. Enviar", "2. Conferir", "3. Corrigir", "4. Baixar")
STEP_UNAVAILABLE = "Esta etapa será exibida quando os arquivos forem carregados."
CONFIG_ERROR = (
    "Configuração inválida. Peça ao responsável técnico para conferir os arquivos locais."
)
CONFIG_KEY = "Verifique: {key}"
SIDEBAR_TITLE = "Configuração da carga"
OLLAMA_ONLINE = "✅ IA local online"
OLLAMA_OFFLINE = "⚠️ IA local offline. Planilhas e arquivos estruturados continuam disponíveis."
OLLAMA_RECHECK = "Verificar IA de novo"
MODEL_LABEL = "Modelo local"
MODEL_UNAVAILABLE = "Nenhum modelo local disponível."
PERIOD_LABEL = "Período atual da oferta (opcional)"
CLEAR_LABEL = "Limpar tudo"
CLEAR_TITLE = "Limpar esta carga?"
CLEAR_WARNING = "Todos os arquivos, registros e correções desta sessão serão removidos."
CLEAR_CONFIRM = "Sim, limpar"
CLEAR_CANCEL = "Cancelar"
UPLOAD_TITLE = "Enviar arquivos"
UPLOAD_HELP = "Arraste os arquivos dos polos aqui. Aceitos: PDF, CSV, XLSX, XLS, DOCX, JSON e TXT."
UPLOAD_LOADED = "Arquivos carregados"
UPLOAD_EMPTY = "Nenhum arquivo nesta carga."
UPLOAD_REMOVE = "Remover arquivo"
UPLOAD_REMOVE_TITLE = "Remover este arquivo?"
UPLOAD_REMOVE_WARNING = "Os registros e as correções deste arquivo serão removidos."
UPLOAD_REMOVE_CONFIRM = "Sim, remover"
UPLOAD_CONTINUE = "Continuar para Conferir"
REVIEW_TITLE = "Conferir leitura"
REVIEW_EMPTY = "Envie um arquivo na etapa 1 para conferir a leitura."
REVIEW_FILE = "{name} · {format} · {rows} linha(s)"
REVIEW_STATE = "Estado: {state}"
REVIEW_ENCODING = "Codificação: {encoding} · separador: {delimiter}"
REVIEW_TABLE = "{sheet} · {rows} linha(s)"
REVIEW_PREVIEW = "Prévia dos dados lidos"
REVIEW_MAPPING = "Coluna {index}: {name}"
REVIEW_POLO_DEFAULT = "Polo para todas as linhas deste arquivo"
REVIEW_SELECT_TABLE = "Incluir esta aba/tabela"
REVIEW_CONFIRM = "Confirmar leitura"
REVIEW_CONFLICT = "Um campo foi associado a mais de uma coluna: {fields}."
REVIEW_MISSING_POLO = "Associe a coluna Polo ou escolha um polo para o arquivo."
REVIEW_AI_PENDING = "Há trechos com dados de aluno aguardando leitura pela IA local."
REVIEW_AI_BUTTON = "Ler trechos com a IA"
REVIEW_AI_OFFLINE = "A IA local está offline. Tente de novo quando ela estiver disponível."
REVIEW_AI_FOUND = "{count} registro(s) extraído(s) pela IA, aguardando sua confirmação."
REVIEW_DISCARDED = "Linhas descartadas: {count} · linhas vazias: {empty}"
REVIEW_REBUILD_TITLE = "Reconstruir este arquivo?"
REVIEW_REBUILD_WARNING = "As correções já feitas nos registros deste arquivo serão perdidas."
REVIEW_REBUILD_CONFIRM = "Sim, reconstruir"
REVIEW_CONTINUE = "Continuar para Corrigir"
REVIEW_BLOCKED = "Confirme os arquivos pendentes antes de abrir a etapa 3."
REVIEW_NO_RECORDS = "Confirme ao menos um registro antes de continuar."
FIELD_OPTIONS = {
    "ignorar": "Ignorar",
    "nome": "Nome (referência)",
    "polo": "Polo",
    "cpf": "CPF",
    "situacao": "Situação",
    "email": "E-mail",
    "ddd": "DDD",
    "telefone": "Telefone",
    "publico_alvo": "Público-alvo",
}
FIX_TITLE = "Corrigir registros"
FIX_EMPTY = "Nenhum registro confirmado para corrigir."
FIX_SUMMARY_TITLE = "Resumo das pendências e sugestões"
FIX_SUMMARY_ERRORS = "Registros com erro"
FIX_SUMMARY_WARNINGS = "Avisos"
FIX_SUMMARY_SUGGESTIONS = "Correções sugeridas"
FIX_SUMMARY_BY_FIELD = "Erros por campo: {details}"
FIX_SUMMARY_WARNINGS_BY_FIELD = "Avisos por campo: {details}"
FIX_SUMMARY_BY_SUGGESTION = "Sugestões por destino: {details}"
FIX_SUMMARY_SUGGESTION_ITEM = "{field} → {proposed}: {count} registro(s)"
FIX_SUMMARY_NONE = "Nenhum"
FIX_COUNTS = (
    "{total} registros · {errors} com ERRO · {warnings} só com AVISO · "
    "{ok} sem problema · {discarded} descartadas"
)
FIX_STATUS_ERROR = "⛔ ERRO"
FIX_STATUS_WARNING = "⚠️ AVISO"
FIX_STATUS_OK = "✅ OK"
FIX_ONLY_ERRORS = "Mostrar somente linhas com erro"
FIX_SHOW_ORIGINAL = "Mostrar dados originais"
FIX_NUMBER = "Nº"
FIX_ORIGIN = "Origem"
FIX_NAME = "Nome (ref.)"
FIX_STATE = "Situação do registro"
FIX_ISSUES = "Problemas"
FIX_INFORMATION = "Informações"
FIX_INFORMATION_TITLE = "Preenchimentos automáticos (informações)"
FIX_INFORMATION_SUMMARY = "{count} registro(s): {message}"
FIX_DELETE_COLUMN = "Excluir"
FIX_DELETE_BUTTON = "Excluir marcados"
FIX_DELETE_TITLE = "Excluir os registros marcados?"
FIX_DELETE_WARNING = "{count} registro(s) serão excluídos. Você poderá desfazer esta ação."
FIX_DELETE_CONFIRM = "Sim, excluir"
FIX_UNDO = "Desfazer última alteração"
FIX_NO_ERRORS = "Nenhum registro com erro neste filtro."
FIX_ALL_CORRECTED = "Todos os erros foram corrigidos."
FIX_BLOCKED = "Ainda há {errors} registro(s) com erro. Corrija antes de continuar."
FIX_PENDING_ACTIONS = "Conclua ou cancele as alterações pendentes antes de continuar."
FIX_CONTINUE = "Continuar para Baixar"
FIX_DETAILS = "Detalhes dos problemas"
FIX_FILE_POLO = "Aplicar polo a um arquivo"
FIX_FILE_SELECT = "Arquivo"
FIX_POLO_SELECT = "Polo válido"
FIX_POLO_APPLY = "Aplicar polo ao arquivo"
FIX_POLO_TITLE = "Aplicar polo a todas as linhas do arquivo?"
FIX_POLO_CONFIRM = "Sim, aplicar polo"
SUGGEST_TITLE = "Sugestões pendentes"
SUGGEST_EMPTY = "Nenhuma sugestão pendente."
SUGGEST_ITEM = "Registro {record} · {field}: {current} → {proposed}"
SUGGEST_GROUP = "{count} registros · Polo sugerido: {proposed}"
SUGGEST_GROUP_VALUES = "Nomes importados: {values}"
SUGGEST_GROUP_ACCEPT = "Revisar troca em {count} registros"
SUGGEST_GROUP_REJECT = "Recusar para estes registros"
SUGGEST_POLO_ALL_WARNING = 'Trocar o polo de {count} registro(s) por "{proposed}"?'
SUGGEST_CURRENT_POLO = "Polo importado"
SUGGEST_PROPOSED_POLO = "Polo sugerido"
SUGGEST_ACCEPT = "Aceitar"
SUGGEST_REJECT = "Recusar"
SUGGEST_ALL_TITLE = "Aplicar esta sugestão em lote?"
SUGGEST_ALL_WARNING = "{count} registro(s) com o mesmo valor serão alterados."
SUGGEST_ALL_CONFIRM = "Sim, aplicar em todas"
CHAT_TITLE = "Correções com a IA local"
CHAT_INPUT = "Peça uma explicação ou proponha uma correção"
CHAT_OFFLINE = "A IA local está desligada. Você ainda pode corrigir direto na tabela."
CHAT_RESPONSE_ERROR = "Não entendi a resposta da IA. Tente escrever o pedido de outro jeito."
CHAT_WARNING = "Confira: valores sugeridos pela IA podem estar errados."
CHAT_PROPOSAL = "Registro {record} · {field}: {current} → {new}"
CHAT_APPLY = "Aplicar selecionadas"
CHAT_REJECT = "Recusar todas"
CHAT_CONTEXT_TRUNCATED = "O contexto foi limitado a 150 registros com problemas."
CHAT_INVALID = "Proposta descartada: {reason}"
CHAT_REASONS = {
    "REGISTRO_INEXISTENTE": "registro inexistente",
    "REGISTRO_EXCLUIDO": "registro excluído",
    "REGISTRO_FORA_CONTEXTO": "registro fora do pedido",
    "VALOR_MUITO_LONGO": "valor longo demais",
    "VALOR_INVALIDO": "o valor não passou na validação do campo",
}
DOWNLOAD_TITLE = "Conferir e baixar CSV"
DOWNLOAD_EMPTY = "Nenhum registro confirmado para exportar."
DOWNLOAD_BLOCKED = "Corrija os {errors} registro(s) com erro para liberar o download."
DOWNLOAD_VERIFY = "Conferir arquivo gerado"
DOWNLOAD_VERIFIED = "✅ Arquivo conferido. O download está liberado."
DOWNLOAD_STALE = "Confira o arquivo desta revisão antes de baixar."
DOWNLOAD_FAILURE = (
    "O arquivo gerado não passou na conferência final. Isso é uma falha do sistema; avise o TI."
)
DOWNLOAD_FAILURE_REASON = "Motivo: {reason}"
DOWNLOAD_PREVIEW = "Prévia bruta do arquivo"
DOWNLOAD_PREVIEW_COUNT = "Mostrando {shown} de {total} linha(s)."
DOWNLOAD_WARNINGS = "Há {count} registro(s) só com aviso. Confira antes de importar."
DOWNLOAD_BUTTON = "Baixar CSV"
NAV_BLOCKED = {
    2: "Envie pelo menos um arquivo para conferir.",
    3: "Confirme a leitura dos arquivos e ao menos um registro antes de corrigir.",
    4: "Corrija os erros e resolva as alterações pendentes antes de baixar.",
}
