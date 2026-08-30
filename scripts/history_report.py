import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils import (
    get_contracts,
    get_fake_students,
    get_grade,
    save_json,
    OUTPUTS_DIR
)


def main():
    w3, ganache_url, report, coin, report_address, coin_address, admin, data = get_contracts()

    students = get_fake_students(data)
    grades = []
    rows = []

    print("=" * 60)
    print("CLASS GRADES HISTORY REPORT")
    print("=" * 60)
    print("Connected to Ganache:", ganache_url)
    print("ReportCard Contract:", report_address)
    print("-" * 60)

    for index, student in enumerate(students, start=1):
        address = student["address"]
        grade = get_grade(report, address)

        grades.append(grade)

        rows.append({
            "student_number": index,
            "address": address,
            "grade": grade
        })

        print(f"Student {index}")
        print("Address :", address)
        print("Grade   :", grade)
        print("-" * 40)

    if grades:
        average = sum(grades) / len(grades)
        highest = max(grades)
        lowest = min(grades)
    else:
        average = 0
        highest = 0
        lowest = 0

    print("\n===== CLASS STATISTICS =====")
    print("Total Students       :", len(grades))
    print(f"Class Average Grade  : {average:.2f}")
    print("Highest Grade        :", highest)
    print("Lowest Grade         :", lowest)

    result = {
        "ganache_url": ganache_url,
        "report_card_contract": report_address,
        "total_students": len(grades),
        "class_average": average,
        "highest_grade": highest,
        "lowest_grade": lowest,
        "students": rows
    }

    output_file = OUTPUTS_DIR / "class_grades_history_report.json"
    save_json(output_file, result)

    print("-" * 60)
    print("Report saved to:", output_file)
    print("=" * 60)


if __name__ == "__main__":
    main()