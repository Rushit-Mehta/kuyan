"""
KUYAN - Currency Converter Module
Copyright (c) 2025 mycloudcondo inc.
Licensed under MIT License - see LICENSE file for details
"""

import requests
from typing import Dict, Optional


class CurrencyConverter:
    """Handles currency exchange rate fetching from frankfurter.app API"""

    BASE_URL = "https://api.frankfurter.app"

    @staticmethod
    def get_exchange_rates(base_currency: str, target_currencies: list, date: Optional[str] = None) -> Optional[Dict[str, float]]:
        """
        Fetch exchange rates from frankfurter.app

        Args:
            base_currency: Base currency code
            target_currencies: List of target currency codes
            date: Optional date in YYYY-MM-DD format. If None, uses latest rates.

        Returns:
            Dictionary with exchange rates or None if request fails
            Format: {"USD_CAD": 1.35, "USD_INR": 83.5, ...}
        """
        try:
            # Build URL
            if date:
                url = f"{CurrencyConverter.BASE_URL}/{date}"
            else:
                url = f"{CurrencyConverter.BASE_URL}/latest"

            # Request parameters
            params = {
                "from": base_currency,
                "to": ",".join([c for c in target_currencies if c != base_currency])
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            rates = data.get("rates", {})

            # Format rates with base currency prefix
            formatted_rates = {}
            for currency, rate in rates.items():
                formatted_rates[f"{base_currency}_{currency}"] = rate

            # Add base currency to itself (always 1.0)
            formatted_rates[f"{base_currency}_{base_currency}"] = 1.0

            return formatted_rates

        except requests.exceptions.RequestException as e:
            print(f"Error fetching exchange rates: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    @staticmethod
    def get_all_cross_rates(currencies: list = None, date: Optional[str] = None) -> Optional[Dict[str, float]]:
        """
        Get all cross rates between provided currencies

        Args:
            currencies: List of currency codes. If None, uses default ["CAD", "USD", "INR"]
            date: Optional date in YYYY-MM-DD format

        Returns:
            Dictionary with all exchange rates between currencies
            Format: {"USD_CAD": 1.35, "CAD_USD": 0.74, "USD_INR": 83.5, ...}
        """
        # Use default currencies if none provided (for backward compatibility)
        if currencies is None:
            currencies = ["CAD", "USD", "INR"]

        all_rates = {}

        for base in currencies:
            rates = CurrencyConverter.get_exchange_rates(base, currencies, date)
            if rates:
                all_rates.update(rates)

        return all_rates if all_rates else None

    @staticmethod
    def convert(amount: float, from_currency: str, to_currency: str, rates: Dict[str, float]) -> float:
        """
        Convert amount from one currency to another using provided rates

        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            rates: Dictionary of exchange rates

        Returns:
            Converted amount
        """
        if from_currency == to_currency:
            return amount

        # Try direct conversion
        direct_key = f"{from_currency}_{to_currency}"
        if direct_key in rates:
            return amount * rates[direct_key]

        # Try inverse conversion
        inverse_key = f"{to_currency}_{from_currency}"
        if inverse_key in rates:
            return amount / rates[inverse_key]

        # Try conversion through USD as intermediary
        from_to_usd_key = f"{from_currency}_USD"
        usd_to_target_key = f"USD_{to_currency}"

        if from_to_usd_key in rates and usd_to_target_key in rates:
            usd_amount = amount * rates[from_to_usd_key]
            return usd_amount * rates[usd_to_target_key]

        # If all else fails, return original amount
        print(f"Warning: Could not find conversion rate for {from_currency} to {to_currency}")
        return amount
