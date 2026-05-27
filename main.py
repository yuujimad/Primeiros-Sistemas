
# ARQUIVO: main.py
# FUNÇÃO : Ponto de entrada e orquestrador do sistema da colônia espacial.
#
# Arquitetura em camadas (fluxo de dados de cima para baixo):
#
#   dados_colonia.py   → guarda e fornece dados (sensores, hierarquia, histórico)
#          ↓
#   analise_energia.py → calcula balanço, nível de bateria, gera alertas
#          ↓
#   previsao.py        → estima geração e consumo futuros (regressão linear)
#          ↓
#   decisoes.py        → avalia regras booleanas e gera ações automáticas
#          ↓
#   main.py            → orquestra tudo e apresenta o resultado ao operador
#
# Modos de operação disponíveis:
#   1. Automático     → usa os dados padrão definidos em dados_colonia.py
#   2. Manual         → operador digita todos os valores pelo teclado (para testes)
#   3. Cenário demo   → três cenários predefinidos para demonstração e validação


# Importa cada módulo com apelido para deixar claro a origem de cada função
import dados_colonia as dc
from analise_energia import exibir_relatorio_energia
from previsao        import exibir_relatorio_previsao, coletar_entrada_previsao_usuario
from decisoes        import exibir_relatorio_decisoes


# CICLO DE ANÁLISE COMPLETO
#
# Sequência de 4 etapas que compõem um ciclo de gerenciamento da colônia.
# Sempre executado com os dados que estiverem em dados_colonia.estado_atual
# no momento da chamada.

def executar_ciclo(titulo: str = "CICLO DE ANÁLISE") -> None:
    """
    Executa as 4 etapas de análise com os dados atuais da colônia.

    Etapa 1 → mostra o estado atual e a hierarquia dos sistemas
    Etapa 2 → análise energética (balanço, bateria, alertas)
    Etapa 3 → previsão por regressão linear (eólica, solar, consumo)
    Etapa 4 → motor de decisão (regras booleanas → ações)
    """
    print("\n" + "#" * 60)
    print(f"#  {titulo:<56}#")
    print("#" * 60)

    # ── ETAPA 1: estado atual e hierarquia ────────────────────────────────────
    print("\n>>> ETAPA 1: ESTADO ATUAL DA COLÔNIA")
    _exibir_sensores()          # mostra os valores dos sensores
    dc.exibir_hierarquia()      # mostra a árvore de sistemas

    # ── ETAPA 2: análise energética ───────────────────────────────────────────
    print("\n>>> ETAPA 2: ANÁLISE DE ENERGIA")
    # O resultado é guardado porque a etapa 4 (decisões) depende dele
    resultado_analise = exibir_relatorio_energia()

    # ── ETAPA 3: previsão ─────────────────────────────────────────────────────
    print("\n>>> ETAPA 3: PREVISÃO POR REGRESSÃO LINEAR")

    if dc.MODO_MANUAL:
        # Em modo manual, pergunta ao usuário os valores de entrada da previsão
        # (separado da coleta do estado, pois pode ser diferente do sensor atual)
        vento, irrad, hora = coletar_entrada_previsao_usuario()
    else:
        # Em modo automático, lê diretamente do estado atual
        vento = dc.obter_estado("velocidade_vento_ms")
        irrad = dc.obter_estado("irradiacao_solar_wm2")
        hora  = dc.obter_estado("hora_do_dia")

    exibir_relatorio_previsao(vento, irrad, hora)

    # ── ETAPA 4: motor de decisão ─────────────────────────────────────────────
    print("\n>>> ETAPA 4: TOMADA DE DECISÃO AUTOMÁTICA")
    # Recebe o resultado da análise — não relê os sensores diretamente
    exibir_relatorio_decisoes(resultado_analise)

    print("\n" + "#" * 60)
    print("#  FIM DO CICLO                                          #")
    print("#" * 60 + "\n")


def _exibir_sensores() -> None:
    """Mostra os valores atuais de todos os sensores da colônia."""
    campos = [
        ("energia_reserva_kwh",  "Reserva energia (kWh)"),
        ("geracao_solar_kw",     "Geração solar (kW)"),
        ("geracao_eolica_kw",    "Geração eólica (kW)"),
        ("consumo_total_kw",     "Consumo total (kW)"),
        ("velocidade_vento_ms",  "Vento (m/s)"),
        ("irradiacao_solar_wm2", "Irradiação (W/m²)"),
        ("temperatura_c",        "Temperatura (°C)"),
        ("previsao_clima",       "Previsão clima"),
        ("hora_do_dia",          "Hora atual"),
    ]
    print("\n  [SENSORES — ESTADO ATUAL]")
    for chave, rotulo in campos:
        print(f"    {rotulo:<25}: {dc.obter_estado(chave)}")



# CENÁRIOS PREDEFINIDOS
#
# Cada cenário define um conjunto de valores de sensores para demonstração.
# Isso permite testar o sistema em situações extremas sem editar o código.


# Dict de cenários: chave → {nome para exibição, dados dos sensores}
CENARIOS = {

    "favoravel": {
        "nome": "CONDIÇÕES FAVORÁVEIS — excedente de energia",
        "dados": {
            "energia_reserva_kwh" : 85,
            "geracao_solar_kw"    : 50,
            "geracao_eolica_kw"   : 35,
            "consumo_total_kw"    : 40,
            "velocidade_vento_ms" : 14,
            "irradiacao_solar_wm2": 900,
            "previsao_clima"      : "favoravel",
            "hora_do_dia"         : 10,
        },
    },

    "crise": {
        "nome": "CRISE ENERGÉTICA — baterias a 15%, quase sem geração",
        "dados": {
            "energia_reserva_kwh" : 15,
            "geracao_solar_kw"    : 5,
            "geracao_eolica_kw"   : 3,
            "consumo_total_kw"    : 75,
            "velocidade_vento_ms" : 4,
            "irradiacao_solar_wm2": 80,
            "previsao_clima"      : "adverso",
            "hora_do_dia"         : 2,
        },
    },
}


def executar_cenario(chave: str) -> None:
    """
    Aplica os dados de um cenário predefinido e executa o ciclo completo.

    Parâmetro:
        chave : chave do dicionário CENARIOS ("favoravel" ou "crise")
    """
    cenario = CENARIOS[chave]

    # Atualiza o estado com os dados do cenário (simula novos dados de sensores)
    for k, v in cenario["dados"].items():
        dc.atualizar_estado(k, v)

    dc.MODO_MANUAL = False   # cenários sempre usam os dados diretamente
    executar_ciclo(cenario["nome"])


# MENU INTERATIVO
#
# Apresenta as opções ao operador e processa a escolha em loop
# até que o usuário escolha sair.


def _mostrar_menu() -> str:
    """Exibe o menu e retorna a opção digitada pelo usuário."""
    print("\n" + "═" * 60)
    print("  SISTEMA DE GERENCIAMENTO — COLÔNIA ESPACIAL")
    print("═" * 60)
    print("  1. Modo automático   (usa dados padrão de dados_colonia.py)")
    print("  2. Modo manual       (você digita os valores — ideal para testes)")
    print("  3. Cenário: condições favoráveis")
    print("  4. Cenário: crise energética")
    print("  5. Executar TODOS os cenários em sequência")
    print("  0. Sair")
    print("─" * 60)
    return input("  Escolha uma opção: ").strip()


def executar_menu() -> None:
    """
    Loop principal do menu interativo.
    Continua até o usuário escolher a opção 0 (sair).
    """
    while True:
        opcao = _mostrar_menu()

        if opcao == "1":
            # Modo automático: usa os dados de dados_colonia.py sem pedir input
            dc.MODO_MANUAL = False
            executar_ciclo("MODO AUTOMÁTICO — DADOS PADRÃO")

        elif opcao == "2":
            # Modo manual: solicita cada valor ao operador antes de analisar
            dc.MODO_MANUAL = True
            dc.coletar_dados_do_usuario()          # coleta o estado completo
            executar_ciclo("MODO MANUAL — DADOS INSERIDOS PELO USUÁRIO")
            dc.MODO_MANUAL = False                 # restaura o modo padrão

        elif opcao == "3":
            executar_cenario("favoravel")

        elif opcao == "4":
            executar_cenario("crise")

        elif opcao == "5":
            # Roda os três contextos em sequência para comparação
            dc.MODO_MANUAL = False
            print("\n  >> Executando TODOS os cenários em sequência...")
            executar_ciclo("CENÁRIO PADRÃO (dados de dados_colonia.py)")
            executar_cenario("favoravel")
            executar_cenario("crise")

        elif opcao == "0":
            print("\n  Sistema encerrado. Até logo!\n")
            break

        else:
            print("\n  [!] Opção inválida. Digite um número entre 0 e 5.")

# PONTO DE ENTRADA DO PROGRAMA

if __name__ == "__main__":
    executar_menu()
