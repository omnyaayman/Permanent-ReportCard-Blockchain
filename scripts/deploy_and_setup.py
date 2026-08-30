import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from web3 import Web3
from solcx import compile_standard, install_solc

from config import (
    connect_to_ganache,
    SOLC_VERSION,
    FIXED_ADMIN_ADDRESS,
    REPORT_CARD_SOL,
    GRADE_COIN_SOL
)
from utils import save_json, wait_tx, OUTPUTS_DIR


REPORT_FILE = REPORT_CARD_SOL.name
COIN_FILE = GRADE_COIN_SOL.name

REPORT_CONTRACT = "ReportCard"
COIN_CONTRACT = "GradeCoin"


def compile_contracts():
    install_solc(SOLC_VERSION)

    sources = {
        REPORT_FILE: {
            "content": REPORT_CARD_SOL.read_text(encoding="utf-8")
        },
        COIN_FILE: {
            "content": GRADE_COIN_SOL.read_text(encoding="utf-8")
        }
    }

    compiled = compile_standard(
        {
            "language": "Solidity",
            "sources": sources,
            "settings": {
                "outputSelection": {
                    "*": {
                        "*": ["abi", "evm.bytecode"]
                    }
                }
            }
        },
        solc_version=SOLC_VERSION
    )

    report = compiled["contracts"][REPORT_FILE][REPORT_CONTRACT]
    coin = compiled["contracts"][COIN_FILE][COIN_CONTRACT]

    return report, coin


def deploy_contract(w3, abi, bytecode, admin):
    contract = w3.eth.contract(
        abi=abi,
        bytecode=bytecode
    )

    tx_hash = contract.constructor().transact({
        "from": admin
    })

    receipt = wait_tx(w3, tx_hash, "Deploy contract")

    return receipt.contractAddress, tx_hash.hex()


def main():
    w3, ganache_url = connect_to_ganache()

    accounts = w3.eth.accounts

    if len(accounts) < 6:
        raise RuntimeError("Ganache must have at least 6 accounts.")

    if not FIXED_ADMIN_ADDRESS:
        raise RuntimeError(
            "No admin address configured. Set ADMIN_ADDRESS in your .env file "
            "to one of the accounts in your running Ganache workspace."
        )

    # Fixed admin
    admin = Web3.to_checksum_address(FIXED_ADMIN_ADDRESS)

    ganache_accounts = [
        Web3.to_checksum_address(account)
        for account in accounts
    ]

    if admin not in ganache_accounts:
        raise RuntimeError(
            f"Admin address {admin} is not found in Ganache accounts. "
            "Open the correct Ganache workspace or set ADMIN_ADDRESS in .env."
        )

    students = [
        account for account in ganache_accounts
        if account.lower() != admin.lower()
    ][:4]

    grades = [90, 85, 95, 80]

    coin_amount = 10
    transfer_amount = 1

    print("=" * 60)
    print("AUTO SETUP SCRIPT")
    print("=" * 60)
    print("Connected to Ganache:", ganache_url)
    print("Fixed Admin:", admin)
    print("-" * 60)

    report_compiled, coin_compiled = compile_contracts()

    print("Contracts compiled successfully")

    report_abi = report_compiled["abi"]
    report_bytecode = report_compiled["evm"]["bytecode"]["object"]

    coin_abi = coin_compiled["abi"]
    coin_bytecode = coin_compiled["evm"]["bytecode"]["object"]

    report_address, report_deploy_tx = deploy_contract(
        w3,
        report_abi,
        report_bytecode,
        admin
    )

    coin_address, coin_deploy_tx = deploy_contract(
        w3,
        coin_abi,
        coin_bytecode,
        admin
    )

    print("ReportCard deployed at:", report_address)
    print("GradeCoin deployed at:", coin_address)
    print("-" * 60)

    report = w3.eth.contract(
        address=Web3.to_checksum_address(report_address),
        abi=report_abi
    )

    coin = w3.eth.contract(
        address=Web3.to_checksum_address(coin_address),
        abi=coin_abi
    )

    batch_tx = report.functions.setMultipleGrades(
        students,
        grades
    ).transact({
        "from": admin
    })

    wait_tx(w3, batch_tx, "Set multiple grades")

    print("Fake student grades added")

    mint_txs = []

    for student in students:
        tx = coin.functions.mint(
            student,
            coin_amount
        ).transact({
            "from": admin
        })

        wait_tx(w3, tx, "Mint GradeCoin")
        mint_txs.append(tx.hex())

    print("GradeCoins minted for fake students")

    fake_transfers = [
        (students[0], students[1]),
        (students[0], students[2]),
        (students[1], students[2]),
        (students[2], students[3]),
        (students[3], students[0]),
    ]

    transfer_txs = []

    for sender, receiver in fake_transfers:
        tx = coin.functions.transfer(
            receiver,
            transfer_amount
        ).transact({
            "from": sender
        })

        wait_tx(w3, tx, "Transfer GradeCoin")
        transfer_txs.append(tx.hex())

    print("Fake user activity transactions added")

    addresses = {
        "ReportCard": report_address,
        "GradeCoin": coin_address,
        "report_card": report_address,
        "grade_coin": coin_address
    }

    deployment_data = {
        "network": {
            "name": "Ganache",
            "url": ganache_url,
            "chain_id": w3.eth.chain_id,
            "latest_block": w3.eth.block_number
        },
        "admin": admin,
        "contracts": {
            "report_card": {
                "name": "ReportCard",
                "address": report_address,
                "deploy_tx": report_deploy_tx
            },
            "grade_coin": {
                "name": "GradeCoin",
                "address": coin_address,
                "deploy_tx": coin_deploy_tx
            }
        },
        "setup_transactions": {
            "batch_grades_tx": batch_tx.hex(),
            "mint_txs": mint_txs,
            "fake_activity_txs": transfer_txs
        },
        "fake_students_for_testing": [
            {
                "address": student,
                "grade": grade,
                "minted_coins": "10 GRC"
            }
            for student, grade in zip(students, grades)
        ]
    }

    save_json(OUTPUTS_DIR / "contract_addresses.json", addresses)
    save_json(OUTPUTS_DIR / "deployed_contracts.json", deployment_data)
    save_json(OUTPUTS_DIR / "ReportCard_abi.json", report_abi)
    save_json(OUTPUTS_DIR / "GradeCoin_abi.json", coin_abi)

    print("-" * 60)
    print("Files saved in outputs folder")
    print("Auto-Setup finished successfully")
    print("=" * 60)


if __name__ == "__main__":
    main()