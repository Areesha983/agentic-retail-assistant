import pytest

from app.tools import inventory_tools


def test_check_inventory(monkeypatch):
    fake_inventory = [
        {
            "inventory_id": 2,
            "product_id": 1,
            "variant": "Size 9",
            "color": "Black",
            "branch": "Dolmen Mall",
            "quantity": 1,
        }
    ]

    def fake_get_inventory(**kwargs):
        assert kwargs["product_id"] == 1
        return fake_inventory

    monkeypatch.setattr(
        inventory_tools.inventory_service,
        "get_inventory",
        fake_get_inventory
    )

    result = inventory_tools.check_inventory(
        product_id=1,
        variant="Size 9",
        color="Black",
        branch="Dolmen Mall"
    )

    assert result["success"] is True
    assert result["total_quantity"] == 1
    assert result["inventory"] == fake_inventory


def test_check_availability_true(monkeypatch):
    monkeypatch.setattr(
        inventory_tools.inventory_service,
        "get_inventory",
        lambda **kwargs: [{"quantity": 3}]
    )

    result = inventory_tools.check_availability(
        product_id=1,
        quantity=2
    )

    assert result["available"] is True
    assert result["available_quantity"] == 3


def test_check_availability_false(monkeypatch):
    monkeypatch.setattr(
        inventory_tools.inventory_service,
        "get_inventory",
        lambda **kwargs: [{"quantity": 1}]
    )

    result = inventory_tools.check_availability(
        product_id=1,
        quantity=2
    )

    assert result["available"] is False


def test_check_availability_no_inventory(monkeypatch):
    monkeypatch.setattr(
        inventory_tools.inventory_service,
        "get_inventory",
        lambda **kwargs: []
    )

    result = inventory_tools.check_availability(
        product_id=1,
        quantity=1
    )

    assert result["available"] is False
    assert result["available_quantity"] == 0


def test_invalid_product_id():
    with pytest.raises(
        ValueError,
        match="greater than 0"
    ):
        inventory_tools.check_inventory(0)