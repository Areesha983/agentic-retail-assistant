import pytest

from app.orchestrator import purchase_orchestrator


def make_sale_event():
    return {
        "event_id": 10,
        "product_id": 1,
        "old_price": 25000,
        "new_price": 19000
    }


def make_item(
    item_id=20,
    purchase_authorized_at="2026-09-07T01:00:00+00:00"
):
    return {
        "item_id": item_id,
        "cart_id": 5,
        "product_id": 1,
        "variant": "Size 9",
        "color": "Black",
        "quantity": 1,
        "maximum_price": 20000,
        "auto_buy_enabled": True,
        "purchase_authorized_at": purchase_authorized_at,
        "status": "WATCHING"
    }


def test_process_sale_event_success(monkeypatch):
    sale_event = make_sale_event()
    item = make_item()

    monkeypatch.setattr(
        purchase_orchestrator.sale_event_service,
        "find_matching_smart_carts",
        lambda event_id: {
            "sale_event": sale_event,
            "matches": [item]
        }
    )

    monkeypatch.setattr(
        purchase_orchestrator.purchase_service,
        "execute_purchase",
        lambda item_id: {
            "success": True,
            "order_id": 99,
            "smart_cart_item_id": item_id,
            "user_id": 1001
        }
    )

    result = (
        purchase_orchestrator.process_sale_event(10)
    )

    assert result["success"] is True
    assert result["event_id"] == 10
    assert result["candidate_count"] == 1
    assert result["processed_count"] == 1
    assert result["successful_purchases"] == 1
    assert result["failed_purchases"] == 0

    assert result["results"][0]["success"] is True
    assert (
        result["results"][0]["purchase"]["order_id"]
        == 99
    )


def test_process_sale_event_no_matches(monkeypatch):
    monkeypatch.setattr(
        purchase_orchestrator.sale_event_service,
        "find_matching_smart_carts",
        lambda event_id: {
            "sale_event": make_sale_event(),
            "matches": []
        }
    )

    result = (
        purchase_orchestrator.process_sale_event(10)
    )

    assert result["success"] is True
    assert result["candidate_count"] == 0
    assert result["successful_purchases"] == 0
    assert result["failed_purchases"] == 0
    assert result["results"] == []


def test_rejects_missing_authorization(monkeypatch):
    item = make_item(
        purchase_authorized_at=None
    )

    monkeypatch.setattr(
        purchase_orchestrator.sale_event_service,
        "find_matching_smart_carts",
        lambda event_id: {
            "sale_event": make_sale_event(),
            "matches": [item]
        }
    )

    called = False

    def fake_purchase(item_id):
        nonlocal called
        called = True

    monkeypatch.setattr(
        purchase_orchestrator.purchase_service,
        "execute_purchase",
        fake_purchase
    )

    result = (
        purchase_orchestrator.process_sale_event(10)
    )

    assert result["success"] is False
    assert result["successful_purchases"] == 0
    assert result["failed_purchases"] == 1
    assert result["results"][0]["stage"] == "VALIDATION"
    assert called is False


def test_purchase_failure_does_not_crash_batch(
    monkeypatch
):
    item = make_item()

    monkeypatch.setattr(
        purchase_orchestrator.sale_event_service,
        "find_matching_smart_carts",
        lambda event_id: {
            "sale_event": make_sale_event(),
            "matches": [item]
        }
    )

    def fake_purchase(item_id):
        raise ValueError("Insufficient inventory")

    monkeypatch.setattr(
        purchase_orchestrator.purchase_service,
        "execute_purchase",
        fake_purchase
    )

    result = (
        purchase_orchestrator.process_sale_event(10)
    )

    assert result["success"] is False
    assert result["successful_purchases"] == 0
    assert result["failed_purchases"] == 1
    assert (
        result["results"][0]["reason"]
        == "Insufficient inventory"
    )


def test_one_failure_does_not_stop_other_items(
    monkeypatch
):
    item_one = make_item(item_id=20)
    item_two = make_item(item_id=21)

    monkeypatch.setattr(
        purchase_orchestrator.sale_event_service,
        "find_matching_smart_carts",
        lambda event_id: {
            "sale_event": make_sale_event(),
            "matches": [
                item_one,
                item_two
            ]
        }
    )

    def fake_purchase(item_id):
        if item_id == 20:
            raise ValueError(
                "Insufficient inventory"
            )

        return {
            "success": True,
            "order_id": 100,
            "smart_cart_item_id": item_id
        }

    monkeypatch.setattr(
        purchase_orchestrator.purchase_service,
        "execute_purchase",
        fake_purchase
    )

    result = (
        purchase_orchestrator.process_sale_event(10)
    )

    assert result["successful_purchases"] == 1
    assert result["failed_purchases"] == 1
    assert result["processed_count"] == 2


def test_rejects_invalid_event_id():
    with pytest.raises(
        ValueError,
        match="Sale event ID must be greater than 0"
    ):
        purchase_orchestrator.process_sale_event(0)


def test_rejects_non_integer_event_id():
    with pytest.raises(
        ValueError,
        match="Sale event ID must be an integer"
    ):
        purchase_orchestrator.process_sale_event("10")