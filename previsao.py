
# MÓDULO: previsao.py
# FUNÇÃO : Gerar estimativas futuras usando regressão linear simples.
#
# O que é regressão linear?
#   Dado um conjunto de pares (x, y), encontrar a reta y = a·x + b
#   que melhor representa a relação entre as duas variáveis.
#
# Fórmulas (Mínimos Quadrados Ordinários — OLS):
#   n   = número de pontos de dados
#   a   = (n·Σxy − Σx·Σy) / (n·Σx² − (Σx)²)   ← inclinação da reta
#   b   = (Σy − a·Σx) / n                        ← ponto onde a reta cruza y
#   ŷ   = a·x + b                                ← previsão para novo x
#   R²  = 1 − SS_res / SS_tot                    ← qualidade do ajuste (0–1)
#
# Seções:
#   1. Motor de regressão (matemática pura)
#   2. Treinamento dos modelos com dados históricos
#   3. Funções de previsão específicas
#   4. Entrada manual para teste
#   5. Relatório de previsão

from dados_colonia import (
    historico_vento,
    historico_solar,
    historico_consumo_horario,
    obter_estado,
    ler_numero,      # helper de leitura de teclado (reutilizado daqui)
)


# SEÇÃO 1 — MOTOR DE REGRESSÃO LINEAR (matemática pura)
#
# Recebe qualquer par de listas e calcula os coeficientes da reta de ajuste.
# Genérico: funciona para vento→energia, hora→consumo, ou qualquer par x/y.

def calcular_regressao(lista_x: list, lista_y: list) -> dict:
    """
    Calcula os coeficientes a e b da reta de regressão linear simples.

    Parâmetros:
        lista_x : variável independente (ex.: vento, irradiação, hora)
        lista_y : variável dependente   (ex.: energia gerada, consumo)

    Retorna dict com:
        "a"  → inclinação (quanto y muda por unidade de x)
        "b"  → intercepto (valor de y quando x = 0)
        "r2" → coeficiente de determinação (0 = ajuste ruim, 1 = perfeito)
    """
    n = len(lista_x)

    # Validação básica dos dados de entrada
    if n != len(lista_y) or n < 2:
        raise ValueError("As listas precisam ter o mesmo tamanho e ao menos 2 pontos.")

    # ── Somatórios necessários para o método OLS ───────────────────────────
    soma_x  = sum(lista_x)
    soma_y  = sum(lista_y)
    soma_xy = sum(x * y for x, y in zip(lista_x, lista_y))   # Σ(x·y)
    soma_x2 = sum(x ** 2 for x in lista_x)                   # Σ(x²)

    # Denominador — mede a variação total de x entre os pontos
    denominador = n * soma_x2 - soma_x ** 2

    # Proteção: se todos os x forem iguais, não há como traçar uma reta
    if denominador == 0:
        raise ValueError("Sem variação em x: impossível calcular regressão.")

    # ── Cálculo dos coeficientes ───────────────────────────────────────────
    a = (n * soma_xy - soma_x * soma_y) / denominador   # inclinação
    b = (soma_y - a * soma_x) / n                        # intercepto

    # ── R²: qualidade do ajuste ────────────────────────────────────────────
    # SS_tot = variação total dos dados ao redor da média
    # SS_res = variação que a reta NÃO conseguiu explicar (resíduos)
    # R² = 1 - SS_res/SS_tot → quanto mais perto de 1, melhor o ajuste
    media_y = soma_y / n
    ss_tot  = sum((y - media_y) ** 2 for y in lista_y)
    ss_res  = sum((y - (a * x + b)) ** 2 for x, y in zip(lista_x, lista_y))
    r2      = 1 - (ss_res / ss_tot) if ss_tot != 0 else 1.0

    return {"a": a, "b": b, "r2": r2}


def prever(coeficientes: dict, x_novo: float) -> float:
    """
    Aplica a reta ajustada: ŷ = a·x + b.

    Parâmetros:
        coeficientes : dict retornado por calcular_regressao()
        x_novo       : novo valor de x para o qual queremos estimar y

    Retorna a estimativa de y (pode ser negativa — o chamador trata isso).
    """
    return coeficientes["a"] * x_novo + coeficientes["b"]

# SEÇÃO 2 — TREINAMENTO DOS MODELOS
#
# Os modelos são treinados UMA vez ao importar este módulo e reutilizados.
# Padrão "fit once, predict many" — evita recalcular a regressão a cada uso.
# As variáveis com _ no início são internas deste módulo.


# Modelo: vento (m/s) → energia eólica gerada (kW)
_modelo_eolico = calcular_regressao(
    historico_vento["vento_ms"],
    historico_vento["energia_kwh"]
)

# Modelo: irradiação (W/m²) → energia solar gerada (kW)
_modelo_solar = calcular_regressao(
    historico_solar["irradiacao_wm2"],
    historico_solar["energia_kwh"]
)

# Modelo: hora do dia (0–23) → consumo típico da colônia (kW)
_modelo_consumo_horario = calcular_regressao(
    historico_consumo_horario["hora"],
    historico_consumo_horario["consumo_kw"]
)

# SEÇÃO 3 — FUNÇÕES DE PREVISÃO ESPECÍFICAS
#
# Cada função usa um modelo treinado e garante resultado ≥ 0
# (energia negativa é fisicamente impossível).


def prever_geracao_eolica(vento_ms: float) -> dict:
    """
    Estima a geração eólica (kW) para uma velocidade de vento em m/s.
    Usa o modelo treinado com historico_vento.
    """
    estimativa = max(0.0, prever(_modelo_eolico, vento_ms))   # garante ≥ 0

    return {
        "entrada_vento_ms": vento_ms,
        "estimativa_kw"   : round(estimativa, 2),
        "qualidade_r2"    : round(_modelo_eolico["r2"], 4),
        "formula"         : (f"Energia = {_modelo_eolico['a']:.3f} "
                             f"× vento + {_modelo_eolico['b']:.3f}"),
    }


def prever_geracao_solar(irradiacao_wm2: float) -> dict:
    """
    Estima a geração solar (kW) para uma irradiação em W/m².
    Usa o modelo treinado com historico_solar.
    """
    estimativa = max(0.0, prever(_modelo_solar, irradiacao_wm2))   # garante ≥ 0

    return {
        "entrada_irradiacao_wm2": irradiacao_wm2,
        "estimativa_kw"         : round(estimativa, 2),
        "qualidade_r2"          : round(_modelo_solar["r2"], 4),
        "formula"               : (f"Energia = {_modelo_solar['a']:.4f} "
                                   f"× irradiação + {_modelo_solar['b']:.3f}"),
    }


def prever_consumo_na_hora(hora: int) -> dict:
    """
    Estima o consumo típico da colônia (kW) para uma hora do dia (0–23).
    Usa o modelo treinado com historico_consumo_horario.
    """
    if not (0 <= hora <= 23):
        raise ValueError("Hora deve estar entre 0 e 23.")

    estimativa = max(0.0, prever(_modelo_consumo_horario, hora))   # garante ≥ 0

    return {
        "entrada_hora"         : hora,
        "estimativa_consumo_kw": round(estimativa, 2),
        "qualidade_r2"         : round(_modelo_consumo_horario["r2"], 4),
    }

# SEÇÃO 4 — ENTRADA MANUAL PARA TESTE (modo interativo)
#
# Permite ao operador digitar os valores de entrada das previsões pelo teclado,
# sem depender dos sensores do estado_atual. Os defaults vêm do estado atual.

def coletar_entrada_previsao_usuario() -> tuple:
    """
    Lê do teclado os valores de entrada para gerar as previsões.
    Os valores padrão são lidos do estado atual da colônia.

    Retorna tupla (vento_ms, irradiacao_wm2, hora).
    """
    print("\n  [ENTRADA MANUAL — VALORES PARA PREVISÃO]")
    print("  (pressione Enter para usar o valor atual do sensor)")

    vento      = ler_numero(
        "Velocidade do vento (m/s)", float,
        obter_estado("velocidade_vento_ms")
    )
    irradiacao = ler_numero(
        "Irradiação solar (W/m²)", float,
        obter_estado("irradiacao_solar_wm2")
    )
    hora       = ler_numero(
        "Hora do dia (0–23)", int,
        obter_estado("hora_do_dia")
    )

    return vento, irradiacao, hora


# SEÇÃO 5 — RELATÓRIO DE PREVISÃO (exibição formatada)
# Consolida as três previsões e mostra o saldo previsto para o operador.


def exibir_relatorio_previsao(vento_ms: float, irradiacao_wm2: float, hora: int) -> None:
    """
    Gera e exibe as previsões de geração eólica, solar e consumo esperado.

    Parâmetros:
        vento_ms       : velocidade do vento a usar na previsão (m/s)
        irradiacao_wm2 : irradiação solar a usar na previsão (W/m²)
        hora           : hora do dia a usar na previsão (0–23)
    """
    # Gera as três previsões usando os modelos treinados
    eolica  = prever_geracao_eolica(vento_ms)
    solar   = prever_geracao_solar(irradiacao_wm2)
    consumo = prever_consumo_na_hora(hora)

    print("\n" + "=" * 60)
    print("  MÓDULO DE PREVISÃO — REGRESSÃO LINEAR SIMPLES")
    print("=" * 60)

    print(f"\n  [EÓLICA]")
    print(f"    Entrada  : {vento_ms} m/s")
    print(f"    Previsão : {eolica['estimativa_kw']} kW estimados")
    print(f"    Fórmula  : {eolica['formula']}")
    print(f"    R²       : {eolica['qualidade_r2']}  (1.0 = ajuste perfeito)")

    print(f"\n  [SOLAR]")
    print(f"    Entrada  : {irradiacao_wm2} W/m²")
    print(f"    Previsão : {solar['estimativa_kw']} kW estimados")
    print(f"    Fórmula  : {solar['formula']}")
    print(f"    R²       : {solar['qualidade_r2']}")

    print(f"\n  [CONSUMO ESPERADO]")
    print(f"    Hora     : {hora:02d}h00")
    print(f"    Previsão : {consumo['estimativa_consumo_kw']} kW de consumo típico")
    print(f"    R²       : {consumo['qualidade_r2']}")

    # ── Saldo previsto: soma das gerações − consumo esperado ──────────────────
    geracao_prevista = eolica["estimativa_kw"] + solar["estimativa_kw"]
    saldo            = geracao_prevista - consumo["estimativa_consumo_kw"]
    sinal            = "+" if saldo >= 0 else ""
    rotulo           = "superávit" if saldo >= 0 else "DÉFICIT"

    print(f"\n  [SALDO PREVISTO]")
    print(f"    Geração prevista  : {geracao_prevista:.2f} kW")
    print(f"    Consumo previsto  : {consumo['estimativa_consumo_kw']} kW")
    print(f"    Saldo             : {sinal}{saldo:.2f} kW ({rotulo})")
    print("=" * 60)
