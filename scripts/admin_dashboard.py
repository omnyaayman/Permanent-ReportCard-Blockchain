import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from collections import Counter

from utils import (
    get_contracts,
    get_fake_students,
    get_grade,
    get_coin_balance,
    format_coin,
    save_json,
    OUTPUTS_DIR
)


def main():
    w3, ganache_url, report, coin, report_address, coin_address, admin, data = get_contracts()

    students = get_fake_students(data)
    total_minted = coin.functions.totalMinted().call()

    active_users = Counter()

    latest_block = w3.eth.block_number

    for block_number in range(latest_block + 1):
        block = w3.eth.get_block(block_number, full_transactions=True)

        for tx in block.transactions:
            tx_to = tx["to"]

            if tx_to is None:
                continue

            if tx_to.lower() in [report_address.lower(), coin_address.lower()]:
                active_users[tx["from"]] += 1

    print("=" * 70)
    print("ADMIN DASHBOARD")
    print("=" * 70)

    print("Connected to Ganache:", ganache_url)
    print("Latest block:", latest_block)
    print("ReportCard Contract:", report_address)
    print("GradeCoin Contract:", coin_address)
    print("Admin:", admin)

    print("-" * 70)
    print("Total student grades stored:", len(students))
    print("Total minted coins:", format_coin(w3, total_minted), "GRC")
    print("Total contract transactions:", sum(active_users.values()))

    print("-" * 70)
    print("Students:")

    students_output = []

    for index, student in enumerate(students, start=1):
        address = student["address"]
        grade = get_grade(report, address)
        balance = get_coin_balance(w3, coin, address)

        print(f"{index}. {address} | Grade: {grade} | Balance: {balance} GRC")

        students_output.append({
            "address": address,
            "grade": grade,
            "balance_grc": balance
        })

    print("-" * 70)
    print("Top 3 active users:")

    top_users = active_users.most_common(3)

    for index, (address, count) in enumerate(top_users, start=1):
        print(f"{index}. {address} | Transactions: {count}")

    result = {
        "network": {
            "ganache_url": ganache_url,
            "latest_block": latest_block
        },
        "contracts": {
            "ReportCard": report_address,
            "GradeCoin": coin_address
        },
        "admin": admin,
        "total_students": len(students),
        "total_minted_grc": format_coin(w3, total_minted),
        "total_transactions": sum(active_users.values()),
        "top_active_users": [
            {
                "address": address,
                "transactions": count
            }
            for address, count in top_users
        ],
        "students": students_output
    }

    output_file = OUTPUTS_DIR / "admin_dashboard_scan_result.json"
    save_json(output_file, result)

    print("-" * 70)
    print("Dashboard result saved to:", output_file)
    print("=" * 70)


if __name__ == "__main__":
    main()