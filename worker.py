import os  # noqa: INP001, RUF100

from uvicorn.workers import UvicornWorker


class ConfigurableUvicornWorker(UvicornWorker):
    #: dict: Set the equivalent of uvicorn command line options as keys.
    CONFIG_KWARGS = {  # noqa: RUF012
        **UvicornWorker.CONFIG_KWARGS,
        "root_path": os.getenv("SCRIPT_NAME") or os.getenv("ROOT_PATH", ""),
        "proxy_headers": True,
        "forwarded_allow_ips": "*",
    }
