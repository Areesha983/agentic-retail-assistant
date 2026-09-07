from app.orchestrator.validation import (
    validate_sale_candidate
)


def make_sale_event():
    return {
        "event_id": 1,
        "product_id": 1,
        "old_price": 25000,
        "new_price": 19000
    }


def make_smart_cart_item():
    return {
        "item_id": 10,
        "product_id": 1,
        "status": "WATCHING",
        "auto_buy_enabled": True,
        "purchase_authorized_at":
            "2026-09-07T01:00:00+00:00",
        "maximum_price": 20000,
        "quantity": 1,
        "variant": "Size 9",
        "color": "Black"
    }


def test_valid_sale_candidate():
    result = validate_sale_candidate(
        make_sale_event(),
        make_smart_cart_item()
    )

    assert result["valid"] is True


def test_rejects_different_product():
    item = make_smart_cart_item()
    item["product_id"] = 2

    result = validate_sale_candidate(
        make_sale_event(),
        item
    )

    assert result["valid"] is False


def test_rejects_non_watching_item():
    item = make_smart_cart_item()
    item["status"] = "PURCHASED"

    result = validate_sale_candidate(
        make_sale_event(),
        item
    )

    assert result["valid"] is False


def test_rejects_auto_buy_disabled():
    item = make_smart_cart_item()
    item["auto_buy_enabled"] = False

    result = validate_sale_candidate(
        make_sale_event(),
        item
    )

    assert result["valid"] is False


def test_rejects_missing_authorization():
    item = make_smart_cart_item()
    item["purchase_authorized_at"] = None

    result = validate_sale_candidate(
        make_sale_event(),
        item
    )

    assert result["valid"] is False


def test_rejects_missing_maximum_price():
    item = make_smart_cart_item()
    item["maximum_price"] = None

    result = validate_sale_candidate(
        make_sale_event(),
        item
    )

    assert result["valid"] is False


def test_rejects_price_above_limit():
    event = make_sale_event()
    event["new_price"] = 21000

    result = validate_sale_candidate(
        event,
        make_smart_cart_item()
    )

    assert result["valid"] is False


def test_accepts_price_equal_to_limit():
    event = make_sale_event()
    event["new_price"] = 20000

    result = validate_sale_candidate(
        event,
        make_smart_cart_item()
    )

    assert result["valid"] is True