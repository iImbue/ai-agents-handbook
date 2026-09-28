"""LedgerLite data models."""

from dataclasses import dataclass, field


@dataclass
class Account:
    """Represents a ledger account with a name and a balance."""

    name: str
    balance: float = field(default=0.0)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Account name must not be empty.")
