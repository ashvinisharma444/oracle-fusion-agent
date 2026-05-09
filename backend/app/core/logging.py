"""
Structured JSON logging with correlation ID context.
Uses structlog for enterprise-grade log output.
"""
import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional
import structlog
from structlog.types import EventDict, WrappedLogger

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    cid = correlation_id_var.get()
    if not cid:
        cid = str(uuid.uuid4())
        correlation_id_var.set(cid)
    return cid


def set_correlation_id(correlation_id: str) -> None:
    correlation_id_var.set(correlation_id)


def add_correlation_id(logger: WrappedLogger, method: str, event_dict: EventDict) -> EventDict:
    event_dict["correlation_id"] = get_correlation_id()
    return event_dict


def add_service_info(logger: WrappedLogger, method: str, event_dict: EventDict) -> EventDict:
    event_dict["service"] = "oracle-fusion-agent"
    return event_dict


def configure_logging(log_level: str = "INFO", json_logs: bool = True) -> None:
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        add_correlation_id,
        add_service_info,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if json_logs:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Suppress noisy third-party loggers
    for name in ["uvicorn.access", "sqlalchemy.engine", "playwright"]:
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)
