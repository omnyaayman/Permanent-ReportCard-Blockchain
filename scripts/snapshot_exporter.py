import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import csv

from utils import (
    get_contracts,
    get_coin_balance,
    get_eth_balance,
    save_json,
    OUTPUTS_DIR
)


def main():
    w3, ganache_url, report, coin, report_address, coin_address, admin, data = get_contracts()

    csv_file = OUTPUTS_DIR / "balance_snapshot.csv"
    json_file = OUTPUTS_DIR / "balance_snapshot.json"

    rows = []

    print("=" * 70)
    print("BALANCE SNAPSHOT EXPORTER")
    print("=" * 70)
    print("Connected to Ganache:", ganache_url)
    print("GradeCoin Contract:", coin_address)
    print("Accounts found:", len(w3.eth.accounts))
    print("-" * 70)

    for account in w3.eth.accounts:
        coin_balance = get_coin_balance(w3, coin, account)
        eth_balance = get_eth_balance(w3, account)

        rows.append({
            "account_address": account,
            "grade_coin_balance": coin_balance,
            "eth_balance": str(eth_balance)
        })

        print(f"{account} | {coin_balance} GRC | {eth_balance} ETH")

    with open(csv_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            "Account Address",
            "Grade Coin Balance",
            "ETH Balance"
        ])

        for row in rows:
            writer.writerow([
                row["account_address"],
                row["grade_coin_balance"],
                row["eth_balance"]
            ])

    save_json(json_file, {
        "ganache_url": ganache_url,
        "grade_coin_contract": coin_address,
        "accounts": rows
    })

    print("-" * 70)
    print("Balance snapshot exported successfully")
    print("CSV saved to:", csv_file)
    print("JSON saved to:", json_file)
    print("=" * 70)


if __name__ == "__main__":
    main()