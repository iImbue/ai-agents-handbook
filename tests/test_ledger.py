"""Unit tests for ledgerlite Transaction model and Ledger manager."""

from datetime import datetime, timezone

import pytest

from ledgerlite.ledger import InsufficientFundsError, Ledger, Transaction
from ledgerlite.models import Account

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_accounts(
    source_balance: float = 1000.0,
    dest_balance: float = 0.0,
) -> tuple[Account, Account]:
    return Account(name="Source", balance=source_balance), Account(
        name="Destination", balance=dest_balance
    )


# ---------------------------------------------------------------------------
# Transaction dataclass tests
# ---------------------------------------------------------------------------


class TestTransaction:
    def test_transaction_stores_accounts_and_amount(self) -> None:
        src, dst = make_accounts()
        txn = Transaction(from_account=src, to_account=dst, amount=100.0)
        assert txn.from_account is src
        assert txn.to_account is dst
        assert txn.amount == 100.0

    def test_transaction_default_description_is_empty(self) -> None:
        src, dst = make_accounts()
        txn = Transaction(from_account=src, to_account=dst, amount=50.0)
        assert txn.description == ""

    def test_transaction_accepts_custom_description(self) -> None:
        src, dst = make_accounts()
        txn = Transaction(
            from_account=src, to_account=dst, amount=50.0, description="Rent"
        )
        assert txn.description == "Rent"

    def test_transaction_default_timestamp_is_utc(self) -> None:
        src, dst = make_accounts()
        txn = Transaction(from_account=src, to_account=dst, amount=10.0)
        assert txn.timestamp.tzinfo == timezone.utc

    def test_transaction_accepts_explicit_timestamp(self) -> None:
        src, dst = make_accounts()
        ts = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        txn = Transaction(from_account=src, to_account=dst, amount=10.0, timestamp=ts)
        assert txn.timestamp == ts


# ---------------------------------------------------------------------------
# Ledger.transfer — successful cases
# ---------------------------------------------------------------------------


class TestLedgerTransferSuccess:
    def test_transfer_debits_source_account(self) -> None:
        src, dst = make_accounts(source_balance=500.0)
        ledger = Ledger()
        ledger.transfer(src, dst, 200.0)
        assert src.balance == 300.0

    def test_transfer_credits_destination_account(self) -> None:
        src, dst = make_accounts(source_balance=500.0, dest_balance=100.0)
        ledger = Ledger()
        ledger.transfer(src, dst, 200.0)
        assert dst.balance == 300.0

    def test_transfer_returns_transaction(self) -> None:
        src, dst = make_accounts()
        ledger = Ledger()
        txn = ledger.transfer(src, dst, 50.0)
        assert isinstance(txn, Transaction)

    def test_transfer_records_correct_amount_on_transaction(self) -> None:
        src, dst = make_accounts()
        ledger = Ledger()
        txn = ledger.transfer(src, dst, 75.0)
        assert txn.amount == 75.0

    def test_transfer_records_accounts_on_transaction(self) -> None:
        src, dst = make_accounts()
        ledger = Ledger()
        txn = ledger.transfer(src, dst, 75.0)
        assert txn.from_account is src
        assert txn.to_account is dst

    def test_transfer_stores_description(self) -> None:
        src, dst = make_accounts()
        ledger = Ledger()
        txn = ledger.transfer(src, dst, 10.0, description="Invoice #42")
        assert txn.description == "Invoice #42"

    def test_transfer_with_exact_balance_succeeds(self) -> None:
        src, dst = make_accounts(source_balance=250.0)
        ledger = Ledger()
        ledger.transfer(src, dst, 250.0)
        assert src.balance == 0.0
        assert dst.balance == 250.0

    def test_multiple_transfers_accumulate_correctly(self) -> None:
        src, dst = make_accounts(source_balance=1000.0, dest_balance=0.0)
        ledger = Ledger()
        ledger.transfer(src, dst, 100.0)
        ledger.transfer(src, dst, 200.0)
        ledger.transfer(src, dst, 50.0)
        assert src.balance == 650.0
        assert dst.balance == 350.0

    def test_transfer_is_appended_to_transaction_history(self) -> None:
        src, dst = make_accounts()
        ledger = Ledger()
        txn = ledger.transfer(src, dst, 10.0)
        assert txn in ledger.transactions

    def test_transaction_history_grows_with_each_transfer(self) -> None:
        src, dst = make_accounts(source_balance=300.0)
        ledger = Ledger()
        assert len(ledger.transactions) == 0
        ledger.transfer(src, dst, 50.0)
        assert len(ledger.transactions) == 1
        ledger.transfer(src, dst, 50.0)
        assert len(ledger.transactions) == 2

    def test_transactions_property_returns_snapshot(self) -> None:
        """Mutating the returned list must not affect the ledger."""
        src, dst = make_accounts()
        ledger = Ledger()
        ledger.transfer(src, dst, 10.0)
        snapshot = ledger.transactions
        snapshot.clear()
        assert len(ledger.transactions) == 1

    def test_transfer_fractional_amount(self) -> None:
        src, dst = make_accounts(source_balance=100.0)
        ledger = Ledger()
        ledger.transfer(src, dst, 0.01)
        assert abs(src.balance - 99.99) < 1e-9
        assert abs(dst.balance - 0.01) < 1e-9


# ---------------------------------------------------------------------------
# Ledger.transfer — failure / edge cases
# ---------------------------------------------------------------------------


class TestLedgerTransferFailures:
    def test_zero_amount_raises_value_error(self) -> None:
        src, dst = make_accounts()
        ledger = Ledger()
        with pytest.raises(ValueError, match="positive"):
            ledger.transfer(src, dst, 0.0)

    def test_negative_amount_raises_value_error(self) -> None:
        src, dst = make_accounts()
        ledger = Ledger()
        with pytest.raises(ValueError, match="positive"):
            ledger.transfer(src, dst, -50.0)

    def test_insufficient_funds_raises_insufficient_funds_error(self) -> None:
        src, dst = make_accounts(source_balance=100.0)
        ledger = Ledger()
        with pytest.raises(InsufficientFundsError):
            ledger.transfer(src, dst, 150.0)

    def test_insufficient_funds_error_message_contains_account_name(self) -> None:
        src, dst = make_accounts(source_balance=100.0)
        ledger = Ledger()
        with pytest.raises(InsufficientFundsError, match="Source"):
            ledger.transfer(src, dst, 200.0)

    def test_failed_transfer_does_not_modify_balances(self) -> None:
        src, dst = make_accounts(source_balance=100.0, dest_balance=50.0)
        ledger = Ledger()
        with pytest.raises(InsufficientFundsError):
            ledger.transfer(src, dst, 500.0)
        assert src.balance == 100.0
        assert dst.balance == 50.0

    def test_failed_transfer_is_not_recorded(self) -> None:
        src, dst = make_accounts(source_balance=100.0)
        ledger = Ledger()
        with pytest.raises(InsufficientFundsError):
            ledger.transfer(src, dst, 500.0)
        assert len(ledger.transactions) == 0

    def test_zero_amount_transfer_is_not_recorded(self) -> None:
        src, dst = make_accounts()
        ledger = Ledger()
        with pytest.raises(ValueError):
            ledger.transfer(src, dst, 0.0)
        assert len(ledger.transactions) == 0

    def test_source_balance_zero_raises_insufficient_funds(self) -> None:
        src = Account(name="Empty", balance=0.0)
        dst = Account(name="Piggy Bank", balance=0.0)
        ledger = Ledger()
        with pytest.raises(InsufficientFundsError):
            ledger.transfer(src, dst, 0.01)

    def test_insufficient_funds_error_is_exception_subclass(self) -> None:
        assert issubclass(InsufficientFundsError, Exception)
