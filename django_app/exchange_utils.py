import json

from settings.utils import project_path

from django.conf import settings


class DeterminingExchangeRateError(Exception):
    pass


def price_on_bitrue() -> float:
    # File is updated via cron
    try:
        with open(project_path("JAMUSDT.BITRUE.json"), "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise DeterminingExchangeRateError()
    except json.decoder.JSONDecodeError:
        raise DeterminingExchangeRateError()
    else:
        return float(data["price"])


def exchange_token_dollar_value() -> float:
    exchange_prices = []
    # Do this for each exchange
    try:
        exchange_prices.append(price_on_bitrue())
    except DeterminingExchangeRateError:
        pass
    if not exchange_prices:
        exchange_prices = [settings.TOKEN_DOLLAR_VALUE]
    return sum(exchange_prices) / len(exchange_prices)


def jam_per_minute() -> float:
    # We pay 0.2 JAM per minute at $0.05 USDT
    # so we divide token dollar value by exchange to get the coefficient
    coefficient = settings.TOKEN_DOLLAR_VALUE / exchange_token_dollar_value()
    return coefficient * settings.JAM_PER_MINUTE  # type: ignore
