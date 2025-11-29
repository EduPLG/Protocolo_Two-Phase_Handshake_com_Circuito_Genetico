import time
from contextlib import contextmanager
import logging
import sys


logger = logging.getLogger(__name__)


def setup_logger(debug=False):
    """
    Configura o logging para a aplicação.
    """
    if debug:
        level = logging.DEBUG
    else:
        level = logging.INFO

    log_formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s: %(message)s", datefmt="%H:%M:%S"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(log_formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(handler)


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
