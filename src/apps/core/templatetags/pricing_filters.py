from django import template

register = template.Library()


@register.filter(name="format_price_with_currency")
def format_price_with_currency(obj, field_name="unit_amount"):
    """
    Format a Stripe Price, Invoice, or plan dict with currency code.

    This filter accesses two fields on the djstripe model object or dictionary:
    1. Amount field (e.g., 'unit_amount', 'total', or 'amount') - integer in cents
    2. 'currency' field - 3-letter ISO code (e.g., 'usd', 'eur')

    Converts cents to dollars and displays with uppercase currency code.

    Examples:
        Price(unit_amount=1000, currency='usd') → "10.00 USD"
        Invoice(total=2500, currency='eur') → "25.00 EUR"
        {'amount': 1000, 'currency': 'usd'} → "10.00 USD"

    Args:
        obj: djstripe.models.Price, Invoice instance, or dict (e.g., subscription.plan)
        field_name: Name of the amount field to read (default: "unit_amount")
                   - For Price objects: "unit_amount"
                   - For Invoice objects: "total"
                   - For plan dicts: "amount"

    Returns:
        Formatted string: "amount CURRENCY"

    Data Access:
        - obj.{field_name} or obj[field_name] - Gets the amount in cents (integer)
        - obj.currency or obj['currency'] - Gets the 3-letter ISO currency code (string)
    """
    try:
        # Handle both object attributes and dictionary keys
        if isinstance(obj, dict):
            # For dictionaries (e.g., subscription.plan JSONField)
            amount_cents = obj.get(field_name, 0)
            currency = obj.get('currency', 'usd')
        else:
            # For ORM objects (e.g., Price, Invoice)
            amount_cents = getattr(obj, field_name, 0)
            currency = getattr(obj, 'currency', 'usd')

        # Convert cents to dollars (always divide by 100)
        amount_dollars = float(amount_cents) / 100

        # Format: "10.00 USD" (amount with 2 decimals + uppercase currency)
        return f"{amount_dollars:.2f} {currency.upper()}"
    except (AttributeError, TypeError, ValueError, KeyError):
        # Fallback if object doesn't have expected fields
        return "0.00 USD"
