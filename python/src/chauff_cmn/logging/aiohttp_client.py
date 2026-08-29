"""Client HTTP sortant aiohttp qui propage le contexte de trace courant (W3C
Trace Context) sur chaque requête via un header `traceparent`. Nécessite
`aiohttp` (extra `aiohttp`).
"""

from typing import Any, Optional

import aiohttp
from aiohttp import TraceConfig, TraceRequestStartParams

from ._trace import TRACEPARENT_HEADER, format_traceparent, generate_trace_id, trace_id_var

__all__ = ["traced_trace_config", "create_traced_session"]


async def _on_request_start(
    session: aiohttp.ClientSession,
    trace_config_ctx: Any,
    params: TraceRequestStartParams,
) -> None:
    # Reprend le trace_id de la requête entrante en cours s'il y en a une,
    # sinon en démarre un nouveau à la volée — un appel sortant part toujours
    # avec un traceparent, y compris depuis un job de fond hors contexte de
    # requête HTTP entrante. Un span-id neuf est généré à chaque appel, jamais
    # réutilisé.
    trace_id: Optional[str] = trace_id_var.get() or generate_trace_id()
    params.headers[TRACEPARENT_HEADER] = format_traceparent(trace_id)


def traced_trace_config() -> TraceConfig:
    """TraceConfig aiohttp qui pose `traceparent` sur chaque requête sortante.

    Usage: `aiohttp.ClientSession(trace_configs=[traced_trace_config()])`.
    """
    trace_config = TraceConfig()
    trace_config.on_request_start.append(_on_request_start)
    return trace_config


def create_traced_session(**kwargs: Any) -> aiohttp.ClientSession:
    """Raccourci équivalent à `aiohttp.ClientSession(trace_configs=[traced_trace_config()], **kwargs)`."""
    trace_configs = [traced_trace_config(), *kwargs.pop("trace_configs", [])]
    return aiohttp.ClientSession(trace_configs=trace_configs, **kwargs)
