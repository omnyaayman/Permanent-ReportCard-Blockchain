import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import time

from utils import get_contracts


def main():
    w3, ganache_url, report, coin, report_address, coin_address, admin, data = get_contracts()

    print("=" * 60)
    print("LIVE ALERT SCRIPT")
    print("=" * 60)
    print("Connected to Ganache:", ganache_url)
    print("ReportCard Contract:", report_address)
    print("Starting from block:", w3.eth.block_number)
    print("Listening for grade updates...")
    print("=" * 60)

    event_filter = report.events.GradeUpdated.create_filter(
        from_block="latest"
    )

    while True:
        try:
            events = event_filter.get_new_entries()

            for event in events:
                args = event["args"]

                print("\n" + "=" * 60)
                print("LIVE ALERT: Grade Updated")
                print("=" * 60)
                print("Block:", event["blockNumber"])
                print("Transaction:", event["transactionHash"].hex())
                print("Student:", args.get("student"))
                print("New Grade:", args.get("grade"))
                print("=" * 60)

            time.sleep(2)

        except KeyboardInterrupt:
            print("\nLive alert stopped.")
            break

        except Exception as e:
            print("Error:", e)
            time.sleep(2)


if __name__ == "__main__":
    main()