"""Unit tests for ledgerlite models."""

import pytest

from ledgerlite.models import Account


def test_account_creation_with_name():
    account = Account(name="Checking")
    assert account.name == "Checking"


def test_account_default_balance_is_zero():
    account = Account(name="Savings")
    assert account.balance == 0.0


def test_account_creation_with_initial_balance():
    account = Account(name="Cash", balance=500.0)
    assert account.balance == 500.0


def test_account_creation_with_negative_balance():
    account = Account(name="Credit Card", balance=-200.0)
    assert account.balance == -200.0


def test_account_empty_name_raises():
    with pytest.raises(ValueError, match="Account name must not be empty."):
        Account(name="")


def test_account_whitespace_name_raises():
    with pytest.raises(ValueError, match="Account name must not be empty."):
        Account(name="   ")
