import logging
import os
import tellurium as te
from utils.logger_functions import setup_logger, _timed
from utils.copasi_hand_shake import (
    generate_handshake_model,
    save_model,
    run_simulation,
    show_plot
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # level = input("Enter logging level INFO (ENTER) ou DEBUG (QUALQUER LETRA): ")
    level = "DEBUG"
    setup_logger(debug=False)

    # (COPASI) Gera e salva o modelo do protocolo Two-Phase Handshake com circuito genético
    with _timed(logger, "(COPASI) Execução do Protocolo Two-Phase Handshake com Circuito Genético"):
        generate_handshake_model()
        save_model()
        simulation_data = run_simulation()
        logger.info("Exibindo o gráfico dos resultados da simulação.")
    show_plot(simulation_data)

    # Carrega o modelo salvo no formato SBML para uso no Tellurium
