"""Cost Guard — Daily budget tracking to prevent billing surprises."""
import time

from fastapi import HTTPException

from app.config import settings

_daily_cost = 0.0
_cost_reset_day = time.strftime("%Y-%m-%d")

# Pricing (GPT-4o-mini)
INPUT_COST_PER_1K = 0.00015   # $0.15 per 1M input tokens
OUTPUT_COST_PER_1K = 0.0006   # $0.60 per 1M output tokens


def check_and_record_cost(input_tokens: int, output_tokens: int):
    """Check budget and record token usage.

    Raises 503 if daily budget is exhausted.
    """
    global _daily_cost, _cost_reset_day

    # Reset counter at midnight
    today = time.strftime("%Y-%m-%d")
    if today != _cost_reset_day:
        _daily_cost = 0.0
        _cost_reset_day = today

    # Check budget
    if _daily_cost >= settings.daily_budget_usd:
        raise HTTPException(503, "Daily budget exhausted. Try tomorrow.")

    # Calculate and record cost
    cost = (input_tokens / 1000) * INPUT_COST_PER_1K + \
           (output_tokens / 1000) * OUTPUT_COST_PER_1K
    _daily_cost += cost


def get_daily_cost() -> float:
    """Return current daily cost in USD."""
    return _daily_cost
