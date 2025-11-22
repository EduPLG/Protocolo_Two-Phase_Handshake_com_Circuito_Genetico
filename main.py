import logging
from utils.logger_functions import setup_logger, _timed
from utils.hand_shake import (
    generate_handshake_model,
    run_simulation,
    show_plot
)

logger = logging.getLogger("app")

if __name__ == "__main__":
    level = input("Enter logging level INFO (ENTER) ou DEBUG (QUALQUER LETRA): ")
    if level:
        level = logging.DEBUG
    else:
        level = logging.INFO
    setup_logger(name="app", level=level)
    with _timed(logger, "Execução do Protocolo Two-Phase Handshake com Circuito Genético"):
        generate_handshake_model()
        simulation_data = run_simulation()
    logger.info("Exibindo o gráfico dos resultados da simulação.")
    show_plot(simulation_data)
