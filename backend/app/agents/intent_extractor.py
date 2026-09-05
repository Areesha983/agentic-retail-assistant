import re

from ollama import chat

from app.config import OLLAMA_MODEL
from app.schemas.intent import RetailIntent


INTENT_EXTRACTION_PROMPT = """
You extract structured retail intent and entities from a
customer message.

Do not answer the customer.
Only extract information that is explicitly present.

Intent values:

PRODUCT_SEARCH
- customer wants to find/search/browse a product

INVENTORY_CHECK
- customer asks whether a product is available or in stock

SMART_CART
- customer wants to create, add to, configure, or manage
  a Smart Cart or automatic purchase condition

SUPPORT
- customer has a support/problem/escalation request

UNKNOWN
- none of the above can be determined

Entity rules:

1. product_name should contain the product identity, not size,
   color, branch, quantity, or price conditions.

2. brand should contain the brand only when identifiable.

3. For numeric shoe sizes, normalize the variant as:
   "Size 9", "Size 8", etc.

4. color should contain only the requested color.

5. branch should contain only the requested store branch.

6. quantity must be a positive integer when explicitly provided.
   Otherwise return null.

7. maximum_price must contain only an explicitly stated purchase
   price threshold.

   Examples:
   "below Rs. 20,000" -> 20000
   "under PKR 15000" -> 15000
   "maximum price 25000" -> 25000

   Do NOT interpret product model numbers such as
   "Air Max 270" as a maximum price.

8. auto_buy_enabled must be true ONLY when the customer explicitly
   authorizes automatic buying or purchasing.

9. auto_buy_enabled must be false when the customer explicitly
   says not to auto-buy.

10. If automatic buying is not mentioned, return null.

11. Never invent missing values.
"""


def normalize_variant(
    variant: str | None
) -> str | None:
    """
    Normalize product variants into a consistent format.

    Examples:
    "9" -> "Size 9"
    "size 9" -> "Size 9"
    """

    if variant is None:
        return None

    variant = variant.strip()

    if not variant:
        return None

    # "9" -> "Size 9"
    if variant.replace(".", "", 1).isdigit():
        return f"Size {variant}"

    # "size 9" -> "Size 9"
    if variant.lower().startswith("size "):
        size = variant[5:].strip()

        if size:
            return f"Size {size}"

    return variant


def extract_maximum_price_from_text(
    message: str
) -> float | None:
    """
    Deterministic fallback for explicit purchase price thresholds.

    This function intentionally requires clear price-condition
    wording so product names such as "Air Max 270" are not
    incorrectly interpreted as a maximum price.
    """

    patterns = [
        # Examples:
        # "below Rs. 20,000"
        # "under 20000"
        # "less than PKR 20,000"
        r"(?:below|under|less than)\s*"
        r"(?:rs\.?|pkr|₨)?\s*"
        r"([\d,]+(?:\.\d+)?)",

        # Examples:
        # "maximum price 20000"
        # "maximum price of Rs. 20,000"
        # "max price PKR 20,000"
        r"(?:maximum\s+price|max\s+price)\s*"
        r"(?:of\s+)?"
        r"(?:rs\.?|pkr|₨)?\s*"
        r"([\d,]+(?:\.\d+)?)",

        # Example:
        # "up to Rs. 20,000"
        r"(?:up to)\s*"
        r"(?:rs\.?|pkr|₨)?\s*"
        r"([\d,]+(?:\.\d+)?)",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            message,
            flags=re.IGNORECASE
        )

        if match:
            value = match.group(1).replace(",", "")

            return float(value)

    return None


def extract_retail_intent(
    user_message: str
) -> dict:
    """
    Convert a customer message into structured retail
    intent and entities using the local Ollama model.
    """

    if not isinstance(user_message, str):
        raise ValueError(
            "User message must be a string"
        )

    user_message = user_message.strip()

    if not user_message:
        raise ValueError(
            "User message cannot be empty"
        )

    response = chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "system",
                "content": INTENT_EXTRACTION_PROMPT
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        format=RetailIntent.model_json_schema(),
        options={
            "temperature": 0
        },
        think=False
    )

    intent = RetailIntent.model_validate_json(
        response.message.content
    )

    # Normalize variant formatting.
    intent.variant = normalize_variant(
        intent.variant
    )

    # Local models can occasionally miss an explicit price
    # threshold, so use deterministic backend extraction as
    # a safe fallback.
    if intent.maximum_price is None:
        intent.maximum_price = (
            extract_maximum_price_from_text(
                user_message
            )
        )

    return intent.model_dump()