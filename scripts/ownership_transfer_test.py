import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils import get_contracts, wait_tx, save_json, OUTPUTS_DIR, has_function, get_grade


def expect_revert(test_name, action):
    try:
        action()
        print("FAILED TEST:", test_name)
        return False
    except Exception:
        print("PASSED TEST:", test_name)
        return True


def choose_new_admin(w3, old_admin):
    for account in w3.eth.accounts:
        if account.lower() != old_admin.lower():
            return account

    raise RuntimeError("No available new admin account found.")


def test_reportcard_ownership(w3, report, old_admin, new_admin, test_student):
    print("=" * 70)
    print("OWNERSHIP TRANSFER TEST - ReportCard")
    print("=" * 70)
    print("Old admin:", old_admin)
    print("New admin:", new_admin)
    print("Test student:", test_student)
    print("-" * 70)

    if not has_function(report, "transferOwnership"):
        print("SKIPPED: ReportCard transferOwnership not found")
        return {
            "skipped": True,
            "reason": "ReportCard transferOwnership not found"
        }

    try:
        if has_function(report, "resume"):
            tx = report.functions.resume().transact({"from": old_admin})
            wait_tx(w3, tx, "Resume ReportCard")
    except Exception:
        pass

    original_grade = get_grade(report, test_student)

    tx = report.functions.setGrade(test_student, original_grade).transact({
        "from": old_admin
    })
    wait_tx(w3, tx, "Old admin setGrade before transfer")
    print("PASSED TEST: old admin can set grade before transfer")

    tx = report.functions.transferOwnership(new_admin).transact({
        "from": old_admin
    })
    wait_tx(w3, tx, "Transfer ReportCard ownership")
    print("ReportCard ownership transferred successfully")

    current_admin = report.functions.getAdmin().call()
    print("Current ReportCard admin:", current_admin)
    print("-" * 70)

    old_admin_blocked = expect_revert(
        "old admin cannot set grade after ReportCard ownership transfer",
        lambda: wait_tx(
            w3,
            report.functions.setGrade(test_student, original_grade).transact({"from": old_admin}),
            "Old admin setGrade after transfer"
        )
    )

    tx = report.functions.setGrade(test_student, original_grade).transact({
        "from": new_admin
    })
    wait_tx(w3, tx, "New admin setGrade after transfer")
    print("PASSED TEST: new admin can set grade after transfer")

    tx = report.functions.transferOwnership(old_admin).transact({
        "from": new_admin
    })
    wait_tx(w3, tx, "Restore ReportCard ownership")

    restored_admin = report.functions.getAdmin().call()
    final_grade = get_grade(report, test_student)

    print("-" * 70)
    print("ReportCard ownership restored back to old admin")
    print("Restored ReportCard admin:", restored_admin)
    print("Final student grade:", final_grade)

    return {
        "skipped": False,
        "old_admin": old_admin,
        "new_admin": new_admin,
        "admin_after_transfer": current_admin,
        "admin_after_restore": restored_admin,
        "old_admin_blocked_after_transfer": old_admin_blocked,
        "new_admin_can_set_grade_after_transfer": True,
        "ownership_restored": restored_admin.lower() == old_admin.lower(),
        "test_student": test_student,
        "final_grade": final_grade
    }


def test_gradecoin_ownership(w3, coin, old_admin, new_admin, test_student):
    print("=" * 70)
    print("OWNERSHIP TRANSFER TEST - GradeCoin")
    print("=" * 70)
    print("Old admin:", old_admin)
    print("New admin:", new_admin)
    print("Test student:", test_student)
    print("-" * 70)

    if not has_function(coin, "transferOwnership"):
        print("SKIPPED: GradeCoin transferOwnership not found")
        return {
            "skipped": True,
            "reason": "GradeCoin transferOwnership not found"
        }

    amount = 1

    tx = coin.functions.mint(test_student, amount).transact({
        "from": old_admin
    })
    wait_tx(w3, tx, "Old admin mint before transfer")
    print("PASSED TEST: old admin can mint before transfer")

    tx = coin.functions.transferOwnership(new_admin).transact({
        "from": old_admin
    })
    wait_tx(w3, tx, "Transfer GradeCoin ownership")
    print("GradeCoin ownership transferred successfully")

    current_admin = coin.functions.getAdmin().call()
    print("Current GradeCoin admin:", current_admin)
    print("-" * 70)

    old_admin_blocked = expect_revert(
        "old admin cannot mint after GradeCoin ownership transfer",
        lambda: wait_tx(
            w3,
            coin.functions.mint(test_student, amount).transact({"from": old_admin}),
            "Old admin mint after transfer"
        )
    )

    tx = coin.functions.mint(test_student, amount).transact({
        "from": new_admin
    })
    wait_tx(w3, tx, "New admin mint after transfer")
    print("PASSED TEST: new admin can mint after transfer")

    balance = coin.functions.balanceOf(test_student).call()
    total_minted = coin.functions.totalMinted().call()

    print("-" * 70)
    print("Test student balance:", w3.from_wei(balance, "ether"), "GRC")
    print("Total minted:", w3.from_wei(total_minted, "ether"), "GRC")

    tx = coin.functions.transferOwnership(old_admin).transact({
        "from": new_admin
    })
    wait_tx(w3, tx, "Restore GradeCoin ownership")

    restored_admin = coin.functions.getAdmin().call()

    print("-" * 70)
    print("GradeCoin ownership restored back to old admin")
    print("Restored GradeCoin admin:", restored_admin)

    return {
        "skipped": False,
        "old_admin": old_admin,
        "new_admin": new_admin,
        "admin_after_transfer": current_admin,
        "admin_after_restore": restored_admin,
        "old_admin_blocked_after_transfer": old_admin_blocked,
        "new_admin_can_mint_after_transfer": True,
        "ownership_restored": restored_admin.lower() == old_admin.lower(),
        "test_student": test_student,
        "test_student_balance_grc": str(w3.from_wei(balance, "ether")),
        "total_minted_grc": str(w3.from_wei(total_minted, "ether"))
    }


def main():
    w3, ganache_url, report, coin, report_address, coin_address, admin, data = get_contracts()

    test_student = data["fake_students_for_testing"][0]["address"]

    report_old_admin = report.functions.getAdmin().call()
    coin_old_admin = coin.functions.getAdmin().call()

    report_new_admin = choose_new_admin(w3, report_old_admin)
    coin_new_admin = choose_new_admin(w3, coin_old_admin)

    print("=" * 70)
    print("OWNERSHIP TRANSFER FULL TEST")
    print("=" * 70)
    print("Connected to Ganache:", ganache_url)
    print("ReportCard Contract:", report_address)
    print("GradeCoin Contract:", coin_address)
    print("Test student:", test_student)
    print("=" * 70)

    report_result = test_reportcard_ownership(
        w3=w3,
        report=report,
        old_admin=report_old_admin,
        new_admin=report_new_admin,
        test_student=test_student
    )

    coin_result = test_gradecoin_ownership(
        w3=w3,
        coin=coin,
        old_admin=coin_old_admin,
        new_admin=coin_new_admin,
        test_student=test_student
    )

    result = {
        "ganache_url": ganache_url,
        "contracts": {
            "report_card": report_address,
            "grade_coin": coin_address
        },
        "test_student": test_student,
        "report_card_ownership_test": report_result,
        "grade_coin_ownership_test": coin_result
    }

    output_file = OUTPUTS_DIR / "ownership_transfer_result.json"
    save_json(output_file, result)

    print("-" * 70)
    print("Ownership transfer result saved to:", output_file)
    print("Ownership Transfer Full Test finished successfully")
    print("=" * 70)


if __name__ == "__main__":
    main()