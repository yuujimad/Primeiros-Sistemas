
# MÓDULO: dados_colonia.py
# FUNÇÃO : Guardar e fornecer todos os dados da colônia espacial.
#
# Estruturas de dados usadas:
#   dict (dicionário)  → acesso por chave em tempo O(1), ideal para sensores
#   dict aninhado      → hierarquia de sistemas (árvore: sistema→subsistema)
#   list (lista)       → histórico ordenado por índice de tempo
#
# Regra deste módulo: só ARMAZENA e FORNECE dados. Não toma decisões.


# MODO DE OPERAÇÃO GLOBAL
#
# MODO_MANUAL = False → usa os valores fixos definidos abaixo (padrão)
# MODO_MANUAL = True  → o sistema pedirá ao usuário que digite os valores
#
# Pode ser trocado pelo menu do main.py ou diretamente aqui.

MODO_MANUAL = False

# SEÇÃO 1 — ESTADO ATUAL DA COLÔNIA (dicionário de sensores)
#
# Representa o "snapshot" do momento: leitura dos sensores em tempo real.
# Usar um dict garante acesso rápido por nome (chave), sem busca em lista.

estado_atual = {
    # ── Energia ──────────────────────────────────────────────────────────────
    "energia_reserva_kwh"  : 45,       # kWh armazenados nas baterias
    "geracao_solar_kw"     : 20,       # kW gerados pelos painéis solares agora
    "geracao_eolica_kw"    : 15,       # kW gerados pelos aerogeradores agora
    "consumo_total_kw"     : 70,       # kW consumidos pela colônia agora

    # ── Clima ─────────────────────────────────────────────────────────────────
    "velocidade_vento_ms"  : 11,       # m/s — velocidade do vento
    "irradiacao_solar_wm2" : 600,      # W/m² — intensidade da luz solar
    "temperatura_c"        : 22,       # °C — temperatura ambiente interna
    "previsao_clima"       : "adverso",# "favoravel" | "neutro" | "adverso"

    # ── Ciclo de tempo ────────────────────────────────────────────────────────
    "hora_do_dia"          : 14,       # hora no formato 0–23
}

# SEÇÃO 2 — HIERARQUIA DE SISTEMAS (dict aninhado = estrutura em árvore)
#
# Organização: sistema → subsistema → dados do subsistema
#
# Cada subsistema tem:
#   "prioridade" : 1 = crítico (nunca desligar), 2 = importante, 3 = dispensável
#   "ativo"      : estado operacional atual (True/False)
#   "consumo_kw" : quanto este subsistema consome (0 se for gerador)
#   "descricao"  : texto explicativo para o operador

hierarquia_sistemas = {

    "sistema_energetico": {
        "solar"   : {"prioridade": 1, "ativo": True, "consumo_kw": 0,
                     "descricao": "Painéis fotovoltaicos da superfície"},
        "eolico"  : {"prioridade": 1, "ativo": True, "consumo_kw": 0,
                     "descricao": "Aerogeradores externos da colônia"},
        "baterias": {"prioridade": 1, "ativo": True, "consumo_kw": 2,
                     "descricao": "Banco de baterias de armazenamento"},
    },

    "sistema_suporte_vida": {
        # CRÍTICOS: nunca podem ser desligados — comprometem a sobrevivência
        "oxigenio"   : {"prioridade": 1, "ativo": True, "consumo_kw": 15,
                        "descricao": "Geradores e recicladores de oxigênio"},
        "pressao"    : {"prioridade": 1, "ativo": True, "consumo_kw": 10,
                        "descricao": "Controle de pressão interna"},
        "temperatura": {"prioridade": 1, "ativo": True, "consumo_kw": 8,
                        "descricao": "Regulação térmica dos módulos habitacionais"},
    },

    "sistema_habitacional": {
        # Importantes mas gerenciáveis em situação de alerta
        "iluminacao" : {"prioridade": 2, "ativo": True, "consumo_kw": 10,
                        "descricao": "Iluminação geral dos módulos"},
        "agua"       : {"prioridade": 2, "ativo": True, "consumo_kw": 12,
                        "descricao": "Bombeamento e purificação de água"},
        "comunicacao": {"prioridade": 2, "ativo": True, "consumo_kw": 5,
                        "descricao": "Comunicação interna e externa"},
    },

    "sistema_nao_essencial": {
        # Dispensáveis — os primeiros a desligar em emergência
        "entretenimento"      : {"prioridade": 3, "ativo": True, "consumo_kw": 4,
                                 "descricao": "Centros de entretenimento e lazer"},
        "pesquisa_nao_urgente": {"prioridade": 3, "ativo": True, "consumo_kw": 6,
                                 "descricao": "Laboratórios de pesquisa não emergencial"},
    },
}


# SEÇÃO 3 — HISTÓRICOS PARA REGRESSÃO LINEAR (listas paralelas)
#
# Cada dict tem duas listas onde lista_x[i] ↔ lista_y[i] pelo mesmo índice.
# Exemplo: vento_ms[3] = 9 m/s produziu energia_kwh[3] = 22 kW.
#
# Estas listas são usadas por previsao.py para treinar os modelos preditivos.


# Vento (m/s) → energia eólica gerada (kW)
historico_vento = {
    "vento_ms"   : [5,  7,  8,  9,  10, 11, 12, 13, 14, 15],
    "energia_kwh": [10, 15, 18, 22, 25, 27, 30, 33, 36, 38],
}

# Irradiação solar (W/m²) → energia solar gerada (kW)
historico_solar = {
    "irradiacao_wm2": [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
    "energia_kwh"   : [4,   8,   12,  16,  20,  24,  28,  32,  36,  40],
}

# Hora do dia (0–23) → consumo típico da colônia (kW)
# Permite identificar padrões de uso ao longo do dia
historico_consumo_horario = {
    "hora"      : [0,  2,  4,  6,  8,  10, 12, 14, 16, 18, 20, 22],
    "consumo_kw": [30, 25, 22, 28, 50, 65, 70, 68, 65, 72, 60, 45],
}

# SEÇÃO 4 — FUNÇÕES DE ACESSO E ATUALIZAÇÃO
#
# Os outros módulos não leem os dicts diretamente — passam sempre por aqui.
# Isso garante que, se a estrutura interna mudar, só este módulo é afetado.


def obter_estado(chave: str):
    """
    Busca o valor de um sensor pelo nome da chave.
    Retorna None se a chave não existir (sem lançar erro).
    """
    return estado_atual.get(chave, None)


def atualizar_estado(chave: str, valor) -> None:
    """
    Atualiza um sensor no estado atual.
    Avisa se a chave informada não existir no dicionário.
    """
    if chave in estado_atual:
        estado_atual[chave] = valor
    else:
        print(f"  [AVISO] Chave '{chave}' não existe no estado atual.")


def obter_geracao_total() -> float:
    """
    Retorna a geração total combinando solar + eólica (kW).
    Centraliza o cálculo para evitar repetição em outros módulos.
    """
    solar  = estado_atual.get("geracao_solar_kw", 0)
    eolica = estado_atual.get("geracao_eolica_kw", 0)
    return solar + eolica


def listar_subsistemas_por_prioridade(prioridade: int) -> list:
    """
    Percorre a hierarquia e retorna todos os subsistemas com a prioridade dada.
    Retorna lista de tuplas: (nome_sistema, nome_subsistema, dados_subsistema).
    """
    resultado = []
    for sistema, subsistemas in hierarquia_sistemas.items():
        for nome_sub, dados in subsistemas.items():
            if dados["prioridade"] == prioridade:
                resultado.append((sistema, nome_sub, dados))
    return resultado


# SEÇÃO 5 — HELPERS DE LEITURA DO TECLADO
#
# Funções auxiliares reutilizadas por coletar_dados_do_usuario() e previsao.py.
# Encapsulam a validação de entrada para não repetir o try/except em todo lugar.


def ler_numero(mensagem: str, tipo=float, padrao=None):
    """
    Lê um número do teclado com validação de tipo.
    Se o usuário pressionar Enter sem digitar, retorna o valor padrão.
    Fica em loop até receber um valor válido.
    """
    sufixo = f" [{padrao}]: " if padrao is not None else ": "
    while True:
        entrada = input(f"  {mensagem}{sufixo}").strip()

        # Enter sem digitar → usa o padrão
        if entrada == "" and padrao is not None:
            return padrao

        try:
            return tipo(entrada)
        except ValueError:
            print(f"  [!] Valor inválido. Digite um número {tipo.__name__}.")


def ler_opcao(mensagem: str, opcoes: list, padrao: str = None) -> str:
    """
    Lê uma string do teclado e valida se está dentro das opções permitidas.
    Se o usuário pressionar Enter sem digitar, retorna o padrão.
    """
    sufixo = f" {opcoes} [{padrao}]: " if padrao else f" {opcoes}: "
    while True:
        entrada = input(f"  {mensagem}{sufixo}").strip().lower()

        if entrada == "" and padrao is not None:
            return padrao

        if entrada in opcoes:
            return entrada

        print(f"  [!] Opção inválida. Escolha: {opcoes}")


# SEÇÃO 6 — COLETA DE DADOS DO USUÁRIO (modo de teste / modo manual)
#
# Permite ao operador digitar os valores de cada sensor pelo teclado.
# Os valores substituem os padrões acima para o ciclo de análise atual.
# Pressionar Enter em qualquer campo mantém o valor padrão daquele sensor.

def coletar_dados_do_usuario() -> None:
    """
    Lê todos os valores do estado_atual diretamente do teclado.
    Útil para testar cenários sem precisar editar o código.
    """
    print("\n" + "─" * 60)
    print("  ENTRADA MANUAL DE DADOS")
    print("  (pressione Enter para manter o valor entre colchetes)")
    print("─" * 60)

    # ── Grupo: energia ────────────────────────────────────────────────────────
    print("\n  [ENERGIA]")
    atualizar_estado("energia_reserva_kwh",
        ler_numero("Reserva nas baterias (kWh)", float,
                   estado_atual["energia_reserva_kwh"]))

    atualizar_estado("geracao_solar_kw",
        ler_numero("Geração solar atual (kW)", float,
                   estado_atual["geracao_solar_kw"]))

    atualizar_estado("geracao_eolica_kw",
        ler_numero("Geração eólica atual (kW)", float,
                   estado_atual["geracao_eolica_kw"]))

    atualizar_estado("consumo_total_kw",
        ler_numero("Consumo total atual (kW)", float,
                   estado_atual["consumo_total_kw"]))

    # ── Grupo: clima ──────────────────────────────────────────────────────────
    print("\n  [CLIMA]")
    atualizar_estado("velocidade_vento_ms",
        ler_numero("Velocidade do vento (m/s)", float,
                   estado_atual["velocidade_vento_ms"]))

    atualizar_estado("irradiacao_solar_wm2",
        ler_numero("Irradiação solar (W/m²)", float,
                   estado_atual["irradiacao_solar_wm2"]))

    atualizar_estado("temperatura_c",
        ler_numero("Temperatura ambiente (°C)", float,
                   estado_atual["temperatura_c"]))

    atualizar_estado("previsao_clima",
        ler_opcao("Previsão do clima",
                  ["favoravel", "neutro", "adverso"],
                  estado_atual["previsao_clima"]))

    # ── Grupo: ciclo ──────────────────────────────────────────────────────────
    print("\n  [CICLO]")
    atualizar_estado("hora_do_dia",
        ler_numero("Hora do dia (0–23)", int,
                   estado_atual["hora_do_dia"]))

    print("\n  ✔ Dados atualizados com sucesso!\n")


# SEÇÃO 7 — EXIBIÇÃO DA HIERARQUIA (formatação visual)


def exibir_hierarquia() -> None:
    """
    Imprime a hierarquia de sistemas da colônia em formato de árvore.
    Útil para o operador ver o estado de cada subsistema de um relance.
    """
    print("\n" + "=" * 60)
    print("  HIERARQUIA DE SISTEMAS DA COLÔNIA")
    print("=" * 60)

    for sistema, subsistemas in hierarquia_sistemas.items():
        # Formata o nome do sistema para exibição (remove underscores)
        nome_exibido = sistema.replace("_", " ").upper()
        print(f"\n  [{nome_exibido}]")

        for nome_sub, dados in subsistemas.items():
            status = "ON " if dados["ativo"] else "OFF"
            print(
                f"    ├─ {nome_sub:<25} "
                f"P{dados['prioridade']}  "
                f"{dados['consumo_kw']:>4} kW  [{status}]"
            )

    print("=" * 60)
