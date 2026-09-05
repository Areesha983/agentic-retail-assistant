import pytest

from app.tools import purchase_tools


def test_validate_purchase(monkeypatch):
    fake_validation = {
        "valid": True,
        "reason": "Purchase validation successful",
        "current_price": 19000,
        "inventory_available": 1
    }

    def fake_validate(item_id):
        assert item_id == 10
        return fake_validation

    monkeypatch.setattr(
        purchase_tools.purchase_service,
        "validate_purchase",
        fake_validate
    )

    result = purchase_tools.validate_purchase(10)

    assert result["success"] is True
    assert result["validation"]["valid"] is True
    assert result["validation"] == fake_validation


def test_validate_purchase_rejects_invalid_id():
    with pytest.raises(
        ValueError,
        match="greater than 0"
    ):
        purchase_tools.validate_purchase(0)


def test_validate_purchase_rejects_non_integer():
    with pytest.raises(
        ValueError,
        match="must be an integer"
    ):
        purchase_tools.validate_purchase("10")


def test_execute_purchase(monkeypatch):
    fake_purchase = {
        "success": True,
        "message": "Mock purchase completed successfully",
        "order": {
            "order_id": 123,
            "product_id": 1,
            "status": "CONFIRMED"
        },
        "inventory_before": 3,
        "inventory_after": 2
    }

    def fake_execute(item_id):
        assert item_id == 10
        return fake_purchase

    monkeypatch.setattr(
        purchase_tools.purchase_service,
        "execute_purchase",
        fake_execute
    )

    result = purchase_tools.execute_purchase(10)

    assert result["success"] is True
    assert result["purchase"] == fake_purchase
    assert result["purchase"]["inventory_after"] == 2


def test_execute_purchase_rejects_invalid_id():
    with pytest.raises(
        ValueError,
        match="greater than 0"
    ):
        purchase_tools.execute_purchase(-1)


def test_execute_purchase_rejects_non_integer():
    with pytest.raises(
        ValueError,
        match="must be an integer"
    ):
        purchase_tools.execute_purchase("10")