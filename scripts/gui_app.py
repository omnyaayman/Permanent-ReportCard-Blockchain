from pathlib import Path
import json
import sys

# Ensure the scripts/ directory is importable regardless of how the app is
# launched (python scripts/gui_app.py, python -m, or Streamlit AppTest).
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from web3 import Web3

from config import ADMIN_PASSWORD, EXPLORER_URL
from styles import (
    inject_css,
    hero,
    section,
    metric_card,
    short_hash,
    chain_badges,
)
from utils import (
    get_contracts,
    get_grade,
    get_coin_balance,
    get_eth_balance,
    wait_tx,
    save_json,
    has_function,
    get_user_activity,
    explorer_tx_url,
    OUTPUTS_DIR,
)
from web3.exceptions import (
    TransactionNotFound,
    ContractLogicError,
)


GUI_STUDENTS_FILE = OUTPUTS_DIR / "gui_students.json"
HIDDEN_STUDENTS_FILE = OUTPUTS_DIR / "hidden_students.json"

GRADE_EVENT_LABELS = {
    "GradeAdded": "Grade Added",
    "GradeUpdated": "Grade Updated",
    "registerUser": "Student Registered",
    "setGrade": "Grade Set",
    "transferOwnership": "Ownership Transferred",
    "pause": "Contract Paused",
    "resume": "Contract Resumed",
    "mint": "Token Minted",
    "transfer": "Token Transfer",
}


# ==============================
# File Helpers
# ==============================

def load_address_list(file_path):
    file_path = Path(file_path)

    if not file_path.exists():
        return []

    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_student_to_dashboard(address):
    address = Web3.to_checksum_address(address)

    students = load_address_list(GUI_STUDENTS_FILE)

    if address.lower() not in [student.lower() for student in students]:
        students.append(address)
        save_json(GUI_STUDENTS_FILE, students)


def hide_student_from_dashboard(address):
    address = Web3.to_checksum_address(address)

    hidden_students = load_address_list(HIDDEN_STUDENTS_FILE)

    if address.lower() not in [student.lower() for student in hidden_students]:
        hidden_students.append(address)
        save_json(HIDDEN_STUDENTS_FILE, hidden_students)


def unhide_student(address):
    address = Web3.to_checksum_address(address)

    hidden_students = load_address_list(HIDDEN_STUDENTS_FILE)

    hidden_students = [
        student for student in hidden_students
        if student.lower() != address.lower()
    ]

    save_json(HIDDEN_STUDENTS_FILE, hidden_students)


def rerun_app():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


# ==============================
# Blockchain Helpers
# ==============================

def load_app():
    return get_contracts()


def address_in_ganache(w3, address):
    address = Web3.to_checksum_address(address)

    ganache_accounts = [
        Web3.to_checksum_address(account)
        for account in w3.eth.accounts
    ]

    return address in ganache_accounts


def get_coin_balance_from_raw(w3, amount_raw):
    amount = w3.from_wei(amount_raw, "ether")

    if amount == int(amount):
        return str(int(amount))

    return str(amount)


def get_dashboard_students(fake_students):
    addresses = []

    for student in fake_students:
        address = Web3.to_checksum_address(student["address"])
        addresses.append(address)

    gui_students = load_address_list(GUI_STUDENTS_FILE)

    for student in gui_students:
        address = Web3.to_checksum_address(student)

        if address.lower() not in [item.lower() for item in addresses]:
            addresses.append(address)

    hidden_students = load_address_list(HIDDEN_STUDENTS_FILE)
    hidden_lower = [student.lower() for student in hidden_students]

    addresses = [
        address for address in addresses
        if address.lower() not in hidden_lower
    ]

    return addresses


def check_admin_login(admin_address_input, password):
    """Validate the demo admin login against config and the on-chain admin."""
    if not ADMIN_PASSWORD:
        st.error(
            "Admin password is not configured. Set ADMIN_PASSWORD in your "
            ".env file, then restart the app."
        )
        st.stop()

    if admin_address_input == "" or password == "":
        st.warning("Enter admin address and password.")
        st.stop()

    try:
        entered_admin = Web3.to_checksum_address(admin_address_input)

        report_admin = Web3.to_checksum_address(
            report.functions.getAdmin().call()
        )

        coin_admin = Web3.to_checksum_address(
            coin.functions.getAdmin().call()
        )

    except Exception:
        st.error("Invalid admin address format.")
        st.stop()

    if password != ADMIN_PASSWORD:
        st.error("Wrong admin password.")
        st.stop()

    if entered_admin.lower() != report_admin.lower():
        st.error("This address is not the ReportCard admin.")
        st.stop()

    if entered_admin.lower() != coin_admin.lower():
        st.error("This address is not the GradeCoin admin.")
        st.stop()

    return entered_admin


def tx_receipt(tx_hash):
    """Return the receipt for a tx, or None if not yet mined/found."""
    try:
        return w3.eth.get_transaction_receipt(tx_hash)
    except (TransactionNotFound, Exception):
        return None


def tx_status(tx_hash):
    """Return (block, status_label) for a transaction, or (None, None)."""
    receipt = tx_receipt(tx_hash)

    if receipt is None:
        return None, None

    return receipt["blockNumber"], "Confirmed" if receipt["status"] == 1 else "Failed"


def show_tx_meta(tx_hash):
    """Render transaction confirmation details in a clean card.

    Shows the status pill, block number and the full hash (shortened, with the
    full value available on demand).
    """
    block, status = tx_status(tx_hash)

    if status:
        if status == "Confirmed":
            st.markdown(
                '<span class="prc-pill success">&#10003; Transaction Confirmed</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span class="prc-pill danger">&#10007; Transaction Failed</span>',
                unsafe_allow_html=True,
            )

        with st.container(border=True):
            cols = st.columns(3)
            cols[0].write(f"**Status:** {status}")
            cols[1].write(f"**Block:** {block}")
            cols[2].write(f"**Event Type:** Grade / Record")
    else:
        st.markdown(
            '<span class="prc-pill neutral">&#9889; Transaction submitted</span>',
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            st.write("Waiting for the transaction to be confirmed on-chain...")

    with st.expander("Transaction Hash"):
        st.write("Full transaction hash:")
        st.code(tx_hash)

    url = explorer_tx_url(tx_hash)

    if url and status:
        st.markdown(f"[View Transaction on explorer]({url})")


def friendly_tx_error(exc):
    """Map a raw transaction exception to a concise, user-facing message.

    Common contract revert reasons are surfaced clearly; unknown failures get
    a generic message instead of leaking a technical traceback.
    """
    if isinstance(exc, ContractLogicError):
        text = str(exc).lower()
    else:
        text = str(exc).lower()

    if "only admin" in text:
        return "Only the admin can perform this action."
    if "paused" in text:
        return "The contract is paused. Resume it before writing."
    if "grade not found" in text:
        return "Grade not found for this address."
    if "invalid student address" in text:
        return "Invalid student address."
    if "user already registered" in text:
        return "This user is already registered."
    if "insufficient funds" in text or "not enough balance" in text:
        return "Insufficient funds or balance for this transaction."
    if "connection" in text or "request" in text:
        return "Blockchain connection unavailable. Check that Ganache is running."

    return "Transaction failed. Please try again."


def render_students_table(rows):
    """Render the students table with shortened hashes and a clean layout."""
    if not rows:
        st.info("No academic records found yet.")
        return

    display = [
        {
            "Student": short_hash(row["Student Address"], 10, 4),
            "Grade": row["Grade"],
            "GradeCoin (GRC)": row["GradeCoin Balance"],
            "Full Address": row["Student Address"],
        }
        for row in rows
    ]

    st.dataframe(display, width="stretch", hide_index=True)

    with st.expander("Show full student addresses"):
        for row in rows:
            st.code(row["Student Address"])


def render_activity_table(activities):
    """Format raw activity entries into a readable table with a status column."""
    if not activities:
        st.info("No blockchain activity yet.")
        return

    display = []

    for act in activities:
        action = act.get("Action", act.get("action", ""))
        value = act.get("Value", act.get("value", ""))
        block = act.get("Block", act.get("block", ""))
        tx = act.get("Tx", act.get("tx", ""))

        # Friendlier action labels where they exist.
        for key, label in GRADE_EVENT_LABELS.items():
            if key.lower() in action.lower():
                action = label
                break

        display.append({
            "Block": block,
            "Action": action,
            "Details": value,
            "Status": "Confirmed",
            "Transaction": short_hash(tx, 12, 4) if tx else "",
        })

    st.dataframe(display, width="stretch", hide_index=True)

    if any(a.get("Tx") or a.get("tx") for a in activities):
        with st.expander("Show full transaction hashes"):
            for act in activities:
                tx = act.get("Tx", act.get("tx"))
                if tx:
                    st.code(tx)


# ==============================
# Load Contracts
# ==============================

st.set_page_config(
    page_title="Permanent Report Card",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

w3, ganache_url, report, coin, report_address, coin_address, saved_admin, data = load_app()


# ==============================
# Main UI
# ==============================

hero(
    "Permanent Report Card",
    "Blockchain-Based Academic Records",
    "Secure academic record management with transparent, traceable blockchain "
    "transactions. Records are stored on the Ethereum smart contract and are "
    "verified on-chain — not fabricated.",
)

with st.sidebar:
    st.markdown("### Navigation")

    page = st.radio(
        "Section",
        [
            "Dashboard",
            "Student Portal",
            "Admin Actions",
            "System Info",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown("**Network**")
    st.caption(ganache_url)
    st.caption(f"Chain ID: {w3.eth.chain_id}  •  Block: {w3.eth.block_number}")

    if st.button("Refresh Page", width="stretch"):
        rerun_app()

    st.caption(
        "Local demo on Ganache. No real funds or wallets are used."
    )


# ==============================
# Dashboard
# ==============================

if page == "Dashboard":
    section(
        "Admin Dashboard",
        "Authenticated view of the on-chain academic records. All figures come "
        "from live blockchain data.",
    )

    with st.expander("Admin Login", expanded=True):
        dashboard_admin_address = st.text_input(
            "Admin Address",
            key="dashboard_admin_address",
        )

        dashboard_password = st.text_input(
            "Admin Password",
            type="password",
            key="dashboard_admin_password",
        )

        entered_admin = check_admin_login(
            dashboard_admin_address,
            dashboard_password,
        )

    st.success(f"Admin access granted for {short_hash(entered_admin)}")

    # --- Real statistics computed from blockchain / project data ---
    students = get_dashboard_students(
        data.get("fake_students_for_testing", [])
    )

    rows = []

    for address in students:
        try:
            rows.append({
                "Student Address": address,
                "Grade": get_grade(report, address),
                "GradeCoin Balance": get_coin_balance(w3, coin, address),
            })
        except Exception:
            pass

    total_minted = coin.functions.totalMinted().call()
    total_contract_txs = 0

    latest_block = w3.eth.block_number

    # Count real contract transactions (both contracts) for accuracy.
    for block_number in range(latest_block + 1):
        try:
            block = w3.eth.get_block(block_number, full_transactions=True)
        except Exception:
            continue

        for tx in block.transactions:
            tx_to = tx.get("to")

            if tx_to and tx_to.lower() in (
                report_address.lower(),
                coin_address.lower(),
            ):
                total_contract_txs += 1

    st.subheader("Overview", divider="gray")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_card("Total Students", len(rows), "Addresses with a grade on-chain")
    with col2:
        metric_card("Total Records", len(rows), "Grades stored in the contract")
    with col3:
        metric_card("Blockchain Transactions", total_contract_txs, "Contract interactions mined")
    with col4:
        metric_card("Minted GRC", get_coin_balance_from_raw(w3, total_minted), "GradeCoins distributed")

    st.divider()

    section(
        "Student Management",
        "Academic records stored on the blockchain.",
    )
    render_students_table(rows)


# ==============================
# Student Portal
# ==============================

elif page == "Student Portal":
    section(
        "Student Portal",
        "Look up your own on-chain academic record. This view has no admin controls.",
    )

    if not ADMIN_PASSWORD:
        st.info(
            "Admin password not configured. The student portal works for "
            "viewing records; set ADMIN_PASSWORD in your .env to enable admin actions."
        )

    user_address_input = st.text_input(
        "Enter Student Address",
        placeholder="0x...",
    )

    if user_address_input:
        try:
            user_address = Web3.to_checksum_address(user_address_input)

            report_admin = Web3.to_checksum_address(
                report.functions.getAdmin().call()
            )

            coin_admin = Web3.to_checksum_address(
                coin.functions.getAdmin().call()
            )

            if (
                user_address.lower() == report_admin.lower()
                or user_address.lower() == coin_admin.lower()
            ):
                st.warning(
                    "This is the admin address. Please use the Dashboard or "
                    "Admin Actions instead."
                )
                st.stop()

            tab1, tab2, tab3, tab4 = st.tabs([
                "My Record",
                "My Grade",
                "My Balances",
                "My Activity History",
            ])

            # ------------------------------
            # Register / Profile
            # ------------------------------

            with tab1:
                st.markdown("#### Profile")

                if not has_function(report, "registerUser"):
                    st.warning("User registration is not supported by the current contract.")
                else:
                    is_registered = False

                    if has_function(report, "isUserRegistered"):
                        try:
                            is_registered = report.functions.isUserRegistered(user_address).call()
                        except Exception:
                            is_registered = False

                    if is_registered:
                        saved_name = report.functions.getUserName(user_address).call()

                        st.success("Profile found on-chain.")
                        with st.container(border=True):
                            st.write("**Name:** ", saved_name)
                            st.write("**Address:**")
                            st.code(user_address)
                    else:
                        st.info("You are not registered yet. Register below to attach a name to your address.")

                        name = st.text_input("Enter your name", key="register_name")

                        if st.button("Register User", type="primary"):
                            try:
                                if not address_in_ganache(w3, user_address):
                                    st.error("This address is not found in the current Ganache accounts.")
                                    st.stop()

                                if name.strip() == "":
                                    st.error("Name cannot be empty.")
                                    st.stop()

                                with st.spinner("Submitting registration transaction..."):
                                    tx = report.functions.registerUser(name.strip()).transact({
                                        "from": user_address,
                                    })
                                    wait_tx(w3, tx, "Register user")

                                st.success("User registered successfully.")
                                with st.container(border=True):
                                    st.write("**Address:**", user_address)
                                    st.write("**Name:**", name.strip())
                                show_tx_meta(tx.hex())

                            except Exception:
                                st.error(
                                    "Registration failed. Confirm the address "
                                    "can sign transactions and is not already "
                                    "registered."
                                )

            # ------------------------------
            # My Grade
            # ------------------------------

            with tab2:
                st.markdown("#### My Grade")

                if st.button("View My Grade", type="primary"):
                    try:
                        grade = get_grade(report, user_address)

                        st.success("Current on-chain grade")
                        with st.container(border=True):
                            st.metric("Grade", grade)
                    except Exception:
                        st.warning("No grade is recorded on-chain for this address yet.")

            # ------------------------------
            # My Balances
            # ------------------------------

            with tab3:
                st.markdown("#### My Balances")

                if st.button("Check My Balances", type="primary"):
                    try:
                        eth_balance = get_eth_balance(w3, user_address)
                        grc_balance = get_coin_balance(w3, coin, user_address)

                        col1, col2 = st.columns(2)
                        with col1:
                            metric_card("ETH Balance", f"{eth_balance} ETH")
                        with col2:
                            metric_card("GradeCoin Balance", f"{grc_balance} GRC")
                    except Exception:
                        st.error("Unable to read balances at this time. Check the blockchain connection.")

            # ------------------------------
            # My Activity History
            # ------------------------------

            with tab4:
                st.markdown("#### My Activity History")

                if st.button("Load My Activity History", type="primary"):
                    try:
                        with st.spinner("Scanning the blockchain for this address..."):
                            activities = get_user_activity(
                                w3,
                                report,
                                coin,
                                report_address,
                                coin_address,
                                user_address,
                            )

                        render_activity_table(activities)
                    except Exception:
                        st.error("Unable to load activity history at this time. Check the blockchain connection.")

        except Exception:
            st.error("Invalid address format. Enter a valid Ethereum address.")


# ==============================
# Admin Actions
# ==============================

elif page == "Admin Actions":
    section(
        "Admin Actions",
        "Write operations are enforced by the smart contract's onlyOwner "
        "modifier. Only the configured admin can submit them.",
    )

    admin_address_input = st.text_input(
        "Admin Address",
        key="actions_admin_address",
    )

    password = st.text_input(
        "Admin Password",
        type="password",
        key="actions_admin_password",
    )

    entered_admin = check_admin_login(
        admin_address_input,
        password,
    )

    st.success(f"Admin access granted for {short_hash(entered_admin)}")

    contract_status = "Paused" if report.functions.paused().call() else "Active"

    if contract_status == "Paused":
        st.warning("The contract is currently paused. Write operations are blocked.")
    else:
        st.caption(f"Contract status: Active")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Add / Update Student",
        "Mint GradeCoin",
        "Pause / Resume",
        "Hide Student",
        "Transfer Ownership",
    ])

    # ------------------------------
    # Add / Update Student
    # ------------------------------

    with tab1:
        st.markdown("#### Add / Update Student Record")
        st.write(
            "Set a grade for a student. This writes the record to the "
            "blockchain and returns a transaction hash."
        )

        student_address = st.text_input("Student Address", key="student_address")
        grade = st.number_input("Grade (0-100)", min_value=0, max_value=100, step=1)

        if st.button("Add / Update Grade", type="primary"):
            try:
                student_address = Web3.to_checksum_address(student_address)

                with st.spinner("Submitting grade transaction..."):
                    tx = report.functions.setGrade(
                        student_address,
                        int(grade),
                    ).transact({"from": entered_admin})

                    wait_tx(w3, tx, "Set grade")

                save_student_to_dashboard(student_address)
                unhide_student(student_address)

                st.success("Grade recorded on the blockchain.")

                with st.container(border=True):
                    st.write("**Student:**", short_hash(student_address))
                    st.write("**Grade:**", grade)

                show_tx_meta(tx.hex())

            except Exception as e:
                st.error(friendly_tx_error(e))

    # ------------------------------
    # Mint GradeCoin
    # ------------------------------

    with tab2:
        st.markdown("#### Mint GradeCoin")
        st.write("Mint GRC tokens to a student as a reward.")

        receiver = st.text_input("Receiver Address", key="receiver_address")
        amount = st.number_input("Amount in GRC", min_value=1, step=1)

        if st.button("Mint GradeCoin", type="primary"):
            try:
                receiver = Web3.to_checksum_address(receiver)

                with st.spinner("Submitting mint transaction..."):
                    tx = coin.functions.mint(receiver, int(amount)).transact({
                        "from": entered_admin,
                    })
                    wait_tx(w3, tx, "Mint GradeCoin")

                st.success("GradeCoins minted successfully.")
                with st.container(border=True):
                    st.write("**Receiver:**", short_hash(receiver))
                    st.write("**Amount:**", f"{int(amount)} GRC")

                show_tx_meta(tx.hex())

            except Exception as e:
                st.error(friendly_tx_error(e))

    # ------------------------------
    # Pause / Resume
    # ------------------------------

    with tab3:
        st.markdown("#### Pause / Resume Contract")
        st.write(
            "Pausing blocks grade write operations. Use it to halt updates "
            "administratively; records remain readable and immutable."
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Pause Contract", type="secondary"):
                try:
                    with st.spinner("Submitting pause transaction..."):
                        tx = report.functions.pause().transact({"from": entered_admin})
                        wait_tx(w3, tx, "Pause contract")
                    st.success("Contract paused successfully.")
                    show_tx_meta(tx.hex())
                except Exception as e:
                    st.error(friendly_tx_error(e))

        with col2:
            if st.button("Resume Contract", type="secondary"):
                try:
                    with st.spinner("Submitting resume transaction..."):
                        tx = report.functions.resume().transact({"from": entered_admin})
                        wait_tx(w3, tx, "Resume contract")
                    st.success("Contract resumed successfully.")
                    show_tx_meta(tx.hex())
                except Exception as e:
                    st.error(friendly_tx_error(e))

    # ------------------------------
    # Hide Student
    # ------------------------------

    with tab4:
        st.markdown("#### Hide Student (Dashboard Only)")
        st.write(
            "Remove a student from the Dashboard list. This is a display-only "
            "action and does NOT delete any blockchain data."
        )

        hide_address = st.text_input("Student Address to Hide", key="hide_address")

        if st.button("Hide Student", type="secondary"):
            try:
                hide_address = Web3.to_checksum_address(hide_address)
                hide_student_from_dashboard(hide_address)
                st.success("Student hidden from Dashboard.")
                st.info("Blockchain data remains permanently stored and verifiable.")
            except Exception:
                st.error("Invalid address format. Enter a valid Ethereum address.")

    # ------------------------------
    # Transfer Ownership
    # ------------------------------

    with tab5:
        st.markdown("#### Transfer Ownership")
        st.write(
            "Transfer admin rights for the ReportCard contract to another "
            "address. The current admin stops being able to write."
        )

        new_admin = st.text_input("New Admin Address", key="new_admin_address")

        if st.button("Transfer Ownership", type="primary"):
            try:
                new_admin = Web3.to_checksum_address(new_admin)

                with st.spinner("Submitting ownership transfer..."):
                    tx = report.functions.transferOwnership(new_admin).transact({
                        "from": entered_admin,
                    })
                    wait_tx(w3, tx, "Transfer ownership")

                st.success("Ownership transferred successfully.")
                show_tx_meta(tx.hex())
                st.warning(
                    "The new admin must be the same address for both contracts. "
                    "You may also need to transfer GradeCoin ownership."
                )
            except Exception as e:
                st.error(friendly_tx_error(e))


# ==============================
# System Info
# ==============================

elif page == "System Info":
    section(
        "System Information",
        "Verified metadata of the deployed smart contracts and network.",
    )

    st.subheader("Deployed Contracts", divider="gray")

    section("ReportCard Contract")
    st.code(report_address)

    section("GradeCoin Contract")
    st.code(coin_address)

    st.subheader("Administrators", divider="gray")

    section("ReportCard Admin")
    st.code(report.functions.getAdmin().call())

    section("GradeCoin Admin")
    st.code(coin.functions.getAdmin().call())

    st.subheader("Network", divider="gray")

    chain_badges([
        ("RPC", ganache_url),
        ("Chain ID", str(w3.eth.chain_id)),
        ("Latest Block", str(w3.eth.block_number)),
    ])

    if EXPLORER_URL:
        section("Block Explorer")
        st.code(EXPLORER_URL)

    st.divider()
    st.caption(
        "Record integrity is enforced by the smart contract. Transactions and "
        "events are traceable on-chain; nothing here is fabricated."
    )
