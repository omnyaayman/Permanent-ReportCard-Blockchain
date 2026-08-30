import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils import get_contracts, wait_tx, save_json, OUTPUTS_DIR, has_function


def expect_revert(test_name, action):
    try:
        action()
        print("FAILED TEST:", test_name)
        return False
    except Exception:
        print("PASSED TEST:", test_name)
        return True


def expect_success(test_name, action):
    try:
        action()
        print("PASSED TEST:", test_name)
        return True
    except Exception as e:
        print("FAILED TEST:", test_name)
        print("Error:", e)
        return False


def choose_accounts(w3, admin):
    accounts = w3.eth.accounts
    normal_accounts = [
        account for account in accounts
        if account.lower() != admin.lower()
    ]

    if len(normal_accounts) < 3:
        raise RuntimeError("Ganache must have at least 4 accounts.")

    attacker = normal_accounts[0]
    student = normal_accounts[1]
    new_admin = normal_accounts[2]

    return attacker, student, new_admin


def main():
    w3, ganache_url, report, coin, report_address, coin_address, admin, data = get_contracts()

    attacker, student, new_admin = choose_accounts(w3, admin)

    print("=" * 70)
    print("SECURITY TEST")
    print("=" * 70)
    print("Connected to Ganache:", ganache_url)
    print("Admin:", admin)
    print("Attacker/User:", attacker)
    print("Test Student:", student)
    print("New Admin Test Address:", new_admin)
    print("ReportCard:", report_address)
    print("GradeCoin:", coin_address)
    print("-" * 70)

    results = {}

    if has_function(report, "setGrade"):
        results["user_cannot_set_grade"] = expect_revert(
            "user cannot call ReportCard setGrade",
            lambda: wait_tx(
                w3,
                report.functions.setGrade(student, 100).transact({"from": attacker}),
                "Unauthorized setGrade"
            )
        )

    if has_function(report, "pause"):
        results["user_cannot_pause"] = expect_revert(
            "user cannot pause ReportCard",
            lambda: wait_tx(
                w3,
                report.functions.pause().transact({"from": attacker}),
                "Unauthorized pause"
            )
        )

    if has_function(report, "resume"):
        results["user_cannot_resume"] = expect_revert(
            "user cannot resume ReportCard",
            lambda: wait_tx(
                w3,
                report.functions.resume().transact({"from": attacker}),
                "Unauthorized resume"
            )
        )

    if has_function(report, "transferOwnership"):
        results["user_cannot_transfer_reportcard_ownership"] = expect_revert(
            "user cannot transfer ReportCard ownership",
            lambda: wait_tx(
                w3,
                report.functions.transferOwnership(new_admin).transact({"from": attacker}),
                "Unauthorized ReportCard ownership transfer"
            )
        )

    if has_function(coin, "mint"):
        results["user_cannot_mint_gradecoin"] = expect_revert(
            "user cannot mint GradeCoin",
            lambda: wait_tx(
                w3,
                coin.functions.mint(student, 1).transact({"from": attacker}),
                "Unauthorized mint"
            )
        )

    if has_function(coin, "transferOwnership"):
        results["user_cannot_transfer_gradecoin_ownership"] = expect_revert(
            "user cannot transfer GradeCoin ownership",
            lambda: wait_tx(
                w3,
                coin.functions.transferOwnership(new_admin).transact({"from": attacker}),
                "Unauthorized GradeCoin ownership transfer"
            )
        )

    if has_function(report, "registerUser"):
        def register_user_test():
            if has_function(report, "isUserRegistered"):
                already_registered = report.functions.isUserRegistered(attacker).call()
                if already_registered:
                    return

            tx = report.functions.registerUser("Security Test User").transact({
                "from": attacker
            })

            wait_tx(w3, tx, "Register user")

        results["normal_user_can_register_profile"] = expect_success(
            "normal user can register profile",
            register_user_test
        )

    passed = sum(1 for value in results.values() if value is True)
    failed = sum(1 for value in results.values() if value is False)

    print("-" * 70)
    print("Security Test Summary")
    print("Passed:", passed)
    print("Failed:", failed)

    output = {
        "ganache_url": ganache_url,
        "admin": admin,
        "attacker": attacker,
        "student": student,
        "new_admin_test_address": new_admin,
        "report_card": report_address,
        "grade_coin": coin_address,
        "results": results,
        "summary": {
            "passed": passed,
            "failed": failed
        }
    }

    output_file = OUTPUTS_DIR / "security_test_result.json"
    save_json(output_file, output)

    print("Security test result saved to:", output_file)

    if failed == 0:
        print("Security Test finished successfully")
    else:
        print("Security Test finished with failed checks")

    print("=" * 70)


if __name__ == "__main__":
    main()