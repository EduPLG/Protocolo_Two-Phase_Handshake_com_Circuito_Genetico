import basico
import matplotlib.pyplot as plt
import pandas as pd
from os.path import join
import logging
from utils.logger_functions import _timed_debug, _timed

logger = logging.getLogger(__name__)

MODELS = "models"

# ----------------------------------------------------------------------
# Etapa 3: Validação Cinética e Interoperabilidade (COPASI/SBML -> Tellurium)
# Foco: Simulação Determinística para validar as constantes de taxa e
# o comportamento do Handshake (Pulso e Reset) com base na estequiometria
# bioquímica clássica.
# ----------------------------------------------------------------------


def generate_handshake_model():
    """
    Gera um modelo COPASI para o protocolo Two-Phase Handshake com um circuito genético.
    O modelo inclui espécies, parâmetros e reações necessárias para simular o comportamento do handshake.
    """
    with _timed_debug(logger, "Criando modelo Two Phase-Handshake"):
        # Inicia um novo modelo no COPASI
        basico.new_model(name="Two Phase Handshake")

        # --- 1. Definindo Parâmetros (Constantes de Taxa) ---
        # Usamos basico.add_parameter para criar as constantes 'k'
        basico.add_parameter(name="k1", value=0.5)      # Taxa de Ativação (Fase 1)
        basico.add_parameter(name="k2", value=0.1)      # Taxa de Inativação/Reset (Fase 2)
        basico.add_parameter(name="k_prod", value=2.0)  # Taxa de Produção
        basico.add_parameter(name="k_deg", value=0.05)  # Taxa de Degradação

        # --- 2. Definindo Espécies e Concentrações Iniciais ---
        # Por padrão, o compartimento 'default' é criado com volume 1.0.

        basico.add_species(name="P_off", initial_concentration=10.0)  # Promotor Desligado
        basico.add_species(name="P_on", initial_concentration=0.0)   # Promotor Ligado
        basico.add_species(name="R", initial_concentration=5.0)     # RNA Regulatório (Sinal)
        basico.add_species(name="G", initial_concentration=0.0)     # Produto Gênico (Saída)

    define_reactions()  # 3. Define as reações do modelo


def define_reactions():
    with _timed_debug(logger, "Adicionando reações do Handshake"):
        # FASE 1: Ativação
        basico.add_reaction(
            name="R1_Activation",
            scheme="P_off + R -> P_on",
            rate_law="k1 * P_off * R"
        )

        # FASE 2: Reset
        basico.add_reaction(
            name="R2_Reset",
            scheme="P_on -> P_off",
            rate_law="k2 * P_on"
        )

        # Saída (Produção de G)
        # P_on + G (irreversível)
        basico.add_reaction(
            name="R3_Production",
            scheme="P_on -> P_on + G",
            rate_law="k_prod * P_on"
        )

        # Degradações (usando "->" sem produtos para indicar consumo)
        basico.add_reaction(
            name="R4_Deg_R",
            scheme="R -> ",
            rate_law="k_deg * R"
        )

        basico.add_reaction(
            name="R5_Deg_G",
            scheme="G -> ",
            rate_law="k_deg * G"
        )


def save_model(file_dir: str = MODELS):
    """ Salva o modelo COPASI atual no formato SBML no diretório especificado."""
    with _timed(logger, f"Salvando modelo em {file_dir} | formato: SBML"):
        basico.save_model(
            join(file_dir, "two_phase_handshake_model.sbml"),
            type="SBML"
        )


def run_simulation() -> pd.DataFrame:
    with _timed_debug(logger, "Executando simulação"):
        # Parâmetros de Simulação
        tempo_final = 100
        intervalos = 500

        # Executa a tarefa Time Course do COPASI
        data = basico.run_time_course(
            duration=tempo_final,
            intervals=intervalos
        )
    return data


def show_plot(data: pd.DataFrame):
    """ Exibe o gráfico dos resultados da simulação do protocolo Two-Phase Handshake."""
    # Plotando os resultados
    plt.figure(figsize=(10, 6))

    # Plota todas as espécies (P_off, P_on, R, G)
    data.plot(ax=plt.gca())

    plt.title('Protocolo Two-Phase Handshake (basico/COPASI)')
    plt.xlabel('Tempo (unidades arbitrárias)')
    plt.ylabel('Concentração')
    plt.grid(True)
    plt.legend(loc='best')
    plt.show()
