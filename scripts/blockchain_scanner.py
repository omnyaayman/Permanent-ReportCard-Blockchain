import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from collections import Counter

from utils import (
    get_contracts,
    process_event,
    format_coin,
    save_json,
    has_event,
    OUTPUTS_DIR,
    ZERO_ADDRESS
)


def decode_action(contract, tx_input, contract_name):
    try:
        function_called, function_args = contract.decode_function_input(tx_input)
        return f"{contract_name}: {function_called.fn_name}", str(function_args)
    except Exception:
        return f"{contract_name}: Interaction", "Could not decode input"


def main():
    w3, ganache_url, report, coin, report_address, coin_address, admin, data = get_contracts()

    latest_block = w3.eth.block_number

    active_users = Counter()
    transactions = []
    coin_events = []
    grade_events = []

    print("=" * 70)
    print("BLOCKCHAIN SCANNER")
    print("=" * 70)
    print("Connected to Ganache:", ganache_url)
    print("Latest Block:", latest_block)
    print("ReportCard:", report_address)
    print("GradeCoin:", coin_address)
    print("-" * 70)

    for block_number in range(latest_block + 1):
        block = w3.eth.get_block(block_number, full_transactions=True)

        for tx in block.transactions:
            receipt = w3.eth.get_transaction_receipt(tx["hash"])

            tx_hash = tx["hash"].hex()
            tx_from = tx["from"]
            tx_to = tx["to"]

            # Contract deployment
            if receipt.get("contractAddress"):
                created = receipt["contractAddress"]

                if created and created.lower() in [
                    report_address.lower(),
                    coin_address.lower()
                ]:
                    active_users[tx_from] += 1

                    transactions.append({
                        "block": block_number,
                        "tx_hash": tx_hash,
                        "from": tx_from,
                        "action": "Contract Deployment",
                        "status": receipt.status
                    })

            # Contract interaction
            if tx_to:
                if tx_to.lower() == report_address.lower():
                    active_users[tx_from] += 1
                    action, value = decode_action(report, tx["input"], "ReportCard")

                    transactions.append({
                        "block": block_number,
                        "tx_hash": tx_hash,
                        "from": tx_from,
                        "action": action,
                        "value": value,
                        "status": receipt.status
                    })

                elif tx_to.lower() == coin_address.lower():
                    active_users[tx_from] += 1
                    action, value = decode_action(coin, tx["input"], "GradeCoin")

                    transactions.append({
                        "block": block_number,
                        "tx_hash": tx_hash,
                        "from": tx_from,
                        "action": action,
                        "value": value,
                        "status": receipt.status
                    })

            # ReportCard grade events (additions and updates)
            for event_name in ("GradeAdded", "GradeUpdated"):
                if not has_event(report, event_name):
                    continue

                try:
                    for event in process_event(
                        getattr(report.events, event_name)(),
                        receipt
                    ):
                        grade_events.append({
                            "block": block_number,
                            "tx_hash": tx_hash,
                            "event": event_name,
                            "student": event["args"]["student"],
                            "grade": event["args"]["grade"]
                        })
                except Exception:
                    pass

            # GradeCoin Transfer events
            transfer_events = process_event(
                coin.events.Transfer(),
                receipt
            )

            for event in transfer_events:
                if event["address"].lower() != coin_address.lower():
                    continue

                sender = event["args"]["from"]
                receiver = event["args"]["to"]
                amount = event["args"]["value"]

                if sender.lower() == ZERO_ADDRESS.lower():
                    event_type = "Mint GradeCoin"
                else:
                    event_type = "Transfer GradeCoin"

                coin_events.append({
                    "block": block_number,
                    "tx_hash": tx_hash,
                    "event": event_type,
                    "from": sender,
                    "to": receiver,
                    "amount_grc": format_coin(w3, amount)
                })

    print("Scanned Contract Transactions:")
    print("-" * 70)

    for item in transactions:
        print(
            f"Block {item['block']} | "
            f"From: {item['from']} | "
            f"Action: {item['action']} | "
            f"Status: {item['status']}"
        )

    print("-" * 70)
    print("Top Active Users:")

    for index, (address, count) in enumerate(active_users.most_common(3), start=1):
        print(f"{index}. {address} | Transactions: {count}")

    print("-" * 70)
    print("ReportCard Grade Events:")

    for event in grade_events:
        print(
            f"Block {event['block']} | "
            f"{event['event']} | "
            f"Student: {event['student']} | "
            f"Grade: {event['grade']}"
        )

    print("-" * 70)
    print("GradeCoin Events:")

    for event in coin_events:
        print(
            f"Block {event['block']} | "
            f"{event['event']} | "
            f"From: {event['from']} | "
            f"To: {event['to']} | "
            f"Amount: {event['amount_grc']} GRC"
        )

    result = {
        "ganache_url": ganache_url,
        "latest_block": latest_block,
        "report_card": report_address,
        "grade_coin": coin_address,
        "total_transactions": len(transactions),
        "top_active_users": [
            {
                "address": address,
                "transactions": count
            }
            for address, count in active_users.most_common(3)
        ],
        "transactions": transactions,
        "grade_coin_events": coin_events,
        "report_card_grade_events": grade_events
    }

    output_file = OUTPUTS_DIR / "blockchain_scan_result.json"
    save_json(output_file, result)

    print("-" * 70)
    print("Blockchain scan result saved to:", output_file)
    print("=" * 70)


if __name__ == "__main__":
    main()