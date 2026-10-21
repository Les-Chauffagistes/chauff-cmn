# Généré par scripts/generate-python.sh à partir de openapi/schema.yaml — ne pas éditer à la main.

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class ApiError(BaseModel):
    """
    Forme standard d'une réponse d'erreur, commune à tous les microservices.
    """

    code: str = Field(
        ..., description='Code d\'erreur stable et machine-readable, ex. "NOT_FOUND".'
    )
    message: str = Field(
        ..., description="Message lisible destiné aux logs ou à l'affichage debug."
    )
    details: dict[str, Any] | None = None


class User(BaseModel):
    user_id: str
    pseudo: str


class LNChallenge(BaseModel):
    lnurl: str
    k1: str


class LNCallbackSuccessPayload(BaseModel):
    status: str
    code: str


class ExchangeCodeStatus(Enum):
    onboarding = 'onboarding'
    logged_in = 'logged_in'


class ExchangeCodePayload(BaseModel):
    status: ExchangeCodeStatus
    session_token: str | None = None
    user: User | None = None


class SubscriptionStatus(Enum):
    inactive = 'inactive'
    active = 'active'
    expired = 'expired'


class Subscription(BaseModel):
    pool_address: str
    started_at: AwareDatetime | None = None
    expires_at: AwareDatetime | None = None
    status: SubscriptionStatus
    created_at: AwareDatetime
    updated_at: AwareDatetime


class PoolPrivateBestRecord(BaseModel):
    month: str
    sdiff: float
    address: str
    epoch: float


class PoolBestRecord(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    month: str
    sdiff: float
    username: str
    workername: str
    epoch: float


class Hashrates(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    hashrate1m: str
    hashrate5m: str
    hashrate1hr: str
    hashrate1d: str
    hashrate7d: str


class Node(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    height: int
    subversion: str
    peers: int


class NumberHashrate(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    hashrate1m: float
    hashrate5m: float
    hashrate1hr: float
    hashrate1d: float
    hashrate7d: float


class PoolHashrates(Hashrates):
    hashrate15m: str
    hashrate6hr: str


class PoolHashrateRecord(BaseModel):
    date: str
    hashrate: int


class PoolRuntime(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    runtime: int
    lastupdate: int
    Users: int
    Workers: int
    Idle: int
    Disconnected: int


class PoolShares(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    diff: float
    accepted: int
    rejected: int
    bestshare: int
    SPS1m: float
    SPS5m: float
    SPS15m: float
    SPS1h: float


class PoolHost(BaseModel):
    name: str
    online: bool
    latencyMs: float
    raw: str


class PoolPing(BaseModel):
    updatedAt: str
    total: int
    online: int
    offline: int
    hosts: list[PoolHost]


class Repartition(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    shares: float
    total_vardiff: float
    weight: float
    percentage: float


class Worker(Hashrates):
    workername: str
    lastshare: int
    shares: int
    bestshare: float
    bestever: float


class Share(BaseModel):
    workinfoid: int
    clientid: int
    diff: int
    sdiff: float
    hash: str
    result: bool
    errn: int
    createdate: str
    ts: float
    workername: str
    username: str
    address: str
    worker: str
    workernameAddr: str
    ip: str
    agent: str
    round: str
    file: str
    rejectReason: str | None = None


class GlobalStats(Hashrates):
    shares: float
    bestshare: float
    workers: float


class PoolStats(BaseModel):
    address: str
    globalStats: GlobalStats
    workers: list[Worker]


class PoolTopHashrate(BaseModel):
    address: str
    workerCount: int
    totalHashrate1hr: int


class PoolTopBestShares(BaseModel):
    address: str = Field(..., description='Valeur tronquée', examples=['bc1qq...5m'])
    workerCount: int
    bestshare: int


class PoolTop(BaseModel):
    topBestShares: list[PoolTopBestShares]
    topHashrate: list[PoolTopHashrate]


class BitcoinPrice(BaseModel):
    time: float
    USD: float
    EUR: float
    GBP: float
    CAD: float
    CHF: float
    AUD: float
    JPY: float | None = None


class WorkerStatsHistory(BaseModel):
    timestamp: str
    avg_hashrate1m: str
    avg_hashrate5m: str
    avg_hashrate1h: str
    avg_hashrate1d: str
    avg_hashrate7d: str
    avg_weight: str


class PoolStatsHistory(BaseModel):
    timestamp: str
    avg_hashrate1h: float
    avg_hashrate1d: float


class WorkersWeights(BaseModel):
    worker_id: str
    avg_weight: str
    timestamp: str


class PoolDistributionElement(BaseModel):
    workername: str
    diff_sum: float
    part: float
    shares_ok: float
    shares_ko: float


class PoolWebsocketShareElement(BaseModel):
    type: str
    share_id: str = Field(
        ..., examples=['debian:000ed6bd/6ab2eef0000145f3.sharelog:1923,']
    )
    epoch: int = Field(..., examples=[1])
    seq: int = Field(..., examples=[20773258])
    instance: str = Field(
        ...,
        description='The instance name of the pool server where the share was submitted',
        examples=['debian'],
    )
    created_at: AwareDatetime = Field(
        ..., examples=['2026-10-21T12:20:51.262066+00:00']
    )
    workinfoid: int = Field(..., examples=[7688470228434503155])
    block_height: int = Field(..., examples=[972480])
    username: str = Field(
        ...,
        description='The bitcoin address',
        examples=['bc1qqp9zq4an6nyzhcspz2xfmkcf8rj0p6w94a5gyeu2a7rghxjhnqqsvymz5m'],
    )
    workername: str = Field(
        ...,
        description='The worker name, including the username',
        examples=[
            'bc1qqp9zq4an6nyzhcspz2xfmkcf8rj0p6w94a5gyeu2a7rghxjhnqqsvymz5m.Heatman'
        ],
    )
    diff: float = Field(..., examples=[1000.0])
    sdiff: float = Field(..., examples=[2026986.9233135832])
    result: bool = Field(
        ..., description='If the share is valid and accepted', examples=[True]
    )
    parse_error: bool = Field(..., examples=[False])


class PoolWebsocketWatermarkElement(BaseModel):
    type: str = Field(..., examples=['watermark'])
    watermark: AwareDatetime = Field(..., examples=['2026-10-21T12:20:51.262066+00:00'])


class Pool(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    runtime: PoolRuntime
    hashrates: PoolHashrates
    shares: PoolShares


class PoolUser(Hashrates):
    lastshare: float
    workers: float
    shares: float
    bestshare: float
    bestever: float
    authorised: float
    worker: list[Worker]


class PoolApiDataPayload(BaseModel):
    backup_pool: bool
    pool: Pool
    users: dict[str, PoolUser]
    repartition: dict[str, Repartition]
    monthly_bests: list[PoolBestRecord]
    node: Node
