import time
from contextlib import contextmanager
import logging


logger = logging.getLogger("app.logger_functions")


def setup_logger(name: str = "app", level=logging.INFO):
    """
    Configura um logger específico para a aplicação, evitando logs de bibliotecas.

    :param name: O nome do logger base da aplicação (ex: 'app').
    :param level: O nível de log (ex: logging.INFO).
    :return: A instância do logger configurado.
    """
    app_logger = logging.getLogger(name)  # Logger principal da aplicação
    app_logger.setLevel(level)

    # Impede que as mensagens sejam passadas para o logger raiz, isolando-o.
    app_logger.propagate = False

    # Adiciona um handler apenas se não houver nenhum, para evitar logs duplicados.
    if not app_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        app_logger.addHandler(handler)
    return app_logger


@contextmanager
def _timed(logger: logging.Logger, message: str):
    """Context manager para medir e logar o tempo de execução de um bloco de código.
    Usa nível INFO para logging."""
    logger.info(f"▶️ {message}...")
    start_time = time.perf_counter()
    try:
        yield
        end_time = time.perf_counter()
        duration = end_time - start_time
        logger.info(f"✅ {message}... concluído em {duration:.3f}s.")
    except Exception:
        logger.error(f"❌ {message}... FALHOU.", exc_info=True)
        raise


@contextmanager
def _timed_debug(logger: logging.Logger, message: str):
    """Context manager para medir e logar o tempo de execução de um bloco de código.
    Usa nível DEBUG para logging."""
    logger.debug(f"▶️ {message}...")
    start_time = time.perf_counter()
    try:
        yield
        end_time = time.perf_counter()
        duration = end_time - start_time
        logger.debug(f"✅ {message}... concluído em {duration:.3f}s.")
    except Exception:
        logger.error(f"❌ {message}... FALHOU.", exc_info=True)
        raise
