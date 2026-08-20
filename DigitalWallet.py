from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, List, Optional, Tuple


class Account:
    """Represents an individual user account with internal mutation locks."""

    def __init__(self, account_id: str, pin: str, name: str, daily_limit: float = 50000.0):
        self.account_id: str = account_id
        self.pin: str = pin
        self.name: str = name
        self.balance: float = 0.0
        self.daily_limit: float = daily_limit
        self.is_locked: bool = False
        
        # Thread lock specifically for this account resource
        self.lock: Lock = Lock()
        
        # Security and tracking states
        self.failed_pin_attempts: int = 0
        self.transactions: List[Dict] = []
        self.failed_timestamps: List[datetime] = []

    def get_daily_spent(self) -> float:
        """Calculates total successful outgoing funds for the current calendar date."""
        today = datetime.now().date()
        return sum(
            tx["amount"] for tx in self.transactions 
            if tx["timestamp"].date() == today and tx["type"] in ["Withdrawal", "Transfer Out"]
        )


class DigitalWallet:
    """Core system managing accounts, financial transactions, and fraud detection."""

    def __init__(self):
        self.accounts: Dict[str, Account] = {}
        self.global_lock: Lock = Lock()  # Prevents race conditions during account generation
        self.UNUSUAL_AMOUNT_THRESHOLD: float = 100000.0

    def create_account(self, account_id: str, pin: str, name: str, daily_limit: float = 50000.0) -> str:
        with self.global_lock:
            if account_id in self.accounts:
                return f"Error: Account ID {account_id} already exists."
            self.accounts[account_id] = Account(account_id, pin, name, daily_limit)
            return f"Account successfully created for {name} (ID: {account_id})."

    def verify_balance(self, account_id: str, pin: str) -> str:
        if account_id not in self.accounts:
            return "Error: Account not found."
        
        account = self.accounts[account_id]
        with account.lock:
            authenticated, message = self._authenticate(account, pin)
            if not authenticated:
                return message
            return f"Account Balance for {account.name}: ${account.balance:,.2f}"

    def deposit(self, account_id: str, amount: float) -> str:
        if account_id not in self.accounts:
            return "Error: Account not found."
        if amount <= 0:
            return "Error: Deposit amount must be positive."

        account = self.accounts[account_id]
        with account.lock:
            is_fraudulent, reason = self._is_fraudulent(account, "Deposit", amount)
            tx_status = "Flagged/Suspicious" if is_fraudulent else "Success"

            account.balance += amount
            self._log_transaction(account, "Deposit", amount, tx_status, reason)

            if is_fraudulent:
                return f"Deposit processed but FLAGGED as suspicious. Reason: {reason}"
            return f"Successfully deposited ${amount:,.2f}. New Balance: ${account.balance:,.2f}"

    def withdraw(self, account_id: str, pin: str, amount: float) -> str:
        if account_id not in self.accounts:
            return "Error: Account not found."
        if amount <= 0:
            return "Error: Withdrawal amount must be positive."

        account = self.accounts[account_id]
        with account.lock:
            authenticated, message = self._authenticate(account, pin)
            if not authenticated:
                return message

            if account.balance < amount:
                return "Error: Insufficient funds."
            if account.get_daily_spent() + amount > account.daily_limit:
                return "Error: Operation exceeds daily transaction limit."

            is_fraudulent, reason = self._is_fraudulent(account, "Withdrawal", amount)
            tx_status = "Flagged/Suspicious" if is_fraudulent else "Success"

            account.balance -= amount
            self._log_transaction(account, "Withdrawal", amount, tx_status, reason)

            if is_fraudulent:
                return f"Withdrawal completed but FLAGGED as suspicious. Reason: {reason}"
            return f"Successfully withdrew ${amount:,.2f}. Remaining Balance: ${account.balance:,.2f}"

    def transfer(self, sender_id: str, pin: str, receiver_id: str, amount: float) -> str:
        if sender_id not in self.accounts or receiver_id not in self.accounts:
            return "Error: Account not found."
        if sender_id == receiver_id:
            return "Error: Cannot transfer money to the same account."
        if amount <= 0:
            return "Error: Transfer amount must be positive."

        sender = self.accounts[sender_id]
        receiver = self.accounts[receiver_id]

        # Acquire lock deterministically based on ID sorting to completely avoid operational deadlock
        first_lock, second_lock = (sender, receiver) if sender_id < receiver_id else (receiver, sender)

        with first_lock.lock:
            with second_lock.lock:
                authenticated, message = self._authenticate(sender, pin)
                if not authenticated:
                    return message

                if sender.balance < amount:
                    return "Error: Insufficient funds."
                if sender.get_daily_spent() + amount > sender.daily_limit:
                    return "Error: Operation exceeds sender's daily transaction limit."

                # Check Duplicate Transaction (Same recipient, same amount within the last 15 seconds)
                if self._is_duplicate(sender, receiver_id, amount):
                    return "Error: Duplicate transaction detected. Please wait before retrying."

                is_fraudulent, reason = self._is_fraudulent(sender, "Transfer Out", amount)
                tx_status = "Flagged/Suspicious" if is_fraudulent else "Success"

                sender.balance -= amount
                receiver.balance += amount

                self._log_transaction(sender, "Transfer Out", amount, tx_status, reason, recipient=receiver_id)
                self._log_transaction(receiver, "Transfer In", amount, "Success", sender_id=sender_id)

                if is_fraudulent:
                    return f"Transfer executed but FLAGGED as suspicious. Reason: {reason}"
                return f"Successfully transferred ${amount:,.2f} to Account {receiver_id}."

    def _authenticate(self, account: Account, input_pin: str) -> Tuple[bool, str]:
        if account.is_locked:
            return False, "Error: This account is permanently locked due to suspicious activity."

        if account.pin != input_pin:
            account.failed_pin_attempts += 1
            account.failed_timestamps.append(datetime.now())
            if self._has_multiple_failed_pins(account):
                account.is_locked = True
                return False, "Security Alert: Too many failed PIN entry attempts! Account locked."
            return False, "Error: Invalid PIN."

        account.failed_pin_attempts = 0
        return True, "Authenticated"

    def _is_fraudulent(self, account: Account, tx_type: str, amount: float) -> Tuple[bool, str]:
        now = datetime.now()
        ten_minutes_ago = now - timedelta(minutes=10)

        if len([tx for tx in account.transactions if tx["timestamp"] >= ten_minutes_ago]) >= 5:
            return True, "High velocity: More than 5 transactions in 10 minutes."
        if tx_type in ["Withdrawal", "Transfer Out"] and amount >= (account.daily_limit * 0.80):
            return True, "Large transaction size: Requesting over 80% of daily total limit."
        if len([t for t in account.failed_timestamps if t >= ten_minutes_ago]) >= 3:
            return True, "High Risk profile: Context includes multiple failed PIN challenges recently."
        if amount >= self.UNUSUAL_AMOUNT_THRESHOLD:
            return True, f"Outlier volume: Amount equals or exceeds static system cap (${self.UNUSUAL_AMOUNT_THRESHOLD:,.2f})."
        return False, ""

    def _is_duplicate(self, account: Account, recipient_id: str, amount: float) -> bool:
        """Heuristic checking if an identical transaction went out within 15 seconds."""
        now = datetime.now()
        for tx in reversed(account.transactions):
            if (now - tx["timestamp"]).total_seconds() > 15:
                break
            if tx["type"] == "Transfer Out" and tx["meta"]["recipient"] == recipient_id and tx["amount"] == amount:
                return True
        return False

    def _has_multiple_failed_pins(self, account: Account) -> bool:
        now = datetime.now()
        return len([t for t in account.failed_timestamps if (now - t).total_seconds() <= 180]) >= 3

    def _log_transaction(self, account: Account, tx_type: str, amount: float, status: str, 
                         reason: str = "", recipient: str = None, sender_id: str = None) -> None:
        account.transactions.append({
            "timestamp": datetime.now(), "type": tx_type, "amount": amount, "status": status,
            "flag_reason": reason, "meta": {"recipient": recipient, "sender_id": sender_id}
        })
