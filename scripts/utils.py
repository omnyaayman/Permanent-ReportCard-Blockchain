"""Shared helpers used across the project scripts.

Everything that needs blockchain state (balances, grades, transactions) is
centralised here so the individual scripts stay small and consistent.
"""

from pathlib import Path
import json
from decimal import Decimal

from web3 import Web3
from web3.logs import DISCARD

from config import connect_to_ganache, EXPLORER_URL


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = ROOT / "outputs"

DEPLOYMENT_FILE = OUTPUTS_DIR / "deployed_contracts.json"
REPORT_ABI_FILE = OUTPUTS_DIR / "ReportCard_abi.json"
COIN_ABI_FILE = OUTPUTS_DIR / "GradeCoin_abi.json"

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


# ==============================
# JSON helpers
# ==============================

def load_json(path):
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, data):
    Path(path).write_text(
        json.dumps(data, indent=4, default=str),
        encoding="utf-8"
    )


# ==============================
# Transaction helpers
# ==============================

def wait_tx(w3, tx_hash, action_name="Transaction"):
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status != 1:
        raise RuntimeError(f"{action_name} failed")

    return receipt


# ==============================
# Contract helpers
# ==============================

def get_contracts():
    data = load_json(DEPLOYMENT_FILE)
    report_abi = load_json(REPORT_ABI_FILE)
    coin_abi = load_json(COIN_ABI_FILE)

    w3, ganache_url = connect_to_ganache()

    report_address = Web3.to_checksum_address(
        data["contracts"]["report_card"]["address"]
    )

    coin_address = Web3.to_checksum_address(
        data["contracts"]["grade_coin"]["address"]
    )

    report = w3.eth.contract(
        address=report_address,
        abi=report_abi
    )

    coin = w3.eth.contract(
        address=coin_address,
        abi=coin_abi
    )

    admin = Web3.to_checksum_address(data["admin"])

    return w3, ganache_url, report, coin, report_address, coin_address, admin, data


def has_function(contract, function_name):
    return any(
        item.get("type") == "function" and item.get("name") == function_name
        for item in contract.abi
    )


def get_grade(report, student_address):
    student_address = Web3.to_checksum_address(student_address)

    if has_function(report, "getGrade"):
        result = report.functions.getGrade(student_address).call()

        if isinstance(result, (list, tuple)):
            return result[-1]

        return result

    result = report.functions.grades(student_address).call()

    if isinstance(result, (list, tuple)):
        return result[0]

    return result


# ==============================
# Balance helpers
# ==============================

def format_coin(w3, amount_raw):
    amount = Decimal(w3.from_wei(amount_raw, "ether"))

    if amount == amount.to_integral_value():
        return str(int(amount))

    return format(amount, "f").rstrip("0").rstrip(".")


def get_coin_balance(w3, coin, address):
    address = Web3.to_checksum_address(address)
    balance_raw = coin.functions.balanceOf(address).call()
    return format_coin(w3, balance_raw)


def get_eth_balance(w3, address):
    address = Web3.to_checksum_address(address)
    return w3.from_wei(w3.eth.get_balance(address), "ether")


# ==============================
# Events / decoding
# ==============================

def process_event(event_builder, receipt):
    """Process a receipt with an event builder (handles web3 API variants)."""
    try:
        return event_builder.process_receipt(receipt, errors=DISCARD)
    except AttributeError:
        return event_builder.processReceipt(receipt, errors=DISCARD)


def decode_contract_action(tx, report_address, coin_address, report, coin):
    """Decode a raw transaction input into a human readable (action, value)."""
    tx_to = tx["to"]

    if tx_to is None:
        return "Contract Deployment", ""

    if tx_to.lower() == report_address.lower():
        try:
            fn, args = report.decode_function_input(tx["input"])
            return "ReportCard: " + fn.fn_name, str(args)
        except Exception:
            return "ReportCard Interaction", ""

    if tx_to.lower() == coin_address.lower():
        try:
            fn, args = coin.decode_function_input(tx["input"])
            return "GradeCoin: " + fn.fn_name, str(args)
        except Exception:
            return "GradeCoin Interaction", ""

    return "Sent Transaction", ""


# ==============================
# Activity history
# ==============================

def get_user_activity(
    w3,
    report,
    coin,
    report_address,
    coin_address,
    user_address
):
    """Return the on-chain activity list for a single address.

    Scans every block transaction and decodes contract calls, transfers and
    relevant events for the given user. This is intentionally thorough so the
    demo reflects real, verified blockchain data.
    """
    user_address = Web3.to_checksum_address(user_address)

    activities = []
    latest_block = w3.eth.block_number

    for block_number in range(latest_block + 1):
        block = w3.eth.get_block(block_number, full_transactions=True)

        for tx in block.transactions:
            receipt = w3.eth.get_transaction_receipt(tx["hash"])

            tx_hash = tx["hash"].hex()
            tx_from = tx["from"]
            tx_to = tx["to"]

            # Transactions sent by the user
            if tx_from.lower() == user_address.lower():
                action, value = decode_contract_action(
                    tx, report_address, coin_address, report, coin
                )
                activities.append({
                    "Block": block_number,
                    "Action": action,
                    "Value": value,
                    "Tx": tx_hash
                })

            # ETH received by the user
            if tx_to and tx_to.lower() == user_address.lower() and tx["value"] > 0:
                activities.append({
                    "Block": block_number,
                    "Action": "Received ETH",
                    "Value": str(w3.from_wei(tx["value"], "ether")) + " ETH",
                    "Tx": tx_hash
                })

            # GradeUpdated / GradeAdded events for this user
            for event_name in ("GradeUpdated", "GradeAdded"):
                if not has_event(report, event_name):
                    continue

                try:
                    event_builder = getattr(report.events, event_name)()
                    events = process_event(event_builder, receipt)

                    for event in events:
                        student = event["args"]["student"]
                        grade = event["args"]["grade"]

                        if student.lower() == user_address.lower():
                            activities.append({
                                "Block": block_number,
                                "Action": "Grade " + (
                                    "Added" if event_name == "GradeAdded"
                                    else "Updated"
                                ),
                                "Value": f"New grade: {grade}",
                                "Tx": tx_hash
                            })
                except Exception:
                    pass

            # GradeCoin Transfer events involving this user
            try:
                transfer_events = process_event(
                    coin.events.Transfer(),
                    receipt
                )

                for event in transfer_events:
                    if event["address"].lower() != coin_address.lower():
                        continue

                    sender = event["args"]["from"]
                    receiver = event["args"]["to"]
                    amount = format_coin(w3, event["args"]["value"])

                    if sender.lower() == user_address.lower():
                        activities.append({
                            "Block": block_number,
                            "Action": "Sent GradeCoin",
                            "Value": f"{amount} GRC to {receiver}",
                            "Tx": tx_hash
                        })

                    if receiver.lower() == user_address.lower():
                        if sender.lower() == ZERO_ADDRESS.lower():
                            action = "Minted GradeCoin"
                            value = f"{amount} GRC"
                        else:
                            action = "Received GradeCoin"
                            value = f"{amount} GRC from {sender}"

                        activities.append({
                            "Block": block_number,
                            "Action": action,
                            "Value": value,
                            "Tx": tx_hash
                        })
            except Exception:
                pass

    return activities


def has_event(contract, event_name):
    return any(
        item.get("type") == "event" and item.get("name") == event_name
        for item in contract.abi
    )


# ==============================
# Misc
# ==============================

def explorer_tx_url(tx_hash):
    """Build an explorer link for a transaction hash, if configured."""
    if not EXPLORER_URL:
        return None

    return f"{EXPLORER_URL}/tx/{tx_hash}"


def get_fake_students(data):
    return data.get("fake_students_for_testing", [])
