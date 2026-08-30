"""Smart contract validation tests.

These tests compile the Solidity contracts and inspect their ABI and source
for the expected structure, events, functions and access-control patterns.

They do NOT require a live blockchain - they validate that the contract is
well-formed and enforces the intended rules at the source level.

Run with:  python -m unittest discover -s tests
"""

import sys
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT))

from solcx import compile_standard, install_solc  # noqa: E402
from config import SOLC_VERSION, REPORT_CARD_SOL, GRADE_COIN_SOL  # noqa: E402


def compile_contracts():
    install_solc(SOLC_VERSION)

    sources = {
        REPORT_CARD_SOL.name: {
            "content": REPORT_CARD_SOL.read_text(encoding="utf-8")
        },
        GRADE_COIN_SOL.name: {
            "content": GRADE_COIN_SOL.read_text(encoding="utf-8")
        },
    }

    compiled = compile_standard(
        {
            "language": "Solidity",
            "sources": sources,
            "settings": {
                "outputSelection": {
                    "*": {"*": ["abi", "evm.bytecode"]}
                }
            },
        },
        solc_version=SOLC_VERSION,
    )

    return compiled


class ReportCardContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiled = compile_contracts()
        cls.abi = cls.compiled["contracts"][REPORT_CARD_SOL.name]["ReportCard"]["abi"]
        cls.source = REPORT_CARD_SOL.read_text(encoding="utf-8")

    def _event_names(self):
        return [
            e["name"] for e in self.abi
            if e.get("type") == "event"
        ]

    def _function_names(self):
        return [
            f["name"] for f in self.abi
            if f.get("type") == "function"
        ]

    def test_compiles(self):
        self.assertIn("abi", self.compiled["contracts"][REPORT_CARD_SOL.name]["ReportCard"])
        self.assertIn("evm", self.compiled["contracts"][REPORT_CARD_SOL.name]["ReportCard"])

    def test_grade_events_exist(self):
        events = self._event_names()
        self.assertIn("GradeAdded", events)
        self.assertIn("GradeUpdated", events)

    def test_core_events_exist(self):
        events = self._event_names()
        self.assertIn("UserRegistered", events)
        self.assertIn("OwnershipTransferred", events)
        self.assertIn("ContractPaused", events)
        self.assertIn("ContractResumed", events)

    def test_core_functions_exist(self):
        fns = self._function_names()
        for name in (
            "setGrade",
            "setMultipleGrades",
            "getGrade",
            "getTotalStudents",
            "transferOwnership",
            "pause",
            "resume",
            "registerUser",
            "isUserRegistered",
        ):
            self.assertIn(name, fns, f"Missing function {name}")

    def test_only_owner_modifier_on_admin_functions(self):
        # setGrade / pause / resume / transferOwnership must be admin-gated.
        for fn in ("setGrade", "setMultipleGrades", "pause", "resume", "transferOwnership"):
            self.assertTrue(
                re.search(
                    rf"function {fn}\b.*?\)\s+public\s+onlyOwner\b",
                    self.source,
                    flags=re.DOTALL,
                ),
                f"{fn} should be gated by onlyOwner",
            )

    def test_grade_bounds_validated(self):
        self.assertIn("grade <= 100", self.source)

    def test_zero_address_rejected(self):
        self.assertIn("address(0)", self.source)

    def test_pause_guard_used(self):
        self.assertIn("whenNotPaused", self.source)


class GradeCoinContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiled = compile_contracts()
        cls.abi = cls.compiled["contracts"][GRADE_COIN_SOL.name]["GradeCoin"]["abi"]
        cls.source = GRADE_COIN_SOL.read_text(encoding="utf-8")

    def test_compiles(self):
        self.assertIn("abi", self.compiled["contracts"][GRADE_COIN_SOL.name]["GradeCoin"])

    def test_erc20_functions(self):
        fns = [
            f["name"] for f in self.abi
            if f.get("type") == "function"
        ]
        for name in ("mint", "transfer", "transferFrom", "balanceOf", "approve"):
            self.assertIn(name, fns, f"Missing GradeCoin function {name}")

    def test_mint_is_admin_gated(self):
        self.assertRegex(self.source, r"function mint\(.*\) public onlyOwner")

    def test_transfer_events(self):
        events = [e["name"] for e in self.abi if e.get("type") == "event"]
        self.assertIn("Transfer", events)
        self.assertIn("Approval", events)

    def test_zero_address_rejected(self):
        self.assertIn("address(0)", self.source)


if __name__ == "__main__":
    unittest.main()
