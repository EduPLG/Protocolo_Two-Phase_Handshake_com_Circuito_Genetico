import basico
from os.path import join
import os
import matplotlib.pyplot as plt
import pandas as pd
import logging
from utils.logger_functions import _timed, setup_logger, _timed_debug

MODEL_FILE_PATH = join("models", "handshake_sRNA_basico.cps")
logger = logging.getLogger(__name__)


def criar_modelo_handshake():
    """
    Cria um novo modelo COPASI, define parâmetros globais e espécies.
    :return: O objeto do modelo criado.
    """
    with _timed_debug(logger, "Criando novo modelo COPASI: Handshake_TwoPhase_sRNA"):
        model = basico.new_model(name="Handshake_TwoPhase_sRNA")

    with _timed_debug(logger, "Definindo Parâmetros Globais"):
        basico.add_parameter(name='V_MAX1', initial_value=2.0)
        basico.add_parameter(name='V_MAX2', initial_value=2.0)
        basico.add_parameter(name='K_M_ATIVACAO', initial_value=0.5)
        basico.add_parameter(name='K_I_REPRESSAO', initial_value=0.5)
        basico.add_parameter(name='HILL_COEF', initial_value=4.0)
        basico.add_parameter(name='k_DEG1', initial_value=0.3)
        basico.add_parameter(name='k_DEG2', initial_value=0.3)

    with _timed_debug(logger, "Definindo Espécies"):
        basico.add_species(name='sRNA1', initial_concentration=0.1)
        basico.add_species(name='sRNA2', initial_concentration=0.0)
    return model


def definir_reacoes_cineticas():
    """Define as reações de produção e degradação do modelo."""
    with _timed_debug(logger, "Definindo Reações Cinéticas (Leis de Hill)"):
        # R1: Produção de sRNA1 (reprimida por sRNA2)
        kinetic_law_1 = "V_MAX1 * (1.0 / (1.0 + pow(<sRNA2> / K_I_REPRESSAO, HILL_COEF)))"
        basico.add_reaction(
            name='PROD_sRNA1_REPRIMIDA',
            scheme='-> sRNA1',
            reversible=False,
            function=kinetic_law_1
        )

        # R2: Produção de sRNA2 (ativada por sRNA1)
        kinetic_law_2 = "V_MAX2 * (pow(<sRNA1>, HILL_COEF) / (pow(K_M_ATIVACAO, HILL_COEF) + pow(<sRNA1>, HILL_COEF)))"
        basico.add_reaction(
            name='PROD_sRNA2_ATIVADA',
            scheme='-> sRNA2',
            reversible=False,
            function=kinetic_law_2
        )

        # R3: Degradação de sRNA1
        kinetic_law_3 = "k_DEG1 * <sRNA1>"
        basico.add_reaction(
            name='DEG_sRNA1',
            scheme='sRNA1 ->',
            reversible=False,
            function=kinetic_law_3
        )

        # R4: Degradação de sRNA2
        kinetic_law_4 = "k_DEG2 * <sRNA2>"
        basico.add_reaction(
            name='DEG_sRNA2',
            scheme='sRNA2 ->',
            reversible=False,
            function=kinetic_law_4
        )


def plotar_resultados(results: pd.DataFrame):
    """
    Plota as concentrações de sRNA1 e sRNA2 ao longo do tempo.
    :param results: DataFrame do pandas com os dados da simulação.
    """
    plt.figure(figsize=(12, 7))
    plt.plot(results.index, results['sRNA1'], label='sRNA1', color='blue')
    plt.plot(results.index, results['sRNA2'], label='sRNA2', color='red')
    plt.title('Simulação do Handshake Two-Phase com sRNA')
    plt.xlabel('Tempo (segundos)')
    plt.ylabel('Concentração')
    plt.legend()
    plt.grid(True)
    plt.show()


def main(level=logging.INFO):
    """
    Função principal para orquestrar a criação, simulação e visualização do modelo.
    """
    # Configura e obtém o logger específico para este script
    global logger
    logger = setup_logger(__name__, level)

    with _timed(logger, "Processo de simulação do Handshake Two-Phase"):
        with _timed(logger, "Construção do modelo"):
            model = criar_modelo_handshake()
            definir_reacoes_cineticas()

        with _timed(logger, "Execução da simulação"):
            results = basico.run_time_course(
                duration=1000.0,
                intervals=10000,
                model=model
            )
        print("\n" + "=" * 70)
        print("RESULTADOS DA SIMULAÇÃO: Handshake Two-Phase")
        print("=" * 70)
        print(results.head(20).to_string())
        print("\n(Apenas as primeiras 20 linhas exibidas.)")

        with _timed(logger, "Geração do gráfico"):
            plotar_resultados(results)

        with _timed_debug(logger, f"Salvamento do modelo em '{MODEL_FILE_PATH}'"):
            os.makedirs(os.path.dirname(MODEL_FILE_PATH), exist_ok=True)
            basico.save_model(MODEL_FILE_PATH)


if __name__ == "__main__":
    level = input("Digite 1 para prints simples (INFO) ou 2 para prints detalhados (DEBUG): ")
    if level == '2':
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    main(log_level)
