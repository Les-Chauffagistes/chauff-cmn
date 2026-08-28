from contextvars import ContextVar, Token
from typing import Mapping, Optional
from uuid import uuid4

REQUEST_ID_HEADER = "X-Request-Id"

# Portée par requête: posée par le middleware au début de la requête, lue par
# le patcher loguru (voir __init__.py) pour injecter correlation_id dans
# CHAQUE ligne de log émise pendant le traitement, pas seulement celle du
# middleware lui-même.
correlation_id_var: ContextVar[Optional[str]] = ContextVar("chauff_cmn_correlation_id", default=None)


def resolve_correlation_id(headers: Mapping[str, str]) -> str:
    """Réutilise l'id de corrélation entrant s'il existe, sinon en génère un.

    Fonctionne avec un CIMultiDict aiohttp (clés insensibles à la casse) et un
    dict brut d'en-têtes ASGI (clés déjà en minuscules par spec), d'où la
    comparaison manuelle plutôt qu'un simple `.get(REQUEST_ID_HEADER)`.
    """
    for key, value in headers.items():
        if key.lower() == REQUEST_ID_HEADER.lower() and value:
            return value
    return str(uuid4())


def bind_correlation_id(value: str) -> Token:
    return correlation_id_var.set(value)


def reset_correlation_id(token: Token) -> None:
    correlation_id_var.reset(token)
