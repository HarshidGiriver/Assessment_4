import time
from DigitalWallet import DigitalWallet

def run_wallet_demo():
    # Initialize the ecosystem
    wallet = DigitalWallet()
    
    print("=" * 60)
    print("          DIGITAL WALLET ENGINE SIMULATION ENVIRONMENT         ")
    print("=" * 60)

    # ----------------------------------------------------
    # 1. ACCOUNT CREATION
    # ----------------------------------------------------
    print("\n[STEP 1] Initializing System Accounts...")
    print(wallet.create_account(account_id="ACC101", pin="1234", name="Alice", daily_limit=10000.0))
    print(wallet.create_account(account_id="ACC102", pin="5678", name="Bob", daily_limit=50000.0))

    # ----------------------------------------------------
    # 2. DEPOSIT & BALANCE VERIFICATION
    # ----------------------------------------------------
    print("\n[STEP 2] Executing Core Deposits & Balance Inspections...")
    print(wallet.deposit(account_id="ACC101", amount=15000.0))
    print(wallet.verify_balance(account_id="ACC101", pin="1234"))

    # ----------------------------------------------------
    # 3. TRANSFER, WITHDRAWAL & LIMIT CONTROLS
    # ----------------------------------------------------
    print("\n[STEP 3] Testing Transfers, Withdrawals, and Daily Limit Boundaries...")
    # Legitimate transfer
    print(wallet.transfer(sender_id="ACC101", pin="1234", receiver_id="ACC102", amount=2000.0))
    # Exceeding the custom daily limit rule bound set at creation ($10,000 max spent rule)
    print(wallet.transfer(sender_id="ACC101", pin="1234", receiver_id="ACC102", amount=9000.0)) 

    # ----------------------------------------------------
    # 4. FRAUD: UNUSUAL & LARGE TRANSACTION VOLUMES
    # ----------------------------------------------------
    print("\n[STEP 4] Evaluating Fraud Detection: Size & Single Caps...")
    # Trigger Large Transaction rule: (>80% of Account Daily Limit capacity spent in 1 call)
    print(wallet.withdraw(account_id="ACC101", pin="1234", amount=8500.0))
    # Trigger Systemic Unusual Transaction static threshold ($100,000 threshold breach)
    print(wallet.deposit(account_id="ACC101", amount=125000.0))

    # ----------------------------------------------------
    # 5. FRAUD: MULTI-VELOCITY TRANSACTION BURST
    # ----------------------------------------------------
    print("\n[STEP 5] Evaluating Fraud Detection: Volumetric Burst Pipeline...")
    print("Processing 5 micro-deposits sequentially to strain security logs...")
    for i in range(5):
        wallet.deposit(account_id="ACC101", amount=10.0)
    
    # 6th action execution item inside the short rolling 10-minute analytics window
    print("Attempting 6th fast transaction action statement:")
    print(wallet.withdraw(account_id="ACC101", pin="1234", amount=5.0))

    # ----------------------------------------------------
    # 6. FRAUD: AUTOMATED BRUTE FORCE CHALLENGE LOCKOUT
    # ----------------------------------------------------
    print("\n[STEP 6] Evaluating Fraud Detection: Security Token Attacks...")
    print(wallet.verify_balance(account_id="ACC102", pin="9999"))  # Failed attempt 1
    print(wallet.verify_balance(account_id="ACC102", pin="8888"))  # Failed attempt 2
    print(wallet.verify_balance(account_id="ACC102", pin="7777"))  # Failed attempt 3 -> Triggers Freeze
    print(wallet.verify_balance(account_id="ACC102", pin="5678"))  # Blocked request evaluation

    # ----------------------------------------------------
    # 7. LEDGER AUDITING & LOG EXPORTS
    # ----------------------------------------------------
    print("\n[STEP 7] Generating Audit Trail Statement Export Ledger...")
    print(wallet.get_transaction_history(account_id="ACC101", pin="1234"))

    print("\n" + "=" * 60)
    print("                   SIMULATION COMPLETE                        ")
    print("=" * 60)

if __name__ == "__main__":
    run_wallet_demo()
