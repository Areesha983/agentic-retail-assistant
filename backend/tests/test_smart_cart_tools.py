import pytest

from app.tools import smart_cart_tools


def test_create_smart_cart(monkeypatch):
    fake_cart = {
        "cart_id": 1,
        "user_id": "user-123",
        "status": "ACTIVE"
    }

    def fake_create(user_id):
        assert user_id == "user-123"
        return fake_cart

    monkeypatch.setattr(
        smart_cart_tools.smart_cart_service,
        "create_smart_cart",
        fake_create
    )

    result = smart_cart_tools.create_smart_cart("user-123")

    assert result["success"] is True
    assert result["cart"] == fake_cart


def test_create_smart_cart_rejects_empty_user():
    with pytest.raises(
        ValueError,
        match="cannot be empty"
    ):
        smart_cart_tools.create_smart_cart("   ")


def test_add_to_smart_cart(monkeypatch):
    fake_item = {
        "item_id": 10,
        "cart_id": 1,
        "product_id": 1,
        "variant": "Size 9",
        "color": "Black",
        "quantity": 1,
        "maximum_price": 20000,
        "auto_buy_enabled": True,
        "status": "WATCHING"
    }

    def fake_add(**kwargs):
        assert kwargs["cart_id"] == 1
        assert kwargs["product_id"] == 1
        assert kwargs["variant"] == "Size 9"
        assert kwargs["color"] == "Black"
        assert kwargs["quantity"] == 1
        assert kwargs["maximum_price"] == 20000
        assert kwargs["auto_buy_enabled"] is True

        return fake_item

    monkeypatch.setattr(
        smart_cart_tools.smart_cart_service,
        "add_item_to_smart_cart",
        fake_add
    )

    result = smart_cart_tools.add_to_smart_cart(
        cart_id=1,
        product_id=1,
        variant="Size 9",
        color="Black",
        quantity=1,
        maximum_price=20000,
        auto_buy_enabled=True
    )

    assert result["success"] is True
    assert result["item"] == fake_item


def test_add_to_smart_cart_rejects_invalid_quantity():
    with pytest.raises(
        ValueError,
        match="Quantity must be a positive integer"
    ):
        smart_cart_tools.add_to_smart_cart(
            cart_id=1,
            product_id=1,
            quantity=0
        )


def test_view_smart_cart(monkeypatch):
    fake_result = {
        "cart": {
            "cart_id": 1,
            "user_id": "user-123",
            "status": "ACTIVE"
        },
        "items": [
            {
                "item_id": 10,
                "product_id": 1,
                "status": "WATCHING"
            }
        ]
    }

    monkeypatch.setattr(
        smart_cart_tools.smart_cart_service,
        "get_smart_cart",
        lambda cart_id: fake_result
    )

    result = smart_cart_tools.view_smart_cart(1)

    assert result["success"] is True
    assert result["cart"] == fake_result["cart"]
    assert result["items"] == fake_result["items"]


def test_cancel_smart_cart_item(monkeypatch):
    fake_item = {
        "item_id": 10,
        "status": "CANCELLED"
    }

    monkeypatch.setattr(
        smart_cart_tools.smart_cart_service,
        "cancel_smart_cart_item",
        lambda item_id: fake_item
    )

    result = smart_cart_tools.cancel_smart_cart_item(10)

    assert result["success"] is True
    assert result["item"]["status"] == "CANCELLED"


def test_cancel_rejects_invalid_id():
    with pytest.raises(
        ValueError,
        match="positive integer"
    ):
        smart_cart_tools.cancel_smart_cart_item(0)