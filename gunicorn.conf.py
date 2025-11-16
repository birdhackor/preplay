import os  # noqa: INP001, RUF100
import signal


def worker_int(worker):
    os.kill(worker.pid, signal.SIGINT)
