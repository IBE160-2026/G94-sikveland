"""The price of one model call (NFR6, AD-12)."""

import pytest

from app.pipeline.cost import Prices, cost_usd
from app.ports.llm import Usage

# The default `PRICE_ANSWER_*` settings.
ANSWER = Prices(input=4.00, output=20.00, cache_read=0.20, cache_write=5.00)


def _usage(input_: int = 0, output: int = 0, cache_read: int = 0, cache_write: int = 0) -> Usage:
    return Usage(
        input_tokens=input_,
        output_tokens=output,
        cache_read_tokens=cache_read,
        cache_write_tokens=cache_write,
    )


def test_the_example_from_the_spec() -> None:
    # (1000x4 + 200x20 + 50000x0.2 + 0x5) / 1e6
    assert cost_usd(_usage(1000, 200, 50000, 0), ANSWER) == 0.018


@pytest.mark.parametrize(
    ("usage", "expected"),
    [
        (_usage(input_=1_000_000), 4.0),
        (_usage(output=1_000_000), 20.0),
        (_usage(cache_read=1_000_000), 0.2),
        (_usage(cache_write=1_000_000), 5.0),
    ],
    ids=["input", "output", "cache-read", "cache-write"],
)
def test_each_token_kind_has_its_own_price(usage: Usage, expected: float) -> None:
    assert cost_usd(usage, ANSWER) == expected


def test_cache_reads_are_cheaper_than_fresh_input() -> None:
    fresh = cost_usd(_usage(input_=50_000, cache_write=0), ANSWER)
    cached = cost_usd(_usage(cache_read=50_000), ANSWER)

    assert cached < fresh


def test_no_tokens_cost_nothing() -> None:
    assert cost_usd(_usage(), ANSWER) == 0.0


def test_rounded_to_six_decimals() -> None:
    # 1 token at 4 USD per million = 0.000004; 1 cache-read token = 0.0000002 rounds away.
    assert cost_usd(_usage(input_=1, cache_read=1), ANSWER) == 0.000004
    assert cost_usd(_usage(input_=1, output=1, cache_read=3, cache_write=1), ANSWER) == 0.000030


def test_prices_are_frozen() -> None:
    with pytest.raises(AttributeError):
        ANSWER.input = 1.0  # type: ignore[misc]
