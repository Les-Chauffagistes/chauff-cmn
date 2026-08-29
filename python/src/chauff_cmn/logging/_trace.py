import secrets
from contextvars import ContextVar, Token
from typing import Mapping, Optional

TRACEPARENT_HEADER = "traceparent"

_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")

# Portée par requête: posée par le middleware au début de la requête, lue par
# le patcher loguru (voir __init__.py) pour injecter trace_id dans CHAQUE
# ligne de log émise pendant le traitement, pas seulement celle du middleware
# lui-même.
trace_id_var: ContextVar[Optional[str]] = ContextVar("chauff_cmn_trace_id", default=None)


def _is_hex(value: str, length: int) -> bool:
    return len(value) == length and all(c in _HEX_DIGITS for c in value)


def _parse_traceparent(value: str) -> Optional[str]:
    """Extrait le trace-id d'une valeur de header `traceparent` (W3C Trace
    Context) valide, sinon None.

    Format attendu: `<version 2 hex>-<trace-id 32 hex>-<parent-id 16 hex>-
    <flags 2 hex>`, ex. `00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`.
    On ne valide que ce dont on a besoin : au moins 4 segments, trace-id de 32
    caractères hexadécimaux, pas entièrement à zéro (valeur invalide selon la
    spec W3C).
    """
    if not value:
        return None
    parts = value.split("-")
    if len(parts) < 4:
        return None
    trace_id = parts[1]
    if not _is_hex(trace_id, 32):
        return None
    if trace_id == "0" * 32:
        return None
    return trace_id.lower()


def generate_trace_id() -> str:
    return secrets.token_hex(16)  # 32 caractères hex


def generate_span_id() -> str:
    return secrets.token_hex(8)  # 16 caractères hex


def format_traceparent(trace_id: str) -> str:
    """Construit une valeur de header `traceparent` complète pour un appel
    sortant, avec un nouveau span-id à chaque appel."""
    return f"00-{trace_id}-{generate_span_id()}-01"


def resolve_trace_id(headers: Mapping[str, str]) -> str:
    """Réutilise le trace-id du header `traceparent` entrant s'il est valide,
    sinon en génère un nouveau. Ne retourne jamais None : même politique que
    Traefik ("continue le trace existant si traceparent est présent, sinon en
    démarre un nouveau").

    Fonctionne avec un CIMultiDict aiohttp (clés insensibles à la casse), un
    dict brut d'en-têtes ASGI (clés déjà en minuscules par spec), ou un objet
    Headers Web standard converti en mapping, d'où la comparaison manuelle
    plutôt qu'un simple `.get(TRACEPARENT_HEADER)`.
    """
    for key, value in headers.items():
        if key.lower() == TRACEPARENT_HEADER.lower() and value:
            trace_id = _parse_traceparent(value)
            if trace_id is not None:
                return trace_id
    return generate_trace_id()


def bind_trace_id(value: str) -> Token:
    return trace_id_var.set(value)


def reset_trace_id(token: Token) -> None:
    trace_id_var.reset(token)
