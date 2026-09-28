"""Mensagens de validação e de arquivo exibidas à usuária."""

from core.models import NoticeLevel, Severity

CATALOG: dict[str, tuple[Severity, str]] = {
    "POLO_AUSENTE": (
        Severity.ERRO,
        "Polo não informado. Escolha o polo desta linha ou aplique um polo a todo o arquivo.",
    ),
    "POLO_INVALIDO": (Severity.ERRO, 'O polo "{valor}" não está na lista de polos válidos.'),
    "POLO_SUGESTAO": (
        Severity.ERRO,
        'O polo "{valor}" não está escrito exatamente como no SisUAB. '
        'Você quis dizer "{sugestao}"?',
    ),
    "POLO_TAMANHO": (Severity.ERRO, "O nome do polo passa de 80 caracteres."),
    "CPF_AUSENTE": (Severity.ERRO, "CPF não informado."),
    "CPF_NAO_NUMERICO": (Severity.ERRO, 'O CPF "{valor}" tem caracteres que não são números.'),
    "CPF_TAMANHO": (Severity.ERRO, 'O CPF "{valor}" tem mais de 11 dígitos.'),
    "CPF_CIENTIFICO": (
        Severity.ERRO,
        'O CPF aparece como "{valor}": o Excel cortou os dígitos. Digite o CPF completo.',
    ),
    "CPF_REPETIDO": (Severity.ERRO, "CPF com todos os dígitos iguais não é válido."),
    "CPF_DV_INVALIDO": (
        Severity.ERRO,
        "CPF inválido: os dígitos verificadores não conferem. Confira com o aluno.",
    ),
    "CPF_DUPLICADO": (
        Severity.ERRO,
        "CPF repetido: também aparece em {outros}. Corrija o CPF ou exclua a linha repetida.",
    ),
    "CPF_NAO_ENCONTRADO_ORIGEM": (
        Severity.ERRO,
        "Este CPF não aparece no documento original; a leitura automática pode ter errado. "
        "Confira.",
    ),
    "SITUACAO_INVALIDA": (
        Severity.ERRO,
        'A situação "{valor}" não existe. Use CUR, CAN, TRC, DES, FDO, FAL, TRA, DTT ou TCC.',
    ),
    "SITUACAO_PADRAO": (Severity.INFO, "Situação não informada: preenchida como CUR (Cursando)."),
    "SITUACAO_CONTEXTO": (
        Severity.AVISO,
        "{orientacao} Período atual: {periodo}.",
    ),
    "EMAIL_AUSENTE": (Severity.ERRO, "E-mail não informado."),
    "EMAIL_INVALIDO": (Severity.ERRO, 'O e-mail "{valor}" não é válido.'),
    "EMAIL_TAMANHO": (Severity.ERRO, "O e-mail passa de 60 caracteres."),
    "EMAIL_CARACTERE": (
        Severity.ERRO,
        "O e-mail tem aspas, apóstrofo ou ponto e vírgula, que o SisUAB não aceita.",
    ),
    "EMAIL_NAO_ASCII": (Severity.ERRO, "O e-mail tem acento ou caractere especial."),
    "DDD_AUSENTE": (Severity.ERRO, "DDD não informado."),
    "DDD_INVALIDO": (Severity.ERRO, 'O DDD "{valor}" não existe no Brasil.'),
    "DDD_CONFLITO": (
        Severity.ERRO,
        "O DDD da coluna ({valor}) é diferente do DDD junto ao telefone ({telefone}).",
    ),
    "TEL_AUSENTE": (Severity.ERRO, "Telefone não informado."),
    "TEL_8_DIGITOS": (Severity.ERRO, "O telefone tem 8 dígitos; o SisUAB exige 9. {orientacao}"),
    "TEL_TAMANHO": (Severity.ERRO, 'O telefone "{valor}" não tem 9 dígitos.'),
    "PUBLICO_INVALIDO": (
        Severity.ERRO,
        'O público-alvo "{valor}" não existe. Use DS (Demanda Social) ou PR (Professor da Rede).',
    ),
    "PUBLICO_PADRAO": (
        Severity.INFO,
        "Público-alvo não informado: preenchido como DS (Demanda Social).",
    ),
}

FILE_CATALOG: dict[str, tuple[NoticeLevel, str]] = {
    "ARQ_FORMATO_NAO_SUPORTADO": (
        NoticeLevel.RECUSADO,
        "O arquivo {nome} não é de um tipo aceito. Envie PDF, CSV, XLSX, XLS, DOCX, JSON ou TXT.",
    ),
    "ARQ_ILEGIVEL": (
        NoticeLevel.RECUSADO,
        "Não foi possível abrir {nome}. Verifique se o arquivo abre no seu computador "
        "e se não tem senha.",
    ),
    "ARQ_MUITO_GRANDE": (NoticeLevel.RECUSADO, "{nome} passa de 50 MB."),
    "ARQ_REPETIDO": (NoticeLevel.RECUSADO, "{nome} já foi carregado."),
    "ARQ_LIMITE_REGISTROS": (
        NoticeLevel.RECUSADO,
        "Com {nome}, a carga passaria de 5.000 alunos. Divida o trabalho em duas cargas.",
    ),
    "ARQ_JSON_FORMATO": (
        NoticeLevel.RECUSADO,
        "O JSON de {nome} não está num formato reconhecido (esperado: lista de alunos).",
    ),
    "ARQ_EXTENSAO_DIVERGENTE": (
        NoticeLevel.AVISO,
        "{nome} tem extensão {ext}, mas o conteúdo parece {fmt}. Li como {fmt}.",
    ),
    "ARQ_VAZIO": (NoticeLevel.AVISO, "Nenhum aluno encontrado em {nome}."),
    "ARQ_SEM_TEXTO": (
        NoticeLevel.AVISO,
        "O PDF {nome} parece ser uma imagem escaneada. Esta versão não lê imagens; "
        "peça o arquivo original ao polo.",
    ),
    "ARQ_TRECHO_NAO_LIDO": (
        NoticeLevel.AVISO,
        "{n} trecho(s) de texto de {nome} com possíveis dados de aluno não foram lidos.",
    ),
    "ARQ_CONTAGEM_DIVERGENTE": (
        NoticeLevel.AVISO,
        "O documento tem {n} CPF(s) que não viraram registro: {lista}.",
    ),
}

VERIFY_CATALOG: dict[str, str] = {
    "V01": "O arquivo tem marca BOM no início.",
    "V02": "O arquivo não está em UTF-8 válido.",
    "V03": "A quebra de linha ou o fim do arquivo está incorreto.",
    "V04": "Há uma linha vazia no arquivo.",
    "V05": "A linha não tem exatamente sete campos.",
    "V06": "O arquivo parece ter cabeçalho ou CPF fora do leiaute.",
    "V07": "O arquivo contém aspas ou apóstrofo.",
    "V08": "A linha começa com caractere proibido.",
    "V09": "O polo da linha não coincide com a lista válida.",
    "V10": "Um campo da linha não passa na validação final.",
    "V11": "Há CPF repetido no arquivo.",
    "V12": "A situação não está em maiúsculas ou é inválida.",
}

CHAT_CATALOG: dict[str, str] = {
    "CAMPO_PROPOSTO": (
        "Proposta de correção de {campo} no registro {registro}. Confira o valor e clique em "
        "Aplicar selecionadas para confirmar."
    ),
    "CAMPO_INVALIDO": (
        "O valor informado para {campo} é inválido e não pode ser aplicado. "
        "Nenhuma alteração foi proposta."
    ),
    "REGISTRO_INEXISTENTE": "O registro {registro} não foi encontrado nesta carga.",
    "NOME_AMBIGUO": (
        "Há mais de um aluno com esse nome. Informe o nome completo ou o número do registro."
    ),
    "ALVO_CONFLITANTE": (
        "O nome e o número do registro indicam alunos diferentes. Confira o pedido."
    ),
    "ERROS_REGISTRO": "Registro {registro}: {detalhes}",
    "SEM_ERROS_REGISTRO": "Não há erro pendente no registro {registro}.",
}


def msg(code: str, **kwargs: str) -> tuple[Severity, str]:
    """Formata uma mensagem de validação."""
    severity, template = CATALOG[code]
    return severity, template.format(**kwargs)


def file_msg(code: str, **kwargs: str) -> tuple[NoticeLevel, str]:
    """Formata um aviso de arquivo."""
    level, template = FILE_CATALOG[code]
    return level, template.format(**kwargs)


def phone_orientation(mobile: bool) -> str:
    """Texto contextual para telefone de oito dígitos."""
    if mobile:
        return "Sugestão: incluir o 9 antes do número."
    return "Parece um telefone fixo: peça um celular ao aluno."


def context_orientation(situacao: str) -> str:
    """Texto contextual para situação fora do período esperado."""
    if situacao == "CAN":
        return "CAN só deveria ser informado no 1º ano (períodos 1 e 2)."
    return f"{situacao} só deveria ser informado a partir do 3º período."


def verify_msg(code: str) -> str:
    """Mensagem de uma falha na conferência final."""
    return VERIFY_CATALOG[code]


def chat_msg(code: str, **kwargs: str) -> str:
    """Formata uma resposta local para pedidos objetivos do chat."""
    return CHAT_CATALOG[code].format(**kwargs)
