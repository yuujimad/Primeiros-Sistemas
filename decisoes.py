
# MÓDULO: decisoes.py
# FUNÇÃO : Tomar decisões automatizadas com base nos dados da análise energética.
#
# Como funciona o motor de regras?
#   1. Condições → funções que respondem True/False a uma pergunta simples
#   2. Regras    → combinam condições com AND/OR e retornam uma ação ou None
#   3. Motor     → avalia todas as regras e filtra as que se aplicam
#   4. Ordenação → ordena as ações por urgência (CRÍTICO primeiro)
#
# Lógica booleana composta:
#   AND → todas as condições devem ser verdadeiras (regra mais restrita)
#   OR  → basta UMA condição ser verdadeira (regra mais permissiva)
#   Exemplo: energia_critica AND consumo_alto → emergência mais severa
#            consumo_alto OR ha_deficit     → qualquer um já justifica atenção

from dados_colonia import obter_estado, listar_subsistemas_por_prioridade

# CONFIGURAÇÃO — limiares das regras de decisão
#
# Separados da lógica para facilitar ajuste sem alterar o código das regras.

LIMIAR_ENERGIA_CRITICA  = 20    # % — abaixo disso é emergência imediata
LIMIAR_ENERGIA_BAIXA    = 40    # % — abaixo disso requer atenção
LIMIAR_CONSUMO_ALTO     = 65    # kW — consumo considerado elevado
LIMIAR_VENTO_FAVORAVEL  = 9     # m/s — vento suficiente para boa geração


# SEÇÃO 1 — FUNÇÕES DE CONDIÇÃO (retornam True ou False — perguntas simples)
#
# Cada função avalia UM critério do sistema.
# Combinando-as nas regras (AND/OR), construímos lógica booleana composta.
# Ter funções separadas facilita leitura e teste independente de cada condição.

def energia_critica(pct: float) -> bool:
    """Bateria está abaixo do nível crítico?"""
    return pct <= LIMIAR_ENERGIA_CRITICA


def energia_baixa(pct: float) -> bool:
    """Bateria está entre crítico e baixo (não chegou à emergência máxima)?"""
    return LIMIAR_ENERGIA_CRITICA < pct <= LIMIAR_ENERGIA_BAIXA


def consumo_alto(consumo_kw: float) -> bool:
    """Consumo atual supera o limiar definido?"""
    return consumo_kw >= LIMIAR_CONSUMO_ALTO


def ha_deficit(saldo_kw: float) -> bool:
    """A geração não está cobrindo o consumo (saldo negativo)?"""
    return saldo_kw < 0


def clima_adverso() -> bool:
    """
    O clima previsto é desfavorável para geração renovável?
    Protege contra None caso o sensor de previsão esteja indisponível.
    """
    clima = obter_estado("previsao_clima")
    return clima == "adverso" if clima is not None else False


def vento_favoravel() -> bool:
    """
    O vento está em velocidade boa para geração eólica?
    isinstance() garante que só compara se o sensor retornar um número.
    Sem essa guarda, a comparação >= lançaria TypeError com None.
    """
    vento = obter_estado("velocidade_vento_ms")
    return isinstance(vento, (int, float)) and vento >= LIMIAR_VENTO_FAVORAVEL


# SEÇÃO 2 — REGRAS DE DECISÃO (combinam condições → retornam ação ou None)
#
# Formato do retorno quando a regra se aplica:
#   {
#     "nivel" : "CRITICO" | "ALTO" | "MEDIO" | "INFO",
#     "acao"  : "o que o operador deve fazer",
#     "motivo": "por que esta regra disparou (as condições verdadeiras)"
#   }
#
# Retorna None quando a regra NÃO se aplica ao estado atual.
# O motor filtra os None e trabalha só com as regras ativas.


def regra_emergencia(pct: float, consumo_kw: float, saldo_kw: float):
    """
    NÍVEL CRÍTICO — Situação mais severa possível.

    Condição: bateria crítica AND consumo alto AND clima adverso
    (AND = as três precisam ser verdadeiras ao mesmo tempo)

    Exige ação imediata: desligar tudo que não for essencial.
    """
    if energia_critica(pct) and consumo_alto(consumo_kw) and clima_adverso():
        return {
            "nivel" : "CRITICO",
            "acao"  : "MODO EMERGÊNCIA: desligar sistemas de prioridade 2 e 3 imediatamente.",
            "motivo": (f"Bateria crítica ({pct}%) "
                       f"AND consumo alto ({consumo_kw} kW) AND clima adverso."),
        }
    return None   # regra não se aplica


def regra_deficit_bateria_baixa(pct: float, saldo_kw: float):
    """
    NÍVEL ALTO — Risco real de apagão.

    Condição: há déficit de energia AND bateria está baixa
    (AND = os dois problemas coexistindo aumentam o risco)

    Exige redução de carga e monitoramento frequente.
    """
    if ha_deficit(saldo_kw) and energia_baixa(pct):
        return {
            "nivel" : "ALTO",
            "acao"  : "ALERTA: desligar prioridade 3. Monitorar reserva a cada 15 min.",
            "motivo": f"Déficit de {abs(saldo_kw):.1f} kW AND bateria baixa ({pct}%).",
        }
    return None


def regra_consumo_elevado(consumo_kw: float, saldo_kw: float):
    """
    NÍVEL MÉDIO — Situação de atenção.

    Condição: consumo alto OR há déficit
    (OR = qualquer um dos dois já é motivo de atenção)

    Usar OR torna esta regra mais sensível que as anteriores (AND).
    """
    if consumo_alto(consumo_kw) or ha_deficit(saldo_kw):
        return {
            "nivel" : "MEDIO",
            "acao"  : "ATENÇÃO: reduzir prioridade 3. Verificar escalonamento de cargas.",
            "motivo": (f"Consumo = {consumo_kw} kW (limiar: {LIMIAR_CONSUMO_ALTO}) "
                       f"OR saldo = {saldo_kw:.1f} kW."),
        }
    return None


def regra_armazenar_excedente(saldo_kw: float, pct: float):
    """
    NÍVEL INFO — Oportunidade de armazenamento.

    Condição: saldo positivo (geração > consumo) AND baterias com espaço
    Janela de oportunidade: armazenar agora evita problemas futuros.
    """
    if saldo_kw > 0 and pct < 90:
        return {
            "nivel" : "INFO",
            "acao"  : (f"SUGESTÃO: direcionar {saldo_kw:.1f} kW para baterias. "
                       f"Capacidade disponível: {100 - pct:.1f}%."),
            "motivo": f"Saldo positivo ({saldo_kw:.1f} kW) AND baterias com espaço ({pct}%).",
        }
    return None


def regra_vento_bom():
    """
    NÍVEL INFO — Condição favorável para geração eólica.
    Notifica o operador para aproveitar o bom vento.
    """
    if vento_favoravel():
        vento = obter_estado("velocidade_vento_ms")
        return {
            "nivel" : "INFO",
            "acao"  : f"INFORMAÇÃO: vento a {vento} m/s — condição favorável para eólica.",
            "motivo": f"Vento ({vento} m/s) ≥ limiar favorável ({LIMIAR_VENTO_FAVORAVEL} m/s).",
        }
    return None

# SEÇÃO 3 — MOTOR DE DECISÃO (orquestrador das regras)
#
# Avalia todas as regras em sequência.
# Filtra as que retornaram None (não se aplicam).
# Ordena as ações restantes por urgência: CRÍTICO > ALTO > MÉDIO > INFO.


# Mapa de urgência: menor número = mais urgente
ORDEM_URGENCIA = {"CRITICO": 0, "ALTO": 1, "MEDIO": 2, "INFO": 3}


def executar_motor_de_decisao(analise: dict) -> list:
    """
    Avalia todas as regras com base nos resultados da análise energética.

    Parâmetro:
        analise : dicionário retornado por analise_energia.exibir_relatorio_energia()

    Retorna lista de ações ordenadas da mais urgente para a menos urgente.
    """
    # Extrai as variáveis necessárias do resultado da análise
    pct     = analise["bateria"]["percentual"]   # nível da bateria em %
    consumo = analise["consumo_kw"]              # consumo atual em kW
    saldo   = analise["balanco"]["saldo_kw"]     # saldo (geração − consumo)

    # Avalia cada regra — cada uma retorna dict ou None
    resultados = [
        regra_emergencia(pct, consumo, saldo),
        regra_deficit_bateria_baixa(pct, saldo),
        regra_consumo_elevado(consumo, saldo),
        regra_armazenar_excedente(saldo, pct),
        regra_vento_bom(),
    ]

    # Filtra as que não se aplicaram (None) e ordena por urgência
    acoes = [r for r in resultados if r is not None]
    return sorted(acoes, key=lambda r: ORDEM_URGENCIA[r["nivel"]])


# SEÇÃO 4 — SUGESTÃO DE DESLIGAMENTO DE SISTEMAS
#
# Consulta a hierarquia e lista quais subsistemas podem ser desligados.
# Sistemas de prioridade 1 (suporte à vida) NUNCA são sugeridos.

def sugerir_reducao_de_carga(nivel_corte: int = 3) -> list:
    """
    Retorna subsistemas candidatos ao desligamento para economizar energia.

    Parâmetro:
        nivel_corte : prioridade mínima para desligamento (3 = só não essenciais;
                      2 = também habitacional; nunca abaixo de 2)

    Retorna lista ordenada pelo maior consumo primeiro (maior impacto ao desligar).
    """
    sugestoes = []

    # Percorre as prioridades de nivel_corte até 3 (máximo dispensável)
    for prioridade in range(nivel_corte, 4):
        candidatos = listar_subsistemas_por_prioridade(prioridade)
        for sistema, subsistema, dados in candidatos:
            if dados["ativo"]:   # só sugere sistemas que estão ligados
                sugestoes.append({
                    "sistema"   : sistema,
                    "subsistema": subsistema,
                    "prioridade": prioridade,
                    "consumo_kw": dados["consumo_kw"],
                    "descricao" : dados["descricao"],
                })

    # Ordena pelo maior consumo: desligar o mais pesado primeiro tem mais impacto
    return sorted(sugestoes, key=lambda s: s["consumo_kw"], reverse=True)


# SEÇÃO 5 — RELATÓRIO DE DECISÕES (exibição formatada)

def exibir_relatorio_decisoes(analise: dict) -> None:
    """
    Exibe o relatório completo de decisões automáticas do sistema.

    Parâmetro:
        analise : resultado de analise_energia.exibir_relatorio_energia()
    """
    acoes = executar_motor_de_decisao(analise)

    print("\n" + "=" * 60)
    print("  MÓDULO DE TOMADA DE DECISÃO — MOTOR DE REGRAS")
    print("=" * 60)

    # ── Resumo do estado que serviu de entrada ────────────────────────────────
    clima = obter_estado("previsao_clima") or "N/D"
    print(f"\n  [ENTRADA PROCESSADA]")
    print(f"    Bateria  : {analise['bateria']['percentual']}% ({analise['bateria']['nivel']})")
    print(f"    Consumo  : {analise['consumo_kw']} kW")
    print(f"    Saldo    : {analise['balanco']['saldo_kw']:+.2f} kW")
    print(f"    Situação : {analise['balanco']['situacao']}")
    print(f"    Clima    : {clima.upper()}")

    # ── Ações geradas pelas regras ────────────────────────────────────────────
    print(f"\n  [AÇÕES — {len(acoes)} regra(s) disparada(s)]")
    if not acoes:
        print("    Nenhuma ação necessária. Sistema estável.")
    else:
        for i, acao in enumerate(acoes, 1):
            print(f"\n    [{i}] Nível : {acao['nivel']}")
            print(f"        Motivo: {acao['motivo']}")
            print(f"        Ação  : {acao['acao']}")

    # ── Se situação grave → lista sistemas candidatos ao desligamento ─────────
    if acoes and acoes[0]["nivel"] in ("CRITICO", "ALTO"):
        # Em emergência crítica: desliga até prioridade 2
        # Em alerta alto: desliga apenas prioridade 3
        nivel_corte = 2 if acoes[0]["nivel"] == "CRITICO" else 3
        sugestoes   = sugerir_reducao_de_carga(nivel_corte)
        economia    = sum(s["consumo_kw"] for s in sugestoes)

        print(f"\n  [SISTEMAS PARA DESLIGAR — prioridade ≥ {nivel_corte}]")
        print(f"    Economia potencial: {economia} kW")
        for s in sugestoes:
            print(f"    ├─ {s['subsistema']:<25} "
                  f"P{s['prioridade']}  "
                  f"{s['consumo_kw']:>4} kW  —  {s['descricao']}")

        # Reforça quais sistemas são intocáveis
        print(f"\n  [SISTEMAS PROTEGIDOS — NUNCA DESLIGAR]")
        for _, subsistema, dados in listar_subsistemas_por_prioridade(1):
            if dados["consumo_kw"] > 0:   # ignora geradores (consumo zero)
                print(f"    ✔ {subsistema:<25} {dados['consumo_kw']:>4} kW garantidos")

    print("=" * 60)
