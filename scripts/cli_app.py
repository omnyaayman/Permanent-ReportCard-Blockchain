import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from web3 import Web3

from config import ADMIN_PASSWORD
from utils import (
    get_contracts,
    get_grade,
    get_coin_balance,
    get_eth_balance,
    wait_tx,
    has_function,
    get_user_activity
)


# ==============================
# Load Contracts
# ==============================

w3, ganache_url, report, coin, report_address, coin_address, admin, data = get_contracts()

print("Connected to Ganache:", ganache_url)
print("ReportCard:", report_address)
print("GradeCoin:", coin_address)
print("Admin:", admin)


# ==============================
# Main Menu
# ==============================

def main_menu():
    while True:
        print("\n===== MAIN MENU =====")
        print("1. User Menu")
        print("2. Admin Menu")
        print("3. Exit")

        choice = input("Choose option: ").strip()

        if choice == "1":
            user_menu()

        elif choice == "2":
            if not ADMIN_PASSWORD:
                print("Admin password is not configured. Set ADMIN_PASSWORD in your .env file.")
                continue

            password = input("Enter admin password: ").strip()

            if password == ADMIN_PASSWORD:
                admin_menu()
            else:
                print("Wrong password")

        elif choice == "3":
            print("Goodbye")
            break

        else:
            print("Invalid choice")


# ==============================
# User Menu
# ==============================

def user_menu():
    while True:
        print("\n--- USER MENU ---")
        print("1. Register User")
        print("2. View Profile")
        print("3. View Grade")
        print("4. Check ETH + GradeCoin Balance")
        print("5. Personal Activity History")
        print("6. Back")

        choice = input("Choose: ").strip()

        if choice == "1":
            register_user()

        elif choice == "2":
            view_profile()

        elif choice == "3":
            view_grade()

        elif choice == "4":
            check_balances()

        elif choice == "5":
            personal_activity_history()

        elif choice == "6":
            break

        else:
            print("Invalid choice")


# ==============================
# Admin Menu
# ==============================

def admin_menu():
    while True:
        print("\n--- ADMIN MENU ---")
        print("1. Add / Update Grade")
        print("2. Mint GradeCoins")
        print("3. Pause Contract")
        print("4. Resume Contract")
        print("5. Back")

        choice = input("Choose: ").strip()

        if choice == "1":
            set_grade()

        elif choice == "2":
            mint_grade_coins()

        elif choice == "3":
            pause_contract()

        elif choice == "4":
            resume_contract()

        elif choice == "5":
            break

        else:
            print("Invalid choice")


# ==============================
# Helper Functions
# ==============================

def to_checksum(address):
    return Web3.to_checksum_address(address)


def address_in_ganache(address):
    address = to_checksum(address)

    ganache_accounts = [
        to_checksum(account)
        for account in w3.eth.accounts
    ]

    return address in ganache_accounts


# ==============================
# User Functions
# ==============================

def register_user():
    try:
        if not has_function(report, "registerUser"):
            print("Register User is not supported by this contract.")
            return

        user_address = input("Enter your address: ").strip()
        user_address = to_checksum(user_address)

        if not address_in_ganache(user_address):
            print("Error: This address is not found in current Ganache accounts.")
            print("Use an address from the current Ganache workspace.")
            return

        if user_address.lower() == admin.lower():
            print("This is the admin address. Please use a student/user address.")
            return

        name = input("Enter your name: ").strip()

        if name == "":
            print("Name cannot be empty.")
            return

        if has_function(report, "isUserRegistered"):
            is_registered = report.functions.isUserRegistered(user_address).call()

            if is_registered:
                current_name = report.functions.getUserName(user_address).call()

                print("\nUser already registered.")
                print("Address:", user_address)
                print("Name:", current_name)
                return

        tx = report.functions.registerUser(name).transact({
            "from": user_address
        })

        wait_tx(w3, tx, "Register user")

        print("\nUser registered successfully")
        print("Address:", user_address)
        print("Name:", name)
        print("Transaction:", tx.hex())

    except Exception as e:
        print("Error:", e)


def view_profile():
    try:
        if not has_function(report, "isUserRegistered"):
            print("User Profile is not supported by this contract.")
            return

        user_address = input("Enter user address: ").strip()
        user_address = to_checksum(user_address)

        is_registered = report.functions.isUserRegistered(user_address).call()

        if not is_registered:
            print("This user is not registered.")
            return

        name = report.functions.getUserName(user_address).call()

        print("\n===== USER PROFILE =====")
        print("Address:", user_address)
        print("Name:", name)

    except Exception as e:
        print("Error:", e)


def view_grade():
    try:
        student = input("Enter student address: ").strip()
        student = to_checksum(student)

        grade = get_grade(report, student)

        print("\n===== STUDENT GRADE =====")
        print("Student:", student)
        print("Grade:", grade)

    except Exception as e:
        print("Error:", e)


def check_balances():
    try:
        address = input("Enter address: ").strip()
        address = to_checksum(address)

        eth_balance = get_eth_balance(w3, address)
        coin_balance = get_coin_balance(w3, coin, address)

        print("\n===== BALANCE CHECKER =====")
        print("Address:", address)
        print("ETH Balance:", eth_balance, "ETH")
        print("GradeCoin Balance:", coin_balance, "GRC")

    except Exception as e:
        print("Error:", e)


def personal_activity_history():
    try:
        user_address = input("Enter user address: ").strip()
        user_address = to_checksum(user_address)

        activities = get_user_activity(
            w3,
            report,
            coin,
            report_address,
            coin_address,
            user_address
        )

        print("\n===== PERSONAL ACTIVITY HISTORY =====")
        print("Address:", user_address)
        print("-" * 80)

        if len(activities) == 0:
            print("No activity found for this address.")
            return

        for item in activities:
            print("Block :", item["Block"])
            print("Action:", item["Action"])
            print("Value :", item["Value"])
            print("Tx    :", item["Tx"])
            print("-" * 80)

    except Exception as e:
        print("Error:", e)


# ==============================
# Admin Functions
# ==============================

def set_grade():
    try:
        student = input("Enter student address: ").strip()
        student = to_checksum(student)

        grade = int(input("Enter grade 0-100: ").strip())

        if grade < 0 or grade > 100:
            print("Invalid grade. Grade must be between 0 and 100.")
            return

        tx = report.functions.setGrade(student, grade).transact({
            "from": admin
        })

        wait_tx(w3, tx, "Set grade")

        print("\nGrade saved successfully")
        print("Student:", student)
        print("Grade:", grade)
        print("Transaction:", tx.hex())

    except Exception as e:
        print("Error:", e)


def mint_grade_coins():
    try:
        receiver = input("Enter receiver address: ").strip()
        receiver = to_checksum(receiver)

        amount = int(input("Enter amount in GRC: ").strip())

        if amount <= 0:
            print("Amount must be greater than zero.")
            return

        tx = coin.functions.mint(receiver, amount).transact({
            "from": admin
        })

        wait_tx(w3, tx, "Mint GradeCoins")

        print("\nGradeCoins minted successfully")
        print("Receiver:", receiver)
        print("Amount:", amount, "GRC")
        print("Transaction:", tx.hex())

    except Exception as e:
        print("Error:", e)


def pause_contract():
    try:
        tx = report.functions.pause().transact({
            "from": admin
        })

        wait_tx(w3, tx, "Pause contract")

        print("\nContract paused successfully")
        print("Transaction:", tx.hex())

    except Exception as e:
        print("Error:", e)


def resume_contract():
    try:
        tx = report.functions.resume().transact({
            "from": admin
        })

        wait_tx(w3, tx, "Resume contract")

        print("\nContract resumed successfully")
        print("Transaction:", tx.hex())

    except Exception as e:
        print("Error:", e)


# ==============================
# Run App
# ==============================

if __name__ == "__main__":
    main_menu()