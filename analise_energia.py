
# MÓDULO: analise_energia.py
# FUNÇÃO : Calcular e avaliar o balanço energético da colônia.
#
# Fluxo interno:
#   1. Lê os dados do estado atual (via dados_colonia)
#   2. Calcula balanço (geração − consumo) e nível da bateria
#   3. Gera alertas com base em limiares configuráveis
#   4. Exibe o relatório formatado
#
# Separação clara de responsabilidades:
#   - Funções de CÁLCULO → recebem parâmetros, retornam resultados, sem prints
#   - Função de EXIBIÇÃO → única que chama print(); orquestra os cálculos
# =============================================================================

from dados_colonia import obter_estado, obter_geracao_total


# CONFIGURAÇÃO — limiares (thresholds)
#
# Centralizar os limiares aqui facilita ajuste sem alterar a lógica abaixo.
# Em produção, esses valores viriam de um arquivo de configuração externo.

CAPACIDADE_MAXIMA_BATERIA_KWH = 100   # kWh — capacidade total do banco de baterias

# Limiares da bateria (em % da capacidade máxima)
LIMIAR_CRITICO_PERC   = 20    # abaixo disso → situação crítica
LIMIAR_BAIXO_PERC     = 40    # abaixo disso → atenção necessária
LIMIAR_EXCEDENTE_PERC = 80    # acima disso → baterias quase cheias

# Limiares de balanço (geração − consumo em kW)
LIMIAR_DEFICIT_GRAVE  = -20   # kW — déficit severo (muito consumo, pouca geração)
LIMIAR_EXCEDENTE_UTIL = 15    # kW — excedente que vale a pena armazenar


# FUNÇÕES DE CÁLCULO (puras — sem efeito colateral, sem prints)
#
# "Pura" significa: mesmo input → sempre mesmo output.
# Não leem estado global, não imprimem, não modificam nada externo.
# Isso facilita testes unitários e reuso.


def calcular_balanco(geracao_kw: float, consumo_kw: float) -> dict:
    """
    Calcula o balanço instantâneo entre geração e consumo.

    Classifica a situação em cinco categorias, do mais grave ao melhor:
      CRÍTICO     → déficit grave (geração ≤ consumo − 20 kW)
      DÉFICIT     → consumo ligeiramente maior que geração
      EQUILIBRADO → geração igual ao consumo
      ESTÁVEL     → pequeno superávit
      EXCEDENTE   → superávit ≥ 15 kW (boa oportunidade para armazenar)

    Parâmetros:
        geracao_kw : total gerado agora (solar + eólica)
        consumo_kw : total consumido agora pela colônia

    Retorna dict com saldo, cobertura percentual e classificação.
    """
    # Saldo = quanto sobra ou falta de energia
    saldo = geracao_kw - consumo_kw

    # Cobertura: % do consumo que a geração está atendendo
    # Guard de divisão por zero: se não há consumo, considera 100% coberto
    cobertura = (geracao_kw / consumo_kw * 100) if consumo_kw > 0 else 100.0

    # Classificação por limiar — verifica do mais grave para o mais favorável
    if saldo <= LIMIAR_DEFICIT_GRAVE:
        situacao = "CRÍTICO"
    elif saldo < 0:
        situacao = "DÉFICIT"
    elif saldo == 0:
        situacao = "EQUILIBRADO"
    elif saldo >= LIMIAR_EXCEDENTE_UTIL:
        situacao = "EXCEDENTE"
    else:
        situacao = "ESTÁVEL"

    return {
        "saldo_kw"      : round(saldo, 2),
        "cobertura_perc": round(cobertura, 1),
        "situacao"      : situacao,
    }


def calcular_nivel_bateria(reserva_kwh: float, consumo_kw: float = None) -> dict:
    """
    Analisa o nível atual da reserva de energia nas baterias.

    Parâmetros:
        reserva_kwh : energia armazenada agora (kWh)
        consumo_kw  : consumo atual (kW); se None, lê do estado global

    Retorna dict com percentual, classificação e autonomia estimada (horas).

    Autonomia = reserva ÷ consumo → quantas horas a bateria dura sozinha.
    """
    # Usa consumo do estado atual se não for informado diretamente
    if consumo_kw is None:
        consumo_kw = obter_estado("consumo_total_kw") or 0

    # Percentual em relação à capacidade total
    percentual = (reserva_kwh / CAPACIDADE_MAXIMA_BATERIA_KWH) * 100

    # Classificação por limiar
    if percentual <= LIMIAR_CRITICO_PERC:
        nivel = "CRÍTICO"
    elif percentual <= LIMIAR_BAIXO_PERC:
        nivel = "BAIXO"
    elif percentual <= LIMIAR_EXCEDENTE_PERC:
        nivel = "NORMAL"
    else:
        nivel = "ALTO"

    # Autonomia: evita divisão por zero se o consumo for zero
    autonomia = (reserva_kwh / consumo_kw) if consumo_kw > 0 else float("inf")

    return {
        "percentual" : round(percentual, 1),
        "nivel"      : nivel,
        "autonomia_h": round(autonomia, 2),
    }


def identificar_alertas(balanco: dict, bateria: dict) -> list:
    """
    Gera alertas e sugestões com base nos resultados de balanço e bateria.

    Parâmetros:
        balanco : resultado de calcular_balanco()
        bateria : resultado de calcular_nivel_bateria()

    Retorna lista de strings — cada string é uma mensagem para o operador.
    Se não houver nenhum problema, retorna uma mensagem de sistema normal.
    """
    msgs = []

    # ── Alertas de balanço ────────────────────────────────────────────────────
    if balanco["situacao"] == "CRÍTICO":
        msgs.append("⚠ ALERTA CRÍTICO: consumo muito maior que geração. "
                    "Desligar sistemas não essenciais imediatamente!")
    elif balanco["situacao"] == "DÉFICIT":
        msgs.append("⚠ ALERTA: consumo maior que geração. "
                    "Reduzir carga ou acionar reserva.")
    elif balanco["situacao"] == "EXCEDENTE":
        msgs.append("✔ SUGESTÃO: geração excede consumo. "
                    "Armazenar energia excedente nas baterias.")

    # ── Alertas de bateria ────────────────────────────────────────────────────
    if bateria["nivel"] == "CRÍTICO":
        msgs.append(f"⚠ ALERTA CRÍTICO: bateria em {bateria['percentual']}%. "
                    f"Autonomia estimada: {bateria['autonomia_h']}h. Ação urgente!")
    elif bateria["nivel"] == "BAIXO":
        msgs.append(f"⚠ ATENÇÃO: bateria em {bateria['percentual']}%. "
                    f"Autonomia estimada: {bateria['autonomia_h']}h.")
    elif bateria["nivel"] == "ALTO":
        msgs.append("✔ SUGESTÃO: baterias acima de 80%. "
                    "Considere reduzir geração ou distribuir energia.")

    # ── Alerta de cobertura insuficiente ─────────────────────────────────────
    if balanco["cobertura_perc"] < 70:
        msgs.append(f"⚠ ATENÇÃO: apenas {balanco['cobertura_perc']}% "
                    "do consumo está sendo coberto pela geração atual.")

    # Se nenhuma condição adversa foi encontrada
    if not msgs:
        msgs.append("✔ Sistema energético operando em condições normais.")

    return msgs


# FUNÇÃO DE EXIBIÇÃO — única com prints; orquestra as funções de cálculo

def exibir_relatorio_energia() -> dict:
    """
    Executa a análise energética completa e exibe o relatório formatado.

    Retorna o dicionário com todos os resultados calculados.
    Esse dict é passado adiante para o módulo de decisões (decisoes.py).
    """
    # ── Leitura dos dados do estado atual ────────────────────────────────────
    geracao = obter_geracao_total()                       # solar + eólica (kW)
    consumo = obter_estado("consumo_total_kw") or 0      # proteção contra None
    reserva = obter_estado("energia_reserva_kwh") or 0   # proteção contra None

    # ── Cálculos ──────────────────────────────────────────────────────────────
    balanco = calcular_balanco(geracao, consumo)
    bateria = calcular_nivel_bateria(reserva, consumo)
    alertas = identificar_alertas(balanco, bateria)

    # ── Exibição do relatório ─────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  MÓDULO DE ANÁLISE DE ENERGIA")
    print("=" * 60)

    print(f"\n  [GERAÇÃO ATUAL]")
    print(f"    Solar              : {obter_estado('geracao_solar_kw')} kW")
    print(f"    Eólica             : {obter_estado('geracao_eolica_kw')} kW")
    print(f"    Total gerado       : {geracao} kW")

    print(f"\n  [CONSUMO E BALANÇO]")
    print(f"    Consumo total      : {consumo} kW")
    print(f"    Saldo              : {balanco['saldo_kw']:+.2f} kW")
    print(f"    Cobertura          : {balanco['cobertura_perc']}%")
    print(f"    Situação           : {balanco['situacao']}")

    print(f"\n  [RESERVA DE ENERGIA]")
    print(f"    Reserva atual      : {reserva} kWh")
    print(f"    Capacidade máxima  : {CAPACIDADE_MAXIMA_BATERIA_KWH} kWh")
    print(f"    Nível              : {bateria['percentual']}% ({bateria['nivel']})")
    print(f"    Autonomia estimada : {bateria['autonomia_h']} horas")

    print(f"\n  [ALERTAS E SUGESTÕES]")
    for msg in alertas:
        print(f"    {msg}")

    print("=" * 60)

    # ── Retorno para o motor de decisão ───────────────────────────────────────
    # Devolver um dict estruturado permite que decisoes.py use os resultados
    # sem precisar recalcular ou reler os sensores.
    return {
        "geracao_total_kw": geracao,
        "consumo_kw"      : consumo,
        "balanco"         : balanco,
        "bateria"         : bateria,
        "alertas"         : alertas,
    }
