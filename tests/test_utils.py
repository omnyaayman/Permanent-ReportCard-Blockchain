"""Unit tests for pure Python helper logic.

These tests run without a live blockchain. They validate the shared helper
functions in ``scripts/utils.py`` and the configuration loading.

Run with:  python -m unittest discover -s tests
"""

import sys
import json
import os
import unittest
from pathlib import Path

# Allow importing scripts/ modules from the project root.
ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT))

from utils import (  # noqa: E402
    format_coin,
    has_function,
    has_event,
    decode_contract_action,
    ZERO_ADDRESS,
)
from config import (  # noqa: E402
    GANACHE_URLS,
    BASE_DIR,
    REPORT_CARD_SOL,
    GRADE_COIN_SOL,
    OUTPUTS_DIR,
)


# A Web3 instance for pure conversions (from_wei needs no live connection).
from web3 import Web3  # noqa: E402
W3 = Web3()


# Minimal mock contract ABIs used to test the ABI-introspection helpers.
REPORT_ABI = [
    {"type": "function", "name": "setGrade", "stateMutability": "nonpayable"},
    {"type": "function", "name": "getGrade", "stateMutability": "view"},
    {"type": "event", "name": "GradeAdded"},
    {"type": "event", "name": "GradeUpdated"},
]

COIN_ABI = [
    {"type": "function", "name": "mint", "stateMutability": "nonpayable"},
    {"type": "event", "name": "Transfer"},
]


class MockContract:
    def __init__(self, abi):
        self.abi = abi

    def decode_function_input(self, data):
        # Return (MockFn, args) where MockFn has .fn_name
        class MockFn:
            fn_name = "setGrade"

        return MockFn(), {"student": "0xabc"}


class FormatCoinTests(unittest.TestCase):
    def test_whole_number(self):
        # 1000000000000000000 wei => 1 ether
        self.assertEqual(format_coin(W3, 10 ** 18), "1")

    def test_multiple_whole(self):
        self.assertEqual(format_coin(W3, 10 * 10 ** 18), "10")

    def test_decimal(self):
        # 1500000000000000000 wei => 1.5
        self.assertEqual(format_coin(W3, 1500000000000000000), "1.5")

    def test_small_decimal(self):
        # 1050000000000000000 wei => 1.05
        self.assertEqual(format_coin(W3, 1050000000000000000), "1.05")

    def test_zero(self):
        self.assertEqual(format_coin(W3, 0), "0")


class FunctionAndEventHelpersTests(unittest.TestCase):
    def setUp(self):
        self.report = MockContract(REPORT_ABI)
        self.coin = MockContract(COIN_ABI)

    def test_has_function_positive(self):
        self.assertTrue(has_function(self.report, "setGrade"))

    def test_has_function_negative(self):
        self.assertFalse(has_function(self.report, "doesNotExist"))

    def test_has_event_positive(self):
        self.assertTrue(has_event(self.report, "GradeAdded"))

    def test_has_event_negative(self):
        self.assertFalse(has_event(self.report, "Nope"))

    def test_decode_deployment(self):
        tx = {"to": None, "input": "0x"}
        action, value = decode_contract_action(tx, "0xrep", "0xcoin", self.report, self.coin)
        self.assertEqual(action, "Contract Deployment")

    def test_decode_report_interaction(self):
        tx = {"to": "0xREP", "input": "0xdeadbeef"}
        action, _ = decode_contract_action(tx, "0xREP", "0xcoin", self.report, self.coin)
        self.assertTrue(action.startswith("ReportCard:"))

    def test_decode_coin_interaction(self):
        tx = {"to": "0xCOIN", "input": "0xdeadbeef"}
        action, _ = decode_contract_action(tx, "0xrep", "0xCOIN", self.report, self.coin)
        self.assertTrue(action.startswith("GradeCoin:"))

    def test_decode_unknown(self):
        tx = {"to": "0x1234", "input": "0x"}
        action, _ = decode_contract_action(tx, "0xrep", "0xcoin", self.report, self.coin)
        self.assertEqual(action, "Sent Transaction")


class ZeroAddressConstantTests(unittest.TestCase):
    def test_zero_address_is_40_hex_chars(self):
        self.assertEqual(len(ZERO_ADDRESS), 42)
        self.assertTrue(ZERO_ADDRESS.lower().startswith("0x"))


class ConfigTests(unittest.TestCase):
    def test_paths_exist(self):
        self.assertTrue(BASE_DIR.exists())
        self.assertTrue(REPORT_CARD_SOL.exists(), "ReportCard.sol should exist")
        self.assertTrue(GRADE_COIN_SOL.exists(), "GradeCoin contract file should exist")

    def test_grade_coin_sol_points_to_member2(self):
        # The GradeCoin contract lives in ReportCardMember2.sol.
        self.assertEqual(GRADE_COIN_SOL.name, "ReportCardMember2.sol")

    def test_outputs_dir_defined(self):
        self.assertEqual(OUTPUTS_DIR.name, "outputs")

    def test_default_ganache_urls(self):
        self.assertTrue(any("127.0.0.1" in url for url in GANACHE_URLS))


if __name__ == "__main__":
    unittest.main()
