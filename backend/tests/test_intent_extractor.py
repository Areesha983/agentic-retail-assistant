from types import SimpleNamespace

import pytest

from app.agents import intent_extractor


def make_response(content):
    return SimpleNamespace(
        message=SimpleNamespace(
            content=content
        )
    )


def test_extract_smart_cart_intent(monkeypatch):
    fake_response = make_response(
        """
        {
            "intent": "SMART_CART",
            "product_name": "Nike Air Max 270",
            "brand": "Nike",
            "variant": "9",
            "color": "Black",
            "branch": null,
            "quantity": 1,
            "maximum_price": 20000,
            "auto_buy_enabled": true
        }
        """
    )

    monkeypatch.setattr(
        intent_extractor,
        "chat",
        lambda **kwargs: fake_response
    )

    result = (
        intent_extractor.extract_retail_intent(
            "Add Nike Air Max 270 size 9 black "
            "to my Smart Cart and automatically "
            "buy below Rs. 20,000."
        )
    )

    assert result["intent"] == "SMART_CART"
    assert result["product_name"] == (
        "Nike Air Max 270"
    )
    assert result["brand"] == "Nike"
    assert result["variant"] == "Size 9"
    assert result["color"] == "Black"
    assert result["quantity"] == 1
    assert result["maximum_price"] == 20000
    assert result["auto_buy_enabled"] is True


def test_auto_buy_unspecified(monkeypatch):
    fake_response = make_response(
        """
        {
            "intent": "SMART_CART",
            "product_name": "Nike Air Max 270",
            "brand": "Nike",
            "variant": "Size 9",
            "color": "Black",
            "branch": null,
            "quantity": null,
            "maximum_price": null,
            "auto_buy_enabled": null
        }
        """
    )

    monkeypatch.setattr(
        intent_extractor,
        "chat",
        lambda **kwargs: fake_response
    )

    result = (
        intent_extractor.extract_retail_intent(
            "Add Nike Air Max 270 size 9 "
            "black to my Smart Cart"
        )
    )

    assert result["intent"] == "SMART_CART"
    assert result["maximum_price"] is None
    assert result["auto_buy_enabled"] is None


def test_extract_intent_rejects_empty_message():
    with pytest.raises(
        ValueError,
        match="cannot be empty"
    ):
        intent_extractor.extract_retail_intent(
            "   "
        )