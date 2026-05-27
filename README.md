# Sistema Integrado de Gerenciamento — Colônia Espacial
## Visão Geral
- Este projeto é um simulador de gerenciamento de recursos para uma colônia espacial. 

- O sistema monitora sensores em tempo real, analisa o balanço energético (geração vs consumo), prevê o comportamento futuro do clima e do consumo usando modelos matemáticos, e toma decisões automatizadas para garantir a sobrevivência da colônia, priorizando sistemas de suporte à vida em casos de emergência.

- A arquitetura foi desenhada com base no princípio de Responsabilidade Única, onde cada módulo faz apenas uma coisa, garantindo um código limpo, modular e de fácil manutenção.

## O Que o Sistema é Capaz de Fazer?

- Monitoramento em Tempo Real: Lê e armazena dados de sensores simulados (geração solar/eólica, consumo, vento, irradiação, temperatura).

- Análise de Balanço Energético: Calcula em tempo real se a colônia está operando em superávit (excedente) ou déficit de energia, estimando a autonomia das baterias.

- Previsão por Machine Learning (Regressão Linear): Sem depender de bibliotecas externas, o sistema calcula os coeficientes de regressão linear (Mínimos Quadrados Ordinários) com base em dados históricos para prever a geração eólica, solar e o consumo horário.

- Tomada de Decisão Automatizada: Um motor de regras avalia o cenário combinando lógica booleana (energia crítica AND consumo alto AND previsão adversa) para gerar planos de ação.

- Gerenciamento Inteligente de Carga (Load Shedding): Em caso de crise energética, o sistema identifica e sugere o desligamento de subsistemas não essenciais (ex: entretenimento, iluminação) para proteger módulos críticos (oxigênio, pressão, temperatura).

## Arquitetura e Módulos do Sistema

1. dados_colonia.py

Este é o "banco de dados" do sistema. Ele não toma decisões, apenas organiza e fornece acesso às informações.

- Armazena o estado atual dos sensores via estrutura de chave-valor.

- Define a hierarquia da colônia (sistemas críticos de prioridade 1 até dispensáveis de prioridade 3).

- Guarda o histórico de dados (vento, irradiação, consumo) para alimentar o módulo de previsão.

- Aplica o princípio do encapsulamento, fornecendo funções como obter_estado() para que os outros módulos leiam os dados com segurança.

2. analise_energia.py

Responsável por comparar a geração atual com a demanda e o nível das baterias.

- Calcula o saldo energético atual (positivo ou negativo) e o percentual de cobertura do consumo.

- Avalia a saúde da reserva de energia, classificando a situação das baterias (crítico, baixo, normal, alto) e estimando horas de autonomia.

- Utiliza funções puras para os cálculos lógicos, separando-os da formatação visual dos relatórios.

3. previsao.py

Estima o cenário futuro para embasar decisões.

- Implementa o algoritmo de Regressão Linear Simples do zero (método OLS).

- Aplica o padrão Fit Once, Predict Many: treina os modelos na inicialização usando o histórico de dados_colonia.py e armazena os coeficientes da reta.

- Fornece estimativas cruzando os dados atuais (vento atual, hora atual) com o modelo treinado, entregando previsões com métrica de confiabilidade (R²).

4. decisoes.py

Recebe os diagnósticos e decide o que deve ser feito.

- Usa funções booleanas isoladas para avaliar critérios simples (ex: energia_esta_critica(), consumo_esta_alto()).

- Combina essas condições com operadores lógicos (AND / OR) para disparar regras complexas, como o protocolo de emergência.

- Classifica as ações por nível de urgência (CRÍTICO, ALTO, MÉDIO, INFO).

- Se necessário, percorre a hierarquia de sistemas e lista exatamente quais subsistemas devem ser desligados (e o quanto isso economizará em kW), poupando sempre a prioridade 1.

5. main.py

O ponto de entrada do programa. Ele não possui lógica de negócio complexa, atuando como um maestro que chama os outros módulos na ordem correta.

- Executa o Ciclo de Análise: Lê dados -> Analisa energia -> Faz previsões -> Toma decisões.

- Contém uma função executar_cenario() que permite simular diferentes realidades no ambiente (mudança de clima, crises, falhas ou bonança), injetando novos dados nos sensores e reavaliando toda a cadeia de sobrevivência.

