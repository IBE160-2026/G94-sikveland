"""The price of one model call (NFR6, AD-12).

Pure logic: prices come in as values; reading them from settings is `app/web`'s job.
"""

from dataclasses import dataclass

from app.ports.llm import Usage

TOKENS_PER_PRICE_UNIT = 1_000_000
COST_DECIMALS = 6


@dataclass(frozen=True)
class Prices:
    """USD per million tokens for one model. Cache reads and writes have their own prices."""

    input: float
    output: float
    cache_read: float
    cache_write: float


def cost_usd(usage: Usage, prices: Prices) -> float:
    """What the call cost in USD, rounded to 6 decimals. `output_tokens` includes thinking."""
    total = (
        usage.input_tokens * prices.input
        + usage.output_tokens * prices.output
        + usage.cache_read_tokens * prices.cache_read
        + usage.cache_write_tokens * prices.cache_write
    )
    return round(total / TOKENS_PER_PRICE_UNIT, COST_DECIMALS)
