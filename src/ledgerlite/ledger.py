"""LedgerLite transaction model and ledger manager."""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from ledgerlite.models import Account


@dataclass
class Transaction:
    """Records a fund transfer from one account to another.

    Attributes:
        from_account: The account funds are debited from.
        to_account: The account funds are credited to.
        amount: The positive monetary amount to transfer.
        timestamp: UTC datetime when the transaction was recorded.
        description: Optional human-readable note for this transaction.
    """

    from_account: Account
    to_account: Account
    amount: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    description: str = ""


class InsufficientFundsError(Exception):
    """Raised when a transfer would overdraw the source account."""


class Ledger:
    """Manages a list of accounts and records transfers between them."""

    def __init__(self) -> None:
        self._transactions: list[Transaction] = []

    @property
    def transactions(self) -> list[Transaction]:
        """Return a snapshot of all recorded transactions."""
        return list(self._transactions)

    def transfer(
        self,
        from_account: Account,
        to_account: Account,
        amount: float,
        description: str = "",
    ) -> Transaction:
        """Transfer *amount* from *from_account* to *to_account*.

        Args:
            from_account: Account to debit.
            to_account: Account to credit.
            amount: Positive amount to transfer.
            description: Optional note for the transaction.

        Returns:
            The recorded :class:`Transaction`.

        Raises:
            ValueError: If *amount* is not strictly positive.
            InsufficientFundsError: If *from_account* has insufficient balance.
        """
        if amount <= 0:
            raise ValueError(f"Transfer amount must be positive, got {amount!r}.")

        if from_account.balance < amount:
            raise InsufficientFundsError(
                f"Account '{from_account.name}' has insufficient funds: "
                f"balance {from_account.balance!r} < amount {amount!r}."
            )

        from_account.balance -= amount
        to_account.balance += amount

        txn = Transaction(
            from_account=from_account,
            to_account=to_account,
            amount=amount,
            description=description,
        )
        self._transactions.append(txn)
        return txn
