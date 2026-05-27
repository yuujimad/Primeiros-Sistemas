# Sistema Integrado de Gerenciamento da Colônia
## Visão Geral
- Este projeto é um simulador de gerenciamento de recursos. 

- O sistema monitora sensores em tempo real, analisa o balanço energético (geração vs consumo), prevê o comportamento futuro do clima e do consumo usando modelos matemáticos, e toma decisões automatizadas para garantir a sobrevivência da colônia, priorizando sistemas de suporte à vida em casos de emergência.

- A arquitetura foi desenhada com base no princípio de Responsabilidade Única, onde cada módulo faz apenas uma coisa, garantindo um código limpo, modular e de fácil manutenção.

## O Que o Sistema é Capaz de Fazer?

- Monitoramento em Tempo Real: Lê e armazena dados de sensores simulados (geração solar/eólica, consumo, vento, irradiação, temperatura).

- Análise de Balanço Energético: Calcula em tempo real se a colônia está operando em superávit (excedente) ou déficit de energia, estimando a autonomia das baterias.

- Previsão por Machine Learning (Regressão Linear): Sem depender de bibliotecas externas, o sistema calcula os coeficientes de regressão linear (Mínimos Quadrados Ordinários) com base em dados históricos para prever a geração eólica, solar e o consumo horário.

- Tomada de Decisão Automatizada: Um motor de regras avalia o cenário combinando lógica booleana (energia crítica AND consumo alto AND previsão adversa) para gerar planos de ação.

- Gerenciamento Inteligente de Carga (Load Shedding): Em caso de crise energética, o sistema identifica e sugere o desligamento de subsistemas não essenciais (ex: entretenimento, iluminação) para proteger módulos críticos (oxigênio, pressão, temperatura).

## Como o Sistema Funciona

O funcionamento do sistema é baseado em um ciclo de processamento linear, orquestrado pelo main.py, que simula o monitoramento contínuo da colônia. 
O ciclo segue quatro etapas rigorosas:

1. Coleta de Dados: O sistema lê o estado atual dos sensores simulados (nível da bateria, força do vento, consumo instantâneo, etc.).

2. Diagnóstico Energético: Calcula-se a diferença matemática entre o que está sendo gerado e o que está sendo consumido. O sistema avalia se a bateria está subindo, descendo, e quanto tempo de autonomia resta.

3. Previsão Inteligente: Os dados de entrada são passados pelos modelos matemáticos de Regressão Linear. O sistema tenta adivinhar o comportamento futuro: "Com o vento atual, quanto vamos gerar?" ou "Considerando a hora atual, qual será o pico de consumo?".

4. Tomada de Ação: O motor de regras cruza todos esses diagnósticos. Se a bateria estiver abaixo de 20% e o consumo estiver acima de 65 kW, o sistema não apenas emite um alerta, mas varre a árvore de prioridades e sugere o corte de energia de setores específicos (como módulos de lazer) para salvar os sistemas de suporte à vida (oxigênio e pressão).

## Arquitetura e Módulos do Sistema

1. Arquivo -> dados_colonia.py

Este é o "banco de dados" do sistema. Ele não toma decisões, apenas organiza e fornece acesso às informações.

- Armazena o estado atual dos sensores via estrutura de chave-valor.

- Define a hierarquia da colônia (sistemas críticos de prioridade 1 até dispensáveis de prioridade 3).

- Guarda o histórico de dados (vento, irradiação, consumo) para alimentar o módulo de previsão.

- Aplica o princípio do encapsulamento, fornecendo funções como obter_estado() para que os outros módulos leiam os dados com segurança.

2. Arquivo -> analise_energia.py

Responsável por comparar a geração atual com a demanda e o nível das baterias.

- Calcula o saldo energético atual (positivo ou negativo) e o percentual de cobertura do consumo.

- Avalia a saúde da reserva de energia, classificando a situação das baterias (crítico, baixo, normal, alto) e estimando horas de autonomia.

- Utiliza funções puras para os cálculos lógicos, separando-os da formatação visual dos relatórios.

3. Arquivo -> previsao.py

Estima o cenário futuro para embasar decisões.

- Implementa o algoritmo de Regressão Linear Simples do zero (método OLS).

- Aplica o padrão Fit Once, Predict Many: treina os modelos na inicialização usando o histórico de dados_colonia.py e armazena os coeficientes da reta.

- Fornece estimativas cruzando os dados atuais (vento atual, hora atual) com o modelo treinado, entregando previsões com métrica de confiabilidade (R²).

4. Arquivo -> decisoes.py

Recebe os diagnósticos e decide o que deve ser feito.

- Usa funções booleanas isoladas para avaliar critérios simples (ex: energia_esta_critica(), consumo_esta_alto()).

- Combina essas condições com operadores lógicos (AND / OR) para disparar regras complexas, como o protocolo de emergência.

- Classifica as ações por nível de urgência (CRÍTICO, ALTO, MÉDIO, INFO).

- Se necessário, percorre a hierarquia de sistemas e lista exatamente quais subsistemas devem ser desligados (e o quanto isso economizará em kW), poupando sempre a prioridade 1.

5. Arquivo -> main.py

O ponto de entrada do programa. Ele não possui lógica de negócio complexa, atuando como um maestro que chama os outros módulos na ordem correta.

- Executa o Ciclo de Análise: Lê dados -> Analisa energia -> Faz previsões -> Toma decisões.

- Contém uma função executar_cenario() que permite simular diferentes realidades no ambiente (mudança de clima, crises, falhas ou bonança), injetando novos dados nos sensores e reavaliando toda a cadeia de sobrevivência.

# Exemplo Prático: Entrada e Saída

Para ilustrar o funcionamento, vamos analisar um cenário de Crise Energética simulado pelo sistema.

## A Entrada (Dados dos Sensores)

O sistema recebe uma atualização abrupta no estado da colônia, indicando uma tempestade que bloqueia o sol e reduz os ventos, combinada com baterias quase vazias:


    "energia_reserva_kwh": 15,       # Bateria crítica (15% da capacidade)

    "geracao_solar_kw": 5,           # Geração muito baixa

    "geracao_eolica_kw": 3,          # Quase sem vento
    
    "consumo_total_kw": 75,          # Consumo altíssimo

    "previsao_clima": "adverso"      # Clima ruim


## A Saída (Processamento e Decisão)

Após rodar o ciclo de análise, o terminal exibirá um relatório completo detalhando a crise e as ações mitigadoras. 

O resultado gerado pelo motor será semelhante a este:


  Módulo de tomada de decisão


  [Entrada processasda]

    Reserva      : 15.0% (CRÍTICO)

    Consumo      : 75 kW

    Saldo        : -67.00 kW

    Situação     : CRÍTICO

    Previsão     : ADVERSO

  [Ações geradas - 2 regra(s) disparada(s)]

    [1] Nível: CRITICO
        Motivo : Energia crítica (15.0%) AND consumo alto (75 kW) AND previsão adversa.
        Ação   : MODO EMERGÊNCIA: desligar todos os sistemas de prioridade 2 e 3 imediatamente.

    [2] Nível: ALTO
        Motivo : Déficit de 67.0 kW AND bateria baixa (15.0%).
        Ação   : ALERTA: reduzir consumo. Desligar sistemas de prioridade 3. Monitorar reserva a cada 15 minutos.

  [Sistemas sugeridos para desligamento]

    (prioridade ≥ 2 — economia potencial: 37 kW)

    ├─ agua                      P2    12 kW  —  Bombeamento e purificação de água

    ├─ iluminacao                P2    10 kW  —  Iluminação geral dos módulos

    ├─ comunicacao               P2     5 kW  —  Sistemas de comunicação interna e externa


  [Sistemas protegidos - Nunca desligar]

    oxigenio                  15 kW mantidos

    pressao                   10 kW mantidos

    temperatura                8 kW mantidos