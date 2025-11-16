import logging
import sys

from loguru import logger


class PropagateHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        if "gunicorn.app.wsgiapp" in sys.modules:
            gunicorn_logger = logging.getLogger("gunicorn.error")
            gunicorn_logger.handle(record)
        elif "uvicorn.server" in sys.modules:
            uvicorn_logger = logging.getLogger("uvicorn.error")
            uvicorn_logger.handle(record)

        if "celery.bin.worker" in sys.modules:
            celery_logger = logging.getLogger("celery.app.trace")
            celery_logger.handle(record)


logger.remove()
logger.add(PropagateHandler(), backtrace=False)
